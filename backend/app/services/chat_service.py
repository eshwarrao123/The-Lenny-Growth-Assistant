import json
import logging
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import ChatSession, Message, Artifact
from app.rag.retriever import TranscriptRetriever
from app.services.skills import SkillRouter, SkillContext
from app.core.exceptions import SessionNotFoundError, InvalidRequestError
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("chat_service")

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
        current_artifact = None
        artifact_content = ""
        start_time = time.perf_counter()

        logger.info(
            "chat_stream_started",
            session_id=str(session_id),
            skill=skill.name,
            provider=provider_name,
            message_len=len(user_message),
        )

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
                elif event_type == "artifact_start":
                    # Initialize artifact tracking
                    current_artifact = {
                        "type": data.get("type", "markdown"),
                        "title": data.get("title", "Artifact"),
                        "version": 1,
                    }
                    artifact_content = ""
                elif event_type == "artifact_chunk":
                    # Accumulate artifact content
                    artifact_content += data.get("content", "")
                elif event_type == "artifact_done":
                    # Persist artifact to database
                    if current_artifact and artifact_content:
                        artifact_id = await self._persist_artifact(
                            session_id=session_id,
                            message_id=None,  # Will link after assistant message is created
                            artifact_type=current_artifact["type"],
                            title=current_artifact["title"],
                            content=artifact_content,
                        )
                        # Update data with artifact ID for frontend
                        data["artifact_id"] = str(artifact_id)
                        current_artifact["id"] = artifact_id

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "chat_stream_failed",
                session_id=str(session_id),
                skill=skill.name,
                provider=provider_name,
                error_type=type(e).__name__,
                error_code="skill_execution_error",
                error_message=str(e),
                total_latency_ms=elapsed_ms,
            )
            yield f"event: error\ndata: {json.dumps({'code': 'skill_execution_error', 'message': str(e)})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            return

        # 5. Persist assistant message
        db_assistant_msg = Message(
            session_id=session_id, 
            role="assistant", 
            content=assistant_content if assistant_content else f"Generated {current_artifact['type'] if current_artifact else 'artifact'}", 
            sources=citations
        )
        self.session.add(db_assistant_msg)
        await self.session.commit()
        await self.session.refresh(db_assistant_msg)

        # 6. Link artifact to assistant message if created
        if current_artifact and current_artifact.get("id"):
            await self._link_artifact_to_message(
                artifact_id=current_artifact["id"],
                message_id=db_assistant_msg.id
            )

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "chat_stream_completed",
            session_id=str(session_id),
            skill=skill.name,
            provider=provider_name,
            retrieval_count=len(citations),
            content_length=len(assistant_content),
            has_artifact=bool(current_artifact),
            total_latency_ms=total_latency_ms,
        )

    async def _persist_artifact(
        self,
        session_id: uuid.UUID,
        message_id: Optional[uuid.UUID],
        artifact_type: str,
        title: str,
        content: str,
    ) -> uuid.UUID:
        """
        Persists an artifact to the database with versioning support.
        Enforces size limits to prevent unbounded storage growth.
        """
        # Validate artifact size
        settings = get_settings()
        content_bytes = len(content.encode('utf-8'))
        max_size = settings.artifact_max_bytes
        
        if content_bytes > max_size:
            raise InvalidRequestError(
                f"Artifact size ({content_bytes} bytes) exceeds maximum allowed size "
                f"({max_size} bytes, ~{max_size // (1024*1024)}MB)"
            )
        
        # Check if there's an existing artifact with same title in this session
        stmt = (
            select(Artifact)
            .where(Artifact.session_id == session_id)
            .where(Artifact.title == title)
            .order_by(Artifact.version.desc())
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        version = 1
        if existing:
            version = existing.version + 1

        artifact = Artifact(
            session_id=session_id,
            message_id=message_id,
            type=artifact_type,
            title=title,
            content=content,
            version=version,
        )
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        
        logger.info(f"Persisted artifact {artifact.id} (v{version}) for session {session_id}, size: {content_bytes} bytes")
        return artifact.id

    async def _link_artifact_to_message(
        self,
        artifact_id: uuid.UUID,
        message_id: uuid.UUID,
    ):
        """
        Links an artifact to a message after both are created.
        """
        stmt = select(Artifact).where(Artifact.id == artifact_id)
        result = await self.session.execute(stmt)
        artifact = result.scalars().first()
        
        if artifact:
            artifact.message_id = message_id
            await self.session.commit()
            logger.debug(f"Linked artifact {artifact_id} to message {message_id}")

    async def get_artifact(self, artifact_id: uuid.UUID) -> Optional[Artifact]:
        """
        Retrieves a specific artifact by ID.
        """
        stmt = select(Artifact).where(Artifact.id == artifact_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_artifact_versions(
        self,
        session_id: uuid.UUID,
        title: str,
    ) -> List[Artifact]:
        """
        Retrieves all versions of an artifact by title.
        """
        stmt = (
            select(Artifact)
            .where(Artifact.session_id == session_id)
            .where(Artifact.title == title)
            .order_by(Artifact.version.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
