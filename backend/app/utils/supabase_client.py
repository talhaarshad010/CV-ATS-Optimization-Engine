import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
SUPABASE_BUCKET: str = os.environ.get("SUPABASE_BUCKET", "resumes")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_file_to_storage(file_bytes: bytes, file_path: str, content_type: str) -> str:
    """Upload file to Supabase Storage and return the storage path."""
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return file_path


def insert_candidate(data: dict) -> dict:
    """Insert a new candidate row and return the created record."""
    response = supabase.table("candidates").insert(data).execute()
    return response.data[0]


def get_candidate(candidate_id: str) -> dict:
    """Fetch a candidate row by ID."""
    response = supabase.table("candidates").select("*").eq("id", candidate_id).execute()
    if not response.data:
        return None
    return response.data[0]


def update_candidate(candidate_id: str, data: dict) -> dict:
    """Update a candidate row by ID and return the updated record."""
    response = supabase.table("candidates").update(data).eq("id", candidate_id).execute()
    if not response.data:
        return None
    return response.data[0]


def delete_candidate_skills(candidate_id: str):
    """Deletes all existing extracted skills for a given candidate ID."""
    supabase.table("extracted_skills").delete().eq("candidate_id", candidate_id).execute()


def insert_extracted_skills(skills: list) -> list:
    """Bulk-inserts a list of candidate skills into extracted_skills table."""
    if not skills:
        return []
    response = supabase.table("extracted_skills").insert(skills).execute()
    return response.data


def insert_skills(candidate_id: str, skills: list[dict]) -> list:
    """Deletes existing skills for a candidate and bulk-inserts new ones."""
    delete_candidate_skills(candidate_id)
    if not skills:
        return []
    
    # Map input raw/normalized keys to database skill_raw/skill_normalized columns
    rows = [
        {
            "candidate_id": candidate_id,
            "skill_raw": skill.get("raw"),
            "skill_normalized": skill.get("normalized"),
            "confidence": skill.get("confidence")
        }
        for skill in skills
    ]
    response = supabase.table("extracted_skills").insert(rows).execute()
    return response.data


def insert_job_description(title: str, raw_text: str, parsed_data: dict) -> dict:
    """Insert a new job description row and return the created record."""
    data = {
        "title": title,
        "raw_text": raw_text,
        "parsed_data": parsed_data
    }
    response = supabase.table("job_descriptions").insert(data).execute()
    return response.data[0]


def get_candidate_skills(candidate_id: str) -> list:
    """Fetch all extracted skills for a candidate."""
    response = supabase.table("extracted_skills").select("*").eq("candidate_id", candidate_id).execute()
    return response.data


def get_job_description(job_id: str) -> dict:
    """Fetch a job description by ID."""
    response = supabase.table("job_descriptions").select("*").eq("id", job_id).execute()
    if not response.data:
        return None
    return response.data[0]


def insert_score(candidate_id: str, job_id: str, ats_score: int, grade: str, breakdown: dict) -> dict:
    """Inserts a computed ATS score record into the ats_scores table."""
    data = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "ats_score": ats_score,
        "grade": grade,
        "breakdown": breakdown
    }
    response = supabase.table("ats_scores").insert(data).execute()
    return response.data[0]


def get_scores_for_candidate(candidate_id: str) -> list:
    """Fetch all ATS score records for a given candidate."""
    response = supabase.table("ats_scores").select("*").eq("candidate_id", candidate_id).execute()
    return response.data




