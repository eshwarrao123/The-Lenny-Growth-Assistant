"""
Tests for artifact generation, persistence, and retrieval.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.skills.artifact import ArtifactSkill
from app.services.skills.router import SkillRouter
from app.services.skills.base import SkillContext
from app.models import Message


@pytest.mark.asyncio
class TestArtifactSkill:
    """Test suite for ArtifactSkill functionality."""

    def test_parse_artifact_request_html(self):
        """Test HTML artifact detection."""
        skill = ArtifactSkill()
        
        test_cases = [
            ("Create an interactive calculator", "html"),
            ("Build a dashboard for this", "html"),
            ("Make an HTML visualization", "html"),
            ("Generate a pricing calculator", "html"),
        ]
        
        for request, expected_type in test_cases:
            artifact_type, _ = skill._parse_artifact_request(request, request)
            assert artifact_type == expected_type, f"Failed for: {request}"

    def test_parse_artifact_request_markdown(self):
        """Test Markdown artifact detection (default)."""
        skill = ArtifactSkill()
        
        test_cases = [
            "Create a framework from this",
            "Turn this into a strategy memo",
            "Generate a checklist",
            "Make a markdown document",
        ]
        
        for request in test_cases:
            artifact_type, _ = skill._parse_artifact_request(request, request)
            assert artifact_type == "markdown", f"Failed for: {request}"

    def test_requires_grounding_positive(self):
        """Test grounding detection for evidence-based requests."""
        skill = ArtifactSkill()
        
        test_cases = [
            "Create a framework based on Elena Verna's advice",
            "Make a checklist using insights from the conversation",
            "Generate a memo from this discussion",
            "Build a calculator based on Brian Balfour's model",
        ]
        
        for request in test_cases:
            requires = skill._requires_grounding(request)
            assert requires is True, f"Failed for: {request}"

    def test_requires_grounding_negative(self):
        """Test grounding detection for generic requests."""
        skill = ArtifactSkill()
        
        test_cases = [
            "Create a pricing calculator",
            "Make a generic onboarding checklist",
            "Build a simple dashboard",
        ]
        
        for request in test_cases:
            requires = skill._requires_grounding(request)
            assert requires is False, f"Failed for: {request}"

    def test_generate_title(self):
        """Test artifact title generation."""
        skill = ArtifactSkill()
        
        test_cases = [
            ("Create a pricing calculator", "Calculator"),
            ("Make a dashboard", "Dashboard"),
            ("Build a framework for PLG", "Framework"),
            ("Generate a strategy memo", "Strategy Memo"),
            ("Create a checklist", "Checklist"),
            ("Something generic", "Artifact"),
        ]
        
        for request, expected_title in test_cases:
            title = skill._generate_title(request)
            assert title == expected_title, f"Failed for: {request}"

    @pytest.mark.asyncio
    async def test_execute_stream_markdown(self):
        """Test markdown artifact generation flow."""
        skill = ArtifactSkill()
        
        # Mock provider
        with patch('app.services.skills.artifact.get_llm_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            # Make generate_stream return the async generator directly, not wrapped in AsyncMock
            mock_provider.generate_stream = MagicMock(
                return_value=self._async_gen([
                    {"type": "content", "content": "# Test Markdown\n\n"},
                    {"type": "content", "content": "This is a test."},
                ])
            )
            mock_get_provider.return_value = mock_provider
            
            # Mock retriever
            mock_retriever = AsyncMock()
            mock_retriever.retrieve = AsyncMock(return_value=[])
            
            context = SkillContext(
                session_id=uuid.uuid4(),
                user_message="Create a markdown framework",
                history=[],
                provider_name="ollama",
                retriever=mock_retriever,
                resolved_query="Create a markdown framework",
            )
            
            events = []
            async for event in skill.execute_stream(context):
                events.append(event)
            
            # Verify event sequence
            event_types = [e["event"] for e in events]
            assert "status" in event_types
            assert "artifact_start" in event_types
            assert "artifact_chunk" in event_types
            assert "artifact_done" in event_types
            assert "done" in event_types

    @pytest.mark.asyncio
    async def test_execute_stream_with_grounding(self):
        """Test artifact generation with transcript grounding."""
        skill = ArtifactSkill()
        
        # Mock provider
        with patch('app.services.skills.artifact.get_llm_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            # Make generate_stream return the async generator directly, not wrapped in AsyncMock
            mock_provider.generate_stream = MagicMock(
                return_value=self._async_gen([
                    {"type": "content", "content": "Test content"},
                ])
            )
            mock_get_provider.return_value = mock_provider
            
            # Mock retriever with results
            mock_retriever = AsyncMock()
            mock_result = MagicMock()
            mock_result.episode_id = uuid.uuid4()
            mock_result.episode_title = "Test Episode"
            mock_result.guest_name = "Test Guest"
            mock_result.text = "Test transcript content"
            mock_result.score = 0.85
            mock_result.speaker = "Test Guest"
            mock_result.start_time = "00:10:00"
            
            mock_retriever.retrieve = AsyncMock(return_value=[mock_result])
            
            context = SkillContext(
                session_id=uuid.uuid4(),
                user_message="Create a framework based on Test Guest's advice",
                history=[],
                provider_name="ollama",
                retriever=mock_retriever,
                resolved_query="Create a framework based on Test Guest's advice",
            )
            
            events = []
            async for event in skill.execute_stream(context):
                events.append(event)
            
            # Verify sources event is emitted
            source_events = [e for e in events if e["event"] == "sources"]
            assert len(source_events) > 0
            assert len(source_events[0]["data"]["sources"]) > 0

    async def _async_gen(self, items):
        """Helper to create async generator from list."""
        for item in items:
            yield item


class TestArtifactRouter:
    """Test suite for artifact routing."""

    def test_route_explicit_artifact_skill(self):
        """Test explicit artifact skill selection."""
        router = SkillRouter()
        
        skill, resolved = router.route(
            user_message="Create a framework",
            history=[],
            explicit_skill="artifact",
        )
        
        assert skill.name == "artifact"

    def test_route_artifact_triggers(self):
        """Test artifact trigger patterns."""
        router = SkillRouter()
        
        test_cases = [
            "Create a markdown memo about this",
            "Generate an interactive calculator",
            "Build a dashboard for these metrics",
            "Make an HTML visualization",
            "/artifact Create a framework",
        ]
        
        for message in test_cases:
            skill, _ = router.route(message, history=[])
            assert skill.name == "artifact", f"Failed to route artifact for: {message}"

    def test_route_ship30_not_artifact(self):
        """Test that Ship 30 requests don't route to artifact."""
        router = SkillRouter()
        
        skill, _ = router.route(
            user_message="Write a Ship 30 essay about retention",
            history=[],
        )
        
        assert skill.name == "ship30"

    def test_route_qa_default(self):
        """Test that normal questions route to QA."""
        router = SkillRouter()
        
        skill, _ = router.route(
            user_message="What does Elena Verna say about PLG?",
            history=[],
        )
        
        assert skill.name == "grounded_qa"


