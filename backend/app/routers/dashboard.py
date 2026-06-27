import logging
from fastapi import APIRouter, HTTPException
from app.utils.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard_stats():
    """
    Retrieves aggregated dashboard statistics and a unified transaction feed:
    - Total candidates parsed
    - Total job matches run
    - Average ATS score across all calculations
    - Combined history list: Candidate details + Matched Job Title + Calculated Score
    """
    try:
        # 1. Fetch Candidates (basic meta)
        candidates_resp = supabase.table("candidates").select(
            "id", "candidate_name", "email", "total_experience_years", "status", "created_at"
        ).order("created_at", desc=True).execute()
        candidates = candidates_resp.data or []

        # 2. Fetch Job Descriptions
        jobs_resp = supabase.table("job_descriptions").select("id", "title").execute()
        jobs_map = {job["id"]: job["title"] for job in (jobs_resp.data or [])}

        # 3. Fetch ATS Scores
        scores_resp = supabase.table("ats_scores").select(
            "id", "candidate_id", "job_id", "ats_score", "grade", "created_at"
        ).order("created_at", desc=True).execute()
        scores = scores_resp.data or []

        # 4. Compute Metrics
        total_candidates = len(candidates)
        total_matches = len(scores)
        
        avg_score = 0
        if total_matches > 0:
            avg_score = round(sum(s["ats_score"] for s in scores) / total_matches, 1)

        # 5. Join records for Unified Activity Feed
        candidates_map = {
            c["id"]: {
                "name": c.get("candidate_name") or "Unnamed Candidate",
                "email": c.get("email") or "No Email",
                "experience": c.get("total_experience_years") or 0
            }
            for c in candidates
        }

        activity_feed = []
        for score in scores:
            c_info = candidates_map.get(score["candidate_id"], {"name": "Deleted Candidate", "email": "N/A", "experience": 0})
            activity_feed.append({
                "score_id": score["id"],
                "candidate_id": score["candidate_id"],
                "candidate_name": c_info["name"],
                "candidate_email": c_info["email"],
                "job_title": jobs_map.get(score["job_id"], "Unknown Position"),
                "ats_score": score["ats_score"],
                "grade": score["grade"],
                "created_at": score["created_at"]
            })

        return {
            "total_candidates": total_candidates,
            "total_matches": total_matches,
            "avg_score": avg_score,
            "candidates": candidates,
            "activity_feed": activity_feed
        }
    except Exception as e:
        logger.error(f"Error compiling dashboard statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data.")
