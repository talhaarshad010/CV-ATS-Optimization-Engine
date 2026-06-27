import logging
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.resume_rewriter import rewrite_bullet_points
from app.services.skill_gap_analyzer import analyze_gaps, generate_improvement_plan
from app.services.rag_pipeline import ask
from app.utils.supabase_client import (
    get_candidate,
    get_candidate_skills,
    get_job_description,
    supabase
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request Models
class GapsRequest(BaseModel):
    candidate_id: str
    job_id: str


class ChatRequest(BaseModel):
    question: str
    candidate_id: Optional[str] = None


@router.post("/rewrite/{candidate_id}")
async def rewrite_candidate_bullets(candidate_id: str, job_title: str = Query("Software Engineer")):
    """
    Fetches the candidate's experience section text from Supabase,
    splits it into bullet points, and rewrites each bullet using Llama 3.1.
    """
    try:
        candidate = get_candidate(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate from database.")

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Get experience text from raw_sections
    raw_sections = candidate.get("raw_sections") or {}
    if isinstance(raw_sections, str):
        try:
            raw_sections = json.loads(raw_sections)
        except Exception:
            raw_sections = {}
            
    experience_text = raw_sections.get("experience", {}).get("text", "").strip()
    
    if not experience_text:
        logger.warning(f"No experience section found for candidate {candidate_id}. Falling back to empty string.")
        experience_text = ""

    try:
        result = rewrite_bullet_points(experience_text, job_title)
        return result
    except Exception as e:
        logger.error(f"Error rewriting bullets for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rewrite resume bullet points.")


@router.post("/gaps")
async def get_gaps(request: GapsRequest):
    """
    Analyzes missing skills and recommends learning courses and projects.
    """
    candidate_id = request.candidate_id.strip()
    job_id = request.job_id.strip()

    if not candidate_id or not job_id:
        raise HTTPException(status_code=400, detail="Both candidate_id and job_id are required.")

    # Fetch candidate
    try:
        candidate = get_candidate(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate.")
        
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Fetch candidate skills
    try:
        skills = get_candidate_skills(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching skills for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate skills.")

    candidate_skills = [
        s.get("skill_normalized") or s.get("skill_raw") or s.get("normalized") or s.get("raw")
        for s in skills if s
    ]

    # Fetch job description
    try:
        jd_record = get_job_description(job_id)
    except Exception as e:
        logger.error(f"Error fetching job description {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve job description.")

    if not jd_record:
        raise HTTPException(status_code=404, detail="Job description not found.")

    jd_data = jd_record.get("parsed_data", {})
    job_title = jd_data.get("job_title") or jd_record.get("title") or "Software Engineer"

    # Find missing skills using on-the-fly computation
    from app.services.ats_scorer import compute_ats_score
    candidate_data = {
        "raw_text": candidate.get("raw_text", ""),
        "total_experience_years": candidate.get("total_experience_years", 0.0),
        "skills": skills,
        "raw_sections": candidate.get("raw_sections", {})
    }
    jd_data_scorer = dict(jd_data)
    jd_data_scorer["raw_text"] = jd_record.get("raw_text", "")

    try:
        base_scoring = compute_ats_score(candidate_data, jd_data_scorer)
        missing_skills = base_scoring.get("missing_skills", [])
    except Exception as e:
        logger.error(f"Error computing ATS score: {e}")
        # Direct list comparison fallback
        jd_required = jd_data.get("required_skills", [])
        missing_skills = [s for s in jd_required if s not in candidate_skills]

    try:
        result = analyze_gaps(missing_skills, candidate_skills, job_title)
        return result
    except Exception as e:
        logger.error(f"Error analyzing skill gaps for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze skill gaps.")


@router.post("/chat")
async def ask_rag(request: ChatRequest):
    """
    RAG Chatbot endpoint: queries the FAISS vector database using the question
    and generates an LLM response using local Llama 3.1.
    """
    question = request.question.strip()
    candidate_id = request.candidate_id.strip() if request.candidate_id else None

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = ask(question, candidate_id)
        return result
    except Exception as e:
        logger.error(f"Error running chat for question '{question}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve chatbot answer.")


@router.post("/report/{candidate_id}/{job_id}")
async def generate_comprehensive_report(candidate_id: str, job_id: str):
    """
    Combines: ATS score + skill gaps + rewritten bullets + action plan.
    Returns a unified report JSON payload.
    """
    # 1. Fetch Candidate
    try:
        candidate = get_candidate(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate.")
        
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # 2. Fetch Candidate Skills
    try:
        skills = get_candidate_skills(candidate_id)
    except Exception as e:
        logger.error(f"Error fetching skills for candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate skills.")

    candidate_skills = [
        s.get("skill_normalized") or s.get("skill_raw") or s.get("normalized") or s.get("raw")
        for s in skills if s
    ]

    # 3. Fetch Job Description
    try:
        jd_record = get_job_description(job_id)
    except Exception as e:
        logger.error(f"Error fetching job description {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve job description.")

    if not jd_record:
        raise HTTPException(status_code=404, detail="Job description not found.")

    jd_data = jd_record.get("parsed_data", {})
    job_title = jd_data.get("job_title") or jd_record.get("title") or "Software Engineer"

    # 4. Fetch or Compute ATS Score
    ats_score = None
    grade = None
    breakdown = None
    missing_skills = []

    # Try to fetch from database
    try:
        resp = supabase.table("ats_scores").select("*").eq("candidate_id", candidate_id).eq("job_id", job_id).order("created_at", desc=True).limit(1).execute()
        if resp.data:
            record = resp.data[0]
            ats_score = record.get("ats_score")
            grade = record.get("grade")
            breakdown = record.get("breakdown")
    except Exception as e:
        logger.warning(f"Failed to fetch score from ats_scores table: {e}")

    # Reconstruct structures for scorer/gap analysis
    candidate_data = {
        "id": candidate_id,
        "raw_text": candidate.get("raw_text", ""),
        "total_experience_years": candidate.get("total_experience_years", 0.0),
        "skills": skills,
        "raw_sections": candidate.get("raw_sections", {})
    }
    jd_data_scorer = dict(jd_data)
    jd_data_scorer["id"] = job_id
    jd_data_scorer["raw_text"] = jd_record.get("raw_text", "")

    # Always compute base scoring to retrieve missing skills lists
    from app.services.ats_scorer import compute_ats_score
    try:
        base_scoring = compute_ats_score(candidate_data, jd_data_scorer)
        missing_skills = base_scoring.get("missing_skills", [])
        if ats_score is None:
            ats_score = base_scoring.get("ats_score")
            grade = base_scoring.get("grade")
            breakdown = base_scoring.get("breakdown")
    except Exception as e:
        logger.error(f"Error calculating ATS score breakdown: {e}")
        if ats_score is None:
            ats_score = 0
            grade = "D"
            breakdown = {}
        jd_required = jd_data.get("required_skills", [])
        missing_skills = [s for s in jd_required if s not in candidate_skills]

    # 5. Skill Gaps Analysis
    try:
        gaps_result = analyze_gaps(missing_skills, candidate_skills, job_title)
    except Exception as e:
        logger.error(f"Error analyzing skill gaps for report: {e}")
        gaps_result = {"gaps": [], "total_gaps": 0, "estimated_total_weeks": 0}

    # 6. Rewritten Bullets
    raw_sections = candidate.get("raw_sections") or {}
    if isinstance(raw_sections, str):
        try:
            raw_sections = json.loads(raw_sections)
        except Exception:
            raw_sections = {}
    experience_text = raw_sections.get("experience", {}).get("text", "").strip()
    try:
        rewrite_result = rewrite_bullet_points(experience_text, job_title)
    except Exception as e:
        logger.error(f"Error rewriting bullets for report: {e}")
        rewrite_result = {"original_bullets": [], "rewritten_bullets": [], "improvement_count": 0}

    # 7. Action Plan
    try:
        action_plan = generate_improvement_plan(ats_score, breakdown, gaps_result)
    except Exception as e:
        logger.error(f"Error generating action plan for report: {e}")
        action_plan = "Failed to generate action plan."

    # Return unified payload
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "job_title": job_title,
        "ats_score": ats_score,
        "grade": grade,
        "breakdown": breakdown,
        "skill_gaps": gaps_result.get("gaps", []),
        "gaps_summary": {
            "total_gaps": gaps_result.get("total_gaps", 0),
            "estimated_total_weeks": gaps_result.get("estimated_total_weeks", 0)
        },
        "rewritten_bullets": rewrite_result,
        "action_plan": action_plan
    }
