import logging
from typing import AsyncGenerator, Dict, Any, List
from app.services.skills.base import BaseSkill, SkillContext
from app.rag.grounding import GroundingContextBuilder
from app.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE = "I don't have sufficient information in Lenny's Podcast archive to answer that reliably."


class GroundedQASkill(BaseSkill):
    """
    Default skill providing grounded Q&A over Lenny's Podcast archive with
    strict negative fallback when context is insufficient.
    """
    name: str = "grounded_qa"
    description: str = "Grounded question answering using Lenny's Podcast transcripts"

    async def execute_stream(
        self, context: SkillContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # 1. Yield retrieving status
        yield {"event": "status", "data": {"stage": "retrieving"}}

        # 2. Retrieve evidence
        retrieval_query = context.resolved_query or context.user_message
        sources = await context.retriever.retrieve(retrieval_query)

        # Context-augmented retrieval fallback if standalone query yields no sources
        if not sources and context.history:
            prev_user_msgs = [m.content for m in context.history if m.role == "user"]
            if prev_user_msgs:
                augmented_query = f"{prev_user_msgs[-1]} {context.user_message}"
                sources = await context.retriever.retrieve(augmented_query)

        # 3. Format citations
        citations = []
        for src in sources:
            citations.append({
                "chunk_id": str(src.chunk_id),
                "episode": src.episode_title,
                "guest": src.guest_name,
                "timestamp": src.start_timestamp,
                "similarity": src.similarity_score,
            })

        if citations:
            yield {"event": "sources", "data": {"sources": citations}}

        # 4. Refusal fast-path if evidence is insufficient
        if not sources:
            yield {"event": "status", "data": {"stage": "generating"}}
            yield {"event": "token", "data": {"content": REFUSAL_MESSAGE}}
            yield {"event": "done", "data": {}}
            return

        # 5. Build prompt
        system_prompt = GroundingContextBuilder.build_system_prompt(sources)
        provider_messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history (last 10 messages)
        for msg in context.history[-10:]:
            provider_messages.append({"role": msg.role, "content": msg.content})

        provider_messages.append({"role": "user", "content": context.user_message})

        # 6. Call LLM provider
        try:
            provider = get_llm_provider(context.provider_name)
        except ValueError as e:
            yield {"event": "error", "data": {"code": "invalid_provider", "message": str(e)}}
            yield {"event": "done", "data": {}}
            return

        try:
            async for chunk in provider.generate_stream(provider_messages):
                yield chunk
        except Exception as e:
            logger.error(f"Provider generation failed in GroundedQASkill: {e}")
            yield {"event": "error", "data": {"code": "generation_error", "message": str(e)}}
            yield {"event": "done", "data": {}}
