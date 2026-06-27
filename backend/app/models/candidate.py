from pydantic import BaseModel
from typing import Optional


class CandidateCreate(BaseModel):
    file_name: str
    file_path: str
    raw_text: Optional[str] = None
    status: str = "pending"


class CandidateResponse(BaseModel):
    candidate_id: str
    file_name: str
    raw_text: str
    char_count: int
    status: str
