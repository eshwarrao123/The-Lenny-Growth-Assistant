"""
Artifact-related Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, UUID4, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


class ArtifactCreate(BaseModel):
    """Schema for creating a new artifact."""
    session_id: UUID4
    message_id: Optional[UUID4] = None
    type: Literal["html", "markdown"]
    title: Optional[str] = None
    content: str
    sources: List[Dict[str, Any]] = []


class ArtifactUpdate(BaseModel):
    """Schema for updating an artifact (creates new version)."""
    content: str
    title: Optional[str] = None


class ArtifactResponse(BaseModel):
    """Schema for artifact responses."""
    id: UUID4
    session_id: UUID4
    message_id: Optional[UUID4] = None
    type: Literal["html", "markdown"]
    title: Optional[str] = None
    content: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Schema for listing artifacts."""
    artifacts: List[ArtifactResponse]
    total: int


class ArtifactVersionResponse(BaseModel):
    """Schema for artifact version history."""
    versions: List[ArtifactResponse]
