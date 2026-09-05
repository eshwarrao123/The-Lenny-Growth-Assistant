import logging
import uuid
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import ChatSession, Message
from app.rag.retriever import TranscriptRetriever
from app.rag.grounding import GroundingContextBuilder
from app.providers.factory import get_llm_provider
from app.core.exceptions import SessionNotFoundError, InvalidRequestError

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.retriever = TranscriptRetriever(session)
        
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
        provider_name: str = "ollama"
    ) -> AsyncGenerator[str, None]:
        if not user_message.strip():
            raise InvalidRequestError("Message cannot be empty.")
            
        chat_session = await self.get_session(session_id)
        
        # Sort history deterministically
        history = sorted(chat_session.messages, key=lambda m: (m.created_at, str(m.id)))
        
        # 1. Retrieve evidence
        sources = await self.retriever.retrieve(user_message)
        if not sources and history:
            prev_user_msgs = [m.content for m in history if m.role == "user"]
            if prev_user_msgs:
                augmented_query = f"{prev_user_msgs[-1]} {user_message}"
                sources = await self.retriever.retrieve(augmented_query)
        
        # 2. Convert sources to citations dict for SSE & DB
        citations = []
        for src in sources:
            citations.append({
                "chunk_id": str(src.chunk_id),
                "episode": src.episode_title,
                "guest": src.guest_name,
                "timestamp": src.start_timestamp,
                "similarity": src.similarity_score
            })
            
        # 3. Build context & prompt
        system_prompt = GroundingContextBuilder.build_system_prompt(sources)
        
        # 4. Construct messages for provider
        provider_messages = [{"role": "system", "content": system_prompt}]
        
        # Add history (last 10 messages)
        for msg in history[-10:]:
            provider_messages.append({"role": msg.role, "content": msg.content})
            
        provider_messages.append({"role": "user", "content": user_message})

        # 5. Persist user message
        db_user_msg = Message(session_id=session_id, role="user", content=user_message)
        self.session.add(db_user_msg)
        await self.session.commit()
        
        # Yield retrieving status and sources
        import json
        yield f"event: status\ndata: {json.dumps({'stage': 'retrieving'})}\n\n"
        
        if citations:
            yield f"event: sources\ndata: {json.dumps({'sources': citations})}\n\n"

        # Refusal fast-path if no sources found
        if not sources:
            refusal_text = "I don't have sufficient information in Lenny's Podcast archive to answer that reliably."
            yield f"event: status\ndata: {json.dumps({'stage': 'generating'})}\n\n"
            yield f"event: token\ndata: {json.dumps({'content': refusal_text})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            
            # Persist refusal
            db_assistant_msg = Message(session_id=session_id, role="assistant", content=refusal_text, sources=[])
            self.session.add(db_assistant_msg)
            await self.session.commit()
            return

        # 6. Call Provider
        try:
            provider = get_llm_provider(provider_name)
        except ValueError as e:
            yield f"event: error\ndata: {json.dumps({'code': 'invalid_provider', 'message': str(e)})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            return
            
        assistant_content = ""
        try:
            async for chunk in provider.generate_stream(provider_messages):
                event_type = chunk.get("event")
                data = chunk.get("data", {})
                
                if event_type == "token":
                    assistant_content += data.get("content", "")
                    
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                
        except Exception as e:
            logger.error(f"Provider generation failed: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'generation_error', 'message': str(e)})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            
        # 7. Persist assistant message
        db_assistant_msg = Message(
            session_id=session_id, 
            role="assistant", 
            content=assistant_content, 
            sources=citations
        )
        self.session.add(db_assistant_msg)
        await self.session.commit()
