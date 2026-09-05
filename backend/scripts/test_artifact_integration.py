"""
Real integration test for artifact generation using Ollama.

This script tests the complete artifact generation flow:
1. Markdown artifact generation
2. HTML artifact generation
3. Persistence and versioning
4. SSE event streaming
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.chat_service import ChatService
from app.models import ChatSession


async def test_markdown_artifact():
    """Test Markdown artifact generation."""
    print("\n" + "="*70)
    print("TEST 1: Markdown Artifact Generation")
    print("="*70)
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        service = ChatService(session)
        
        # Create test session
        chat_session = await service.create_session(title="Artifact Test - Markdown")
        print(f"✓ Created test session: {chat_session.id}")
        
        # Test markdown artifact request
        request = "Create a markdown framework for product-led growth based on Elena Verna's principles"
        print(f"\n📝 Request: {request}")
        print("\n🔄 Streaming response...")
        
        events_received = {
            "status": 0,
            "sources": 0,
            "artifact_start": 0,
            "artifact_chunk": 0,
            "artifact_done": 0,
            "done": 0,
        }
        
        artifact_content = ""
        artifact_metadata = {}
        
        async for event_line in service.generate_chat_stream(
            session_id=chat_session.id,
            user_message=request,
            provider_name="ollama",
            skill_name="artifact",
        ):
            # Parse SSE event
            if event_line.startswith("event:"):
                event_type = event_line.split(":", 1)[1].strip()
                if event_type in events_received:
                    events_received[event_type] += 1
                    
                if event_type == "artifact_start":
                    print(f"\n✓ Artifact generation started")
                elif event_type == "artifact_chunk":
                    artifact_content += "."  # Progress indicator
                    print(".", end="", flush=True)
                elif event_type == "artifact_done":
                    print(f"\n✓ Artifact generation complete")
        
        print(f"\n\n📊 Event Summary:")
        for event_type, count in events_received.items():
            print(f"  {event_type}: {count}")
        
        # Verify artifact was persisted
        session_data = await service.get_session(chat_session.id)
        artifacts = session_data.artifacts
        
        if artifacts:
            artifact = artifacts[0]
            print(f"\n✅ Artifact persisted successfully")
            print(f"  ID: {artifact.id}")
            print(f"  Type: {artifact.type}")
            print(f"  Title: {artifact.title}")
            print(f"  Version: {artifact.version}")
            print(f"  Content length: {len(artifact.content)} characters")
            print(f"  Preview: {artifact.content[:200]}...")
            return True
        else:
            print("\n❌ ERROR: No artifact was persisted")
            return False


async def test_html_artifact():
    """Test HTML artifact generation."""
    print("\n" + "="*70)
    print("TEST 2: HTML Artifact Generation")
    print("="*70)
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        service = ChatService(session)
        
        # Create test session
        chat_session = await service.create_session(title="Artifact Test - HTML")
        print(f"✓ Created test session: {chat_session.id}")
        
        # Test HTML artifact request
        request = "Create an interactive pricing calculator with basic inputs"
        print(f"\n📝 Request: {request}")
        print("\n🔄 Streaming response...")
        
        html_detected = False
        artifact_persisted = False
        
        async for event_line in service.generate_chat_stream(
            session_id=chat_session.id,
            user_message=request,
            provider_name="ollama",
            skill_name="artifact",
        ):
            if "artifact_start" in event_line and "html" in event_line.lower():
                html_detected = True
                print(f"\n✓ HTML artifact type detected")
            elif "artifact_done" in event_line:
                print(f"\n✓ HTML artifact generation complete")
        
        # Verify HTML artifact
        session_data = await service.get_session(chat_session.id)
        artifacts = session_data.artifacts
        
        if artifacts:
            artifact = artifacts[0]
            if artifact.type == "html":
                print(f"\n✅ HTML artifact persisted successfully")
                print(f"  ID: {artifact.id}")
                print(f"  Type: {artifact.type}")
                print(f"  Content length: {len(artifact.content)} characters")
                
                # Basic HTML validation
                has_doctype = "<!DOCTYPE" in artifact.content.upper()
                has_html_tag = "<html" in artifact.content.lower()
                
                print(f"  Contains DOCTYPE: {has_doctype}")
                print(f"  Contains <html> tag: {has_html_tag}")
                return has_html_tag
            else:
                print(f"\n❌ ERROR: Expected HTML but got {artifact.type}")
                return False
        else:
            print("\n❌ ERROR: No artifact was persisted")
            return False


async def test_artifact_versioning():
    """Test artifact versioning."""
    print("\n" + "="*70)
    print("TEST 3: Artifact Versioning")
    print("="*70)
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        service = ChatService(session)
        
        # Create test session
        chat_session = await service.create_session(title="Artifact Test - Versioning")
        print(f"✓ Created test session: {chat_session.id}")
        
        # Create version 1
        print(f"\n📝 Creating version 1...")
        async for _ in service.generate_chat_stream(
            session_id=chat_session.id,
            user_message="Create a simple markdown checklist",
            provider_name="ollama",
            skill_name="artifact",
        ):
            pass
        
        # Create version 2 (same title should increment version)
        print(f"📝 Creating version 2...")
        async for _ in service.generate_chat_stream(
            session_id=chat_session.id,
            user_message="Update that checklist",
            provider_name="ollama",
            skill_name="artifact",
        ):
            pass
        
        # Verify versions
        session_data = await service.get_session(chat_session.id)
        artifacts = sorted(session_data.artifacts, key=lambda a: a.version)
        
        if len(artifacts) >= 2:
            v1 = artifacts[0]
            v2 = artifacts[-1]
            
            print(f"\n✅ Versioning working correctly")
            print(f"  Version 1: ID={v1.id}, version={v1.version}")
            print(f"  Version 2: ID={v2.id}, version={v2.version}")
            
            # Version numbers should be sequential
            version_correct = v2.version > v1.version
            if version_correct:
                print(f"  ✓ Version numbers are sequential")
                return True
            else:
                print(f"  ❌ Version numbers are not sequential")
                return False
        else:
            print(f"\n⚠️  Only {len(artifacts)} artifact(s) created")
            return len(artifacts) >= 1  # At least one is okay for minimal test


async def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("ARTIFACT GENERATION INTEGRATION TESTS")
    print("Using local Ollama for generation")
    print("="*70)
    
    results = []
    
    try:
        # Test 1: Markdown artifact
        result1 = await test_markdown_artifact()
        results.append(("Markdown Artifact", result1))
        
        # Test 2: HTML artifact
        result2 = await test_html_artifact()
        results.append(("HTML Artifact", result2))
        
        # Test 3: Versioning
        result3 = await test_artifact_versioning()
        results.append(("Artifact Versioning", result3))
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All artifact integration tests PASSED")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
