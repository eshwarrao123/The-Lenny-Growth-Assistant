import re
import logging
from typing import Optional, List, Tuple
from app.models import Message
from app.services.skills.base import BaseSkill
from app.services.skills.grounded_qa import GroundedQASkill
from app.services.skills.ship30 import Ship30Skill
from app.services.skills.artifact import ArtifactSkill

logger = logging.getLogger(__name__)

# Patterns that signal a Ship 30 for 30 essay request
SHIP30_TRIGGERS = [
    r"^/ship30\b",
    r"^/essay\b",
    r"\bship\s*30(\s*for\s*30)?\b",
    r"\batomic\s+essay\b",
    r"\bturn\s+(this|that|it)\s+into\s+(a\s+)?(ship\s*30|essay)\b",
    r"\bwrite\s+(a\s+)?(ship\s*30|atomic\s+essay|1[,.]?250\s*words?\s+essay)\b",
    r"\bgive\s+me\s+the\s+ship\s*30\b",
    r"\bmake\s+(this|that)\s+into\s+a\s+ship\s*30\b",
]

# Patterns that signal artifact generation request
ARTIFACT_TRIGGERS = [
    r"^/artifact\b",
    r"\b(create|generate|build|make)\s+(?:a|an)?\s*(?:[a-z0-9\-]+\s+){0,3}(markdown|html|interactive|calculator|dashboard|framework|memo|checklist|artifact|visualization)\b",
    r"\bturn\s+(this|that)\s+into\s+(?:a|an)?\s*(?:[a-z0-9\-]+\s+){0,3}(markdown|html|framework|memo|artifact|calculator|dashboard|checklist)\b",
    r"\bconvert.*into.*artifact\b",
]


class SkillRouter:
    """
    Deterministic router that maps incoming requests and conversation history
    to the appropriate skill capability.
    """

    def __init__(self):
        self.grounded_qa_skill = GroundedQASkill()
        self.ship30_skill = Ship30Skill()
        self.artifact_skill = ArtifactSkill()

    def route(
        self,
        user_message: str,
        history: Optional[List[Message]] = None,
        explicit_skill: Optional[str] = None,
    ) -> Tuple[BaseSkill, str]:
        """
        Determines the appropriate skill to execute and returns (skill, resolved_query).
        
        Args:
            user_message: Raw user input text.
            history: Recent conversation messages (for anaphora resolution).
            explicit_skill: Optional explicit skill name ('qa', 'ship30', 'auto').
            
        Returns:
            Tuple of (selected BaseSkill instance, resolved query string).
        """
        history = history or []
        msg_clean = user_message.strip()

        # 1. Explicit skill override
        if explicit_skill and explicit_skill.lower() not in ("auto", "default"):
            skill_name = explicit_skill.lower()
            if skill_name == "ship30":
                resolved = self._resolve_topic(msg_clean, history)
                return self.ship30_skill, resolved
            elif skill_name == "artifact":
                resolved = self._resolve_topic(msg_clean, history)
                return self.artifact_skill, resolved
            elif skill_name in ("qa", "grounded_qa"):
                return self.grounded_qa_skill, msg_clean

        # 2. Check Ship 30 triggers
        for pattern in SHIP30_TRIGGERS:
            if re.search(pattern, msg_clean, flags=re.IGNORECASE):
                logger.info(f"SkillRouter matched Ship 30 trigger: '{pattern}'")
                resolved = self._resolve_topic(msg_clean, history)
                return self.ship30_skill, resolved

        # 3. Check Artifact triggers
        for pattern in ARTIFACT_TRIGGERS:
            if re.search(pattern, msg_clean, flags=re.IGNORECASE):
                logger.info(f"SkillRouter matched Artifact trigger: '{pattern}'")
                resolved = self._resolve_topic(msg_clean, history)
                return self.artifact_skill, resolved

        # 4. Default: Grounded Q&A
        logger.debug("SkillRouter defaulting to GroundedQASkill")
        return self.grounded_qa_skill, msg_clean

    def _resolve_topic(self, message: str, history: List[Message]) -> str:
        """
        Extracts the subject topic for a Ship 30 request, resolving pronouns
        or follow-up references ('that', 'this') from prior conversation turns.
        """
        if self.ship30_skill._is_anaphoric(message) and history:
            resolved = self.ship30_skill._resolve_from_history(history)
            if resolved:
                return resolved

        core = self.ship30_skill._extract_core_topic(message)
        if (not core or self.ship30_skill._is_anaphoric(core)) and history:
            resolved = self.ship30_skill._resolve_from_history(history)
            if resolved:
                return resolved
        return core if core else message
