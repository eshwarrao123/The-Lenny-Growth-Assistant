"""
Artifact API endpoints for retrieving and managing generated artifacts.
"""

import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.chat_service import ChatService
from app.schemas.artifact_schemas import ArtifactResponse, ArtifactListResponse, ArtifactVersionResponse

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])
logger = logging.getLogger(__name__)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific artifact by ID.
    """
    chat_service = ChatService(session)
    artifact = await chat_service.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found"
        )
    
    return artifact


@router.get("/session/{session_id}", response_model=ArtifactListResponse)
async def list_session_artifacts(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    List all artifacts for a session.
    """
    chat_service = ChatService(session)
    chat_session = await chat_service.get_session(session_id)
    
    artifacts = sorted(chat_session.artifacts, key=lambda a: a.created_at, reverse=True)
    
    return {
        "artifacts": artifacts,
        "total": len(artifacts)
    }


@router.get("/versions/{session_id}/{title}", response_model=ArtifactVersionResponse)
async def get_artifact_versions(
    session_id: uuid.UUID,
    title: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieve all versions of an artifact by title.
    """
    chat_service = ChatService(session)
    versions = await chat_service.get_artifact_versions(session_id, title)
    
    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No artifacts found with title '{title}' in session {session_id}"
        )
    
    return {"versions": versions}