@pytest.mark.asyncio
class TestArtifactPersistence:
    """Test suite for artifact persistence and versioning."""

    @pytest.mark.asyncio
    async def test_artifact_versioning(self, async_session):
        """Test that updating an artifact increments version."""
        from app.services.chat_service import ChatService
        
        service = ChatService(async_session)
        session_id = uuid.uuid4()
        
        # Create session first
        from app.models import ChatSession
        chat_session = ChatSession(id=session_id, title="Test")
        async_session.add(chat_session)
        await async_session.commit()
        
        # Create first artifact
        artifact_id_v1 = await service._persist_artifact(
            session_id=session_id,
            message_id=None,
            artifact_type="markdown",
            title="Test Framework",
            content="Version 1 content",
        )
        
        # Create second artifact with same title (should increment version)
        artifact_id_v2 = await service._persist_artifact(
            session_id=session_id,
            message_id=None,
            artifact_type="markdown",
            title="Test Framework",
            content="Version 2 content",
        )
        
        # Verify versions
        artifact_v1 = await service.get_artifact(artifact_id_v1)
        artifact_v2 = await service.get_artifact(artifact_id_v2)
        
        assert artifact_v1.version == 1
        assert artifact_v2.version == 2
        assert artifact_v1.content == "Version 1 content"
        assert artifact_v2.content == "Version 2 content"

    @pytest.mark.asyncio
    async def test_get_artifact_versions(self, async_session):
        """Test retrieving all versions of an artifact."""
        from app.services.chat_service import ChatService
        from app.models import ChatSession
        
        service = ChatService(async_session)
        session_id = uuid.uuid4()
        
        # Create session
        chat_session = ChatSession(id=session_id, title="Test")
        async_session.add(chat_session)
        await async_session.commit()
        
        # Create multiple versions
        for i in range(1, 4):
            await service._persist_artifact(
                session_id=session_id,
                message_id=None,
                artifact_type="markdown",
                title="Test Artifact",
                content=f"Version {i} content",
            )
        
        # Retrieve all versions
        versions = await service.get_artifact_versions(session_id, "Test Artifact")
        
        assert len(versions) == 3
        assert [v.version for v in versions] == [1, 2, 3]


def test_artifact_security_prompt():
    """Test that artifact prompt includes security instructions."""
    skill = ArtifactSkill()
    
    prompt = skill._build_artifact_prompt(
        artifact_type="html",
        artifact_request="Create a calculator",
        retrieved_context="",
        conversation_history=[],
    )
    
    # Verify security instructions are present
    assert "IMPORTANT SECURITY RULES" in prompt
    assert "self-contained" in prompt.lower()
    assert "sandbox" in prompt.lower() or "isolation" in prompt.lower()


def test_artifact_grounding_isolation():
    """Test that transcript context is properly isolated in prompt."""
    skill = ArtifactSkill()
    
    context_text = "Test transcript content"
    
    prompt = skill._build_artifact_prompt(
        artifact_type="markdown",
        artifact_request="Create a framework",
        retrieved_context=context_text,
        conversation_history=[],
    )
    
    # Verify context is wrapped in delimiters
    assert "<transcript_context>" in prompt
    assert "</transcript_context>" in prompt
    assert context_text in prompt
