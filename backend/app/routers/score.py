import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ats_scorer import explain_score
from app.utils.supabase_client import (
    get_candidate,
    get_candidate_skills,
    get_job_description,
    insert_score
)

router = APIRouter()
logger = logging.getLogger(__name__)


class ScoreRequest(BaseModel):
    candidate_id: str
    job_id: str


@router.post("")
async def compute_and_save_ats_score(request: ScoreRequest):
    """
    Computes and saves ATS score for a candidate against a job description:
    1. Fetches candidate metadata and skills from Supabase.
    2. Fetches job description from Supabase.
    3. Runs explain_score computation using SHAP.
    4. Saves the results to the ats_scores table in Supabase.
    5. Returns the full scoring explanation.
    """
    candidate_id = request.candidate_id.strip()
    job_id = request.job_id.strip()

    if not candidate_id or not job_id:
        raise HTTPException(
            status_code=400,
            detail="Both candidate_id and job_id are required."
        )

    # 1. Fetch Candidate Row
    try:
        candidate = get_candidate(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate from database.")

    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with ID {candidate_id} not found.")

    # 2. Fetch Candidate Skills
    try:
        skills = get_candidate_skills(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching skills for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate skills from database.")

    # Reconstruct candidate data for scorer
    candidate_data = {
        "id": candidate_id,
        "raw_text": candidate.get("raw_text", ""),
        "total_experience_years": candidate.get("total_experience_years", 0.0),
        "skills": skills,
        "raw_sections": candidate.get("raw_sections", {})
    }

    # 3. Fetch Job Description
    try:
        jd_record = get_job_description(job_id)
    except Exception as e:
        logger.error(f"Error fetching job description {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve job description from database.")

    if not jd_record:
        raise HTTPException(status_code=404, detail=f"Job description with ID {job_id} not found.")

    # Reconstruct JD data for scorer (using stored parsed_data + raw_text)
    jd_data = jd_record.get("parsed_data", {})
    jd_data["id"] = job_id
    jd_data["raw_text"] = jd_record.get("raw_text", "")

    # 4. Compute ATS score and explanation
    try:
        explanation = explain_score(candidate_data, jd_data)
    except Exception as e:
        logger.error(f"Error running ATS scorer for candidate {candidate_id} against job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute ATS score explanation.")

    # Get breakdown and base score to save in database
    ats_score = explanation.get("ats_score", 0)
    # Re-calculate or obtain grade from explanation
    grade = explanation.get("grade", "D")
    
    # We can reconstruct or parse breakdown values
    # In explain_score, we run compute_ats_score which contains raw breakdown values
    from app.services.ats_scorer import compute_ats_score
    try:
        base_scoring = compute_ats_score(candidate_data, jd_data)
        breakdown_db = base_scoring.get("breakdown", {})
    except Exception:
        breakdown_db = {}

    # 5. Save results to Supabase ats_scores table
    try:
        insert_score(
            candidate_id=candidate_id,
            job_id=job_id,
            ats_score=ats_score,
            grade=grade,
            breakdown=breakdown_db
        )
    except Exception as e:
        logger.error(f"Error saving ATS score record to Supabase: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save computed ATS score to database.")

    # 6. Return response
    # Include grade in returned response as well
    explanation["grade"] = grade
    return explanation
