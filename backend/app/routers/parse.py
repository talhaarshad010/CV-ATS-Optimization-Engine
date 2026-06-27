import logging
from fastapi import APIRouter, HTTPException
from app.services.cleaner import clean_text
from app.services.section_detector import detect_sections
from app.services.ner_orchestrator import orchestrate_cv
from app.services import skill_extractor
from app.utils.supabase_client import get_candidate, update_candidate, insert_skills

from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ensure skill_extractor module has the exact extract_skills attribute mapping
skill_extractor.extract_skills = skill_extractor.extract_skills_from_cv

router = APIRouter()
logger = logging.getLogger(__name__)


class CandidateUpdatePayload(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    total_experience_years: Optional[float] = None
    raw_sections: Optional[Dict[str, Any]] = None


@router.put("/candidates/{candidate_id}")
async def update_candidate_details(candidate_id: str, payload: CandidateUpdatePayload):
    """
    Updates the candidate's parsed details in Supabase with manually edited fields.
    """
    try:
        candidate = get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")

        update_data = {}
        if payload.name is not None:
            update_data["candidate_name"] = payload.name
        if payload.email is not None:
            update_data["email"] = payload.email
        if payload.phone is not None:
            update_data["phone"] = payload.phone
        if payload.location is not None:
            update_data["location"] = payload.location
        if payload.linkedin_url is not None:
            update_data["linkedin_url"] = payload.linkedin_url
        if payload.total_experience_years is not None:
            update_data["total_experience_years"] = payload.total_experience_years
        if payload.raw_sections is not None:
            # Merge or overwrite raw sections
            existing_sections = candidate.get("raw_sections") or {}
            for k, v in payload.raw_sections.items():
                existing_sections[k] = v
            update_data["raw_sections"] = existing_sections

        updated = update_candidate(candidate_id, update_data)
        return {"status": "success", "candidate": updated}
    except Exception as e:
        logger.error(f"Error updating candidate details for {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update candidate details.")


@router.post("/parse/{candidate_id}")
async def parse_candidate_cv(candidate_id: str):
    """
    Orchestrates Phase 2 and Phase 3 processing for a candidate's CV:
    1. Fetches candidate row from Supabase.
    2. Runs text cleaning on raw_text.
    3. Runs section detection on cleaned text.
    4. Runs NER orchestrator to extract structured fields.
    5. Runs skill extractor to extract and normalize skills.
    6. Saves skill results to extracted_skills table in Supabase.
    7. Updates the candidate row in the database, setting status to 'parsed'.
    8. Returns the structured results, including a skills summary.
    """
    # 1. Fetch candidate raw text
    try:
        candidate = get_candidate(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate from database.")

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    raw_text = candidate.get("raw_text")
    if not raw_text:
        raise HTTPException(
            status_code=400, 
            detail="No raw text found for this candidate. Upload a valid document first."
        )

    # 2. Run cleaner
    try:
        clean_result = clean_text(raw_text)
        display_text = clean_result.get("display_text", "")
    except Exception as e:
        logger.error(f"Cleaning error for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Text cleaning process failed.")

    # 3. Run section detector
    try:
        sections = detect_sections(display_text)
    except Exception as e:
        logger.error(f"Section detection error for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Section detection process failed.")

    # 4. Run NER orchestrator
    try:
        ner_result = orchestrate_cv(sections, candidate_id)
    except Exception as e:
        logger.error(f"NER orchestration error for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="NER extraction process failed.")

    # 5. Run Skill Extraction & Normalization
    try:
        skills_result = skill_extractor.extract_skills(sections)
    except Exception as e:
        logger.error(f"Skill extraction error for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Skill extraction process failed.")

    # 6. Save skill results to extracted_skills table in Supabase
    try:
        insert_skills(candidate_id, skills_result.get("skills", []))
    except Exception as e:
        logger.error(f"Error saving skills to Supabase for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save extracted skills to database.")

    # 7. Update candidates row in Supabase and update status to "parsed"
    update_data = {
        "candidate_name": ner_result.get("name"),
        "email": ner_result.get("email"),
        "phone": ner_result.get("phone"),
        "linkedin_url": ner_result.get("linkedin"),
        "location": ner_result.get("location"),
        "total_experience_years": ner_result.get("total_experience_years"),
        "raw_sections": sections,  # stores section_detector output
        "raw_entities": ner_result,  # stores NER output
        "ner_method": ner_result.get("ner_method"),
        "status": "parsed"
    }

    try:
        updated_candidate = update_candidate(candidate_id, update_data)
    except Exception as e:
        logger.error(f"Database update error for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save parsed results to database.")

    if not updated_candidate:
        raise HTTPException(status_code=500, detail="Database update returned empty result.")

    # Format the skills for the API response
    skills_list = [
        {
            "normalized": skill.get("normalized"),
            "confidence": skill.get("confidence")
        }
        for skill in skills_result.get("skills", [])
    ]

    # 8. Return response
    return {
        "candidate_id": candidate_id,
        "name": updated_candidate.get("candidate_name"),
        "email": updated_candidate.get("email"),
        "phone": updated_candidate.get("phone"),
        "location": updated_candidate.get("location"),
        "linkedin_url": updated_candidate.get("linkedin_url"),
        "total_experience_years": updated_candidate.get("total_experience_years"),
        "skills": skills_list,
        "skill_count": len(skills_list),
        "status": updated_candidate.get("status"),
        "raw_sections": sections,
        "raw_entities": ner_result
    }
