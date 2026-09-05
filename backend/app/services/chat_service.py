import json
import logging
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import ChatSession, Message
from app.rag.retriever import TranscriptRetriever
from app.services.skills import SkillRouter, SkillContext
from app.core.exceptions import SessionNotFoundError, InvalidRequestError

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.retriever = TranscriptRetriever(session)
        self.router = SkillRouter()
        
    async def create_session(self, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(title=title)
        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        return chat_session

    async def get_session(self, session_id: uuid.UUID) -> ChatSession:
        stmt = (
            select(ChatSession)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.artifacts),
            )
            .where(ChatSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        chat_session = result.scalars().first()
        if not chat_session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        return chat_session

    async def generate_chat_stream(
        self, 
        session_id: uuid.UUID, 
        user_message: str, 
        provider_name: str = "ollama",
        skill_name: Optional[str] = "auto",
    ) -> AsyncGenerator[str, None]:
        if not user_message.strip():
            raise InvalidRequestError("Message cannot be empty.")
            
        chat_session = await self.get_session(session_id)
        
        # Sort history deterministically
        history = sorted(chat_session.messages, key=lambda m: (m.created_at, str(m.id)))

        # 1. Route to skill capability
        skill, resolved_query = self.router.route(
            user_message=user_message,
            history=history,
            explicit_skill=skill_name,
        )

        # 2. Persist user message
        db_user_msg = Message(session_id=session_id, role="user", content=user_message)
        self.session.add(db_user_msg)
        await self.session.commit()

        # 3. Create execution context
        context = SkillContext(
            session_id=session_id,
            user_message=user_message,
            history=history,
            provider_name=provider_name,
            retriever=self.retriever,
            resolved_query=resolved_query,
        )

        # 4. Stream events from selected skill
        assistant_content = ""
        citations = []

        # Emit start event to notify client of active skill and session
        yield f"event: start\ndata: {json.dumps({'session_id': str(session_id), 'skill': skill.name})}\n\n"

        try:
            async for chunk in skill.execute_stream(context):
                event_type = chunk.get("event")
                data = chunk.get("data", {})

                if event_type == "sources":
                    citations = data.get("sources", [])
                elif event_type == "token":
                    assistant_content += data.get("content", "")

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        except Exception as e:
            logger.error(f"Execution failed for skill {skill.name}: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'skill_execution_error', 'message': str(e)})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"

        # 5. Persist assistant message
        db_assistant_msg = Message(
            session_id=session_id, 
            role="assistant", 
            content=assistant_content, 
            sources=citations
        )
        self.session.add(db_assistant_msg)
        await self.session.commit()
