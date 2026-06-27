import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.jd_parser import parse_jd
from app.utils.supabase_client import insert_job_description

router = APIRouter()
logger = logging.getLogger(__name__)


class JobDescriptionRequest(BaseModel):
    raw_text: str


@router.post("")
async def create_job_description(request: JobDescriptionRequest):
    """
    Creates a new job description:
    1. Parses the job description raw text.
    2. Saves the parsed details and raw text to Supabase.
    3. Returns the saved job ID and parsed details.
    """
    raw_text = request.raw_text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail="Job description text cannot be empty."
        )

    # 1. Parse Job Description
    try:
        parsed_data = parse_jd(raw_text)
    except Exception as e:
        logger.error(f"Error parsing job description: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to parse job description."
        )

    # 2. Save to Supabase
    try:
        title = parsed_data.get("job_title", "Unknown Job Title")
        saved_record = insert_job_description(
            title=title,
            raw_text=raw_text,
            parsed_data=parsed_data
        )
    except Exception as e:
        logger.error(f"Error saving job description to Supabase: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to save parsed job description to database."
        )

    # 3. Return results
    return {
        "job_id": saved_record.get("id"),
        "parsed_data": parsed_data
    }
