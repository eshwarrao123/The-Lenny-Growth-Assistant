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
    session_id: UUID4 = Field(
        ...,
        description="Target chat session UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    message: str = Field(
        ...,
        min_length=1,
        description="User question, follow-up prompt, or skill trigger command.",
        examples=["What does Elena Verna say about product-led sales?"]
    )
    provider: Literal["ollama", "openai"] = Field(
        default="ollama",
        description="LLM provider: 'ollama' (local default) or 'openai' (cloud).",
        examples=["ollama"]
    )
    skill: Optional[Literal["auto", "qa", "ship30", "artifact"]] = Field(
        default="auto",
        description="Target capability skill override. 'auto' uses deterministic intent routing.",
        examples=["auto"]
    )
    artifact_type: Optional[Literal["markdown", "html"]] = Field(
        default=None,
        description="Explicit artifact format preference if invoking the artifact skill directly.",
        examples=["markdown"]
    )

class CreateSessionResponse(BaseModel):
    id: UUID4
    title: str
