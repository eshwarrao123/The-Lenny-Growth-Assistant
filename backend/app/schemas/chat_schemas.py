from pydantic import BaseModel, UUID4, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class ArtifactBase(BaseModel):
    id: UUID4
    type: Literal["html", "markdown"]
    title: Optional[str] = None
    content: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    id: UUID4
    role: Literal["user", "assistant", "system"]
    content: str
    sources: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    id: UUID4
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatSessionDetail(ChatSessionBase):
    messages: List[MessageBase] = []
    artifacts: List[ArtifactBase] = []

class ChatRequest(BaseModel):
    session_id: UUID4
    message: str
    provider: Literal["ollama", "openai"] = "ollama"

class CreateSessionResponse(BaseModel):
    id: UUID4
    title: str
