from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Any, List
import uuid

from app.models import Message
from app.rag.retriever import TranscriptRetriever


@dataclass
class SkillContext:
    """
    Context passed to each skill execution.
    """
    session_id: uuid.UUID
    user_message: str
    history: List[Message]
    provider_name: str
    retriever: TranscriptRetriever
    resolved_query: str = ""  # The query resolved for retrieval (may be context-augmented)


class BaseSkill(ABC):
    """
    Abstract Base Class for all assistant capabilities/skills.
    """
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute_stream(
        self, context: SkillContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the skill and yields structured event dictionaries:
        e.g. {"event": "status", "data": {...}}
             {"event": "sources", "data": {"sources": [...]}}
             {"event": "token", "data": {"content": "..."}}
             {"event": "done", "data": {}}
        """
        pass
