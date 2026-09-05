import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.chat_schemas import ChatRequest
from app.services.chat_service import ChatService
from app.core.exceptions import InvalidRequestError, SessionNotFoundError

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("")
async def generate_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a grounded chat response for a given session.
    Streams back SSE tokens.
    """
    chat_service = ChatService(db)
    
    # We return a streaming response
    return StreamingResponse(
        chat_service.generate_chat_stream(
            session_id=request.session_id,
            user_message=request.message,
            provider_name=request.provider
        ),
        media_type="text/event-stream"
    )
