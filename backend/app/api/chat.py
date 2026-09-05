import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat_schemas import ChatRequest
from app.services.chat_service import ChatService
from app.core.exceptions import InvalidRequestError, SessionNotFoundError

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post(
    "",
    summary="Generate Grounded Chat Stream",
    description="Streams Server-Sent Events (SSE) containing tokens, retrieved citations, and artifact blocks for a conversation turn.",
    response_description="Server-Sent Events text stream",
)
async def generate_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a grounded chat response for a given session.
    Streams back SSE tokens.
    """
    if not request.message or not request.message.strip():
        raise InvalidRequestError("Message cannot be empty.")

    chat_service = ChatService(db)
    
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    
    return StreamingResponse(
        chat_service.generate_chat_stream(
            session_id=request.session_id,
            user_message=request.message,
            provider_name=request.provider or "ollama",
            skill_name=request.skill or "auto",
        ),
        media_type="text/event-stream",
        headers=headers,
    )
