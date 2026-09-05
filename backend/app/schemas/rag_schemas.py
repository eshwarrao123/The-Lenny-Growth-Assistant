from pydantic import BaseModel, UUID4, Field
from typing import Optional, List

class RetrievalResult(BaseModel):
    chunk_id: UUID4
    episode_id: UUID4
    episode_title: str
    guest_name: str
    source_path: Optional[str] = None
    transcript_text: str
    similarity_score: float
    speaker: Optional[str] = None
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.65
