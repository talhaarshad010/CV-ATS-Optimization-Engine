import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extract
from app.utils.supabase_client import upload_file_to_storage, insert_candidate
from app.models.candidate import CandidateResponse

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


@router.post("/upload", response_model=CandidateResponse)
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload a CV (PDF or DOCX).
    Extracts raw text, stores file in Supabase Storage,
    inserts a candidate record, and returns structured data.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Upload PDF or DOCX only.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    candidate_id = str(uuid.uuid4())
    ext = ".pdf" if "pdf" in file.content_type else ".docx"
    storage_path = f"cvs/{candidate_id}{ext}"

    try:
        raw_text = extract(file_bytes, file.content_type, candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail="Text extraction failed.")

    try:
        upload_file_to_storage(file_bytes, storage_path, file.content_type)
    except Exception as e:
        logger.error(f"Storage upload error: {e}")
        raise HTTPException(status_code=500, detail="File storage failed.")

    try:
        insert_candidate({
            "id": candidate_id,
            "file_name": file.filename,
            "file_path": storage_path,
            "raw_text": raw_text,
            "status": "extracted",
        })
    except Exception as e:
        logger.error(f"DB insert error: {e}")
        raise HTTPException(status_code=500, detail="Database insert failed.")

    return CandidateResponse(
        candidate_id=candidate_id,
        file_name=file.filename,
        raw_text=raw_text,
        char_count=len(raw_text),
        status="extracted",
    )
