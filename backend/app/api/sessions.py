import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List
from app.core.database import get_db
from app.schemas.chat_schemas import CreateSessionResponse, ChatSessionDetail, ChatSessionBase
from app.services.chat_service import ChatService
from app.core.exceptions import SessionNotFoundError

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.get("", response_model=List[ChatSessionBase])
async def list_sessions(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Retrieves existing persisted chat sessions ordered by most recently updated first.
    """
    chat_service = ChatService(db)
    return await chat_service.list_sessions(limit=limit)

@router.post("", response_model=CreateSessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    """
    Creates a new chat session.
    """
    chat_service = ChatService(db)
    session = await chat_service.create_session()
    return CreateSessionResponse(id=session.id, title=session.title or "New Chat")

@router.get("/{session_id}", response_model=ChatSessionDetail)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a session and its message history.
    """
    chat_service = ChatService(db)
    try:
        session = await chat_service.get_session(session_id)
        return session
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
