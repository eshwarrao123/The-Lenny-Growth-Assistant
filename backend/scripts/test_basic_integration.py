"""
Phase 8 Basic Integration Check.
Verifies:
1. Application health endpoint
2. Database connectivity
3. Ollama model reachability
4. One small grounded question (retrieval + SSE streaming)
5. One small artifact generation (SSE streaming + versioning)
6. Session and artifact persistence
"""

import asyncio
import json
import sys
import httpx

BASE_URL = "http://localhost:8000"


async def main():
    print("=" * 60)
    print("PHASE 8 — BASIC INTEGRATION CHECK")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Health Endpoint
        print("\n[1/6] Checking GET /api/health...")
        health_resp = await client.get("/api/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.status_code}"
        health_data = health_resp.json()
        print(f"      Status: {health_data.get('status')}")
        print(f"      Database: {health_data.get('db')}")
        print(f"      Ollama: {health_data.get('ollama')}")
        assert health_data.get("db") == "ok", "Database is not ok"
        assert health_data.get("status") in ("healthy", "degraded"), f"Unexpected health status: {health_data}"
        print("      PASS: Health endpoint operational.")

        # 2. Create Session
        print("\n[2/6] Creating chat session...")
        sess_resp = await client.post("/api/sessions")
        assert sess_resp.status_code == 200, f"Session creation failed: {sess_resp.status_code}"
        session_id = sess_resp.json()["id"]
        print(f"      Created session: {session_id}")
        print("      PASS: Session created.")

        # 3. One Small Grounded Question
        print("\n[3/6] Testing ONE small grounded question...")
        payload_qa = {
            "session_id": session_id,
            "message": "What is product-led sales according to Elena Verna? Keep it to two sentences.",
            "provider": "ollama",
        }
        got_sources = False
        tokens_received = 0
        async with client.stream("POST", "/api/chat", json=payload_qa) as stream:
            assert stream.status_code == 200
            async for line in stream.aiter_lines():
                if not line:
                    continue
                if line.startswith("event: sources"):
                    got_sources = True
                elif line.startswith("data: ") and '"content":' in line:
                    tokens_received += 1

        print(f"      Grounded sources received: {got_sources}")
        print(f"      Tokens streamed: {tokens_received}")
        assert got_sources, "Expected transcript grounding sources"
        assert tokens_received > 0, "Expected token stream"
        print("      PASS: Grounded QA streaming verified.")

        # 4. Verify Grounded QA Persistence
        print("\n[4/6] Verifying session message persistence...")
        get_sess = await client.get(f"/api/sessions/{session_id}")
        assert get_sess.status_code == 200
        sess_detail = get_sess.json()
        messages = sess_detail.get("messages", [])
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert len(messages[1].get("sources", [])) > 0, "Expected persisted sources in assistant message"
        print(f"      Persisted messages: {len(messages)}")
        print(f"      Persisted citations: {len(messages[1]['sources'])}")
        print("      PASS: Session message persistence verified.")

        # 5. One Small Artifact Generation
        print("\n[5/6] Testing ONE small markdown artifact...")
        payload_art = {
            "session_id": session_id,
            "message": "Create a short markdown checklist with 3 items for validating product-market fit.",
            "provider": "ollama",
        }
        artifact_id = None
        artifact_chunks = 0
        async with client.stream("POST", "/api/chat", json=payload_art) as stream:
            assert stream.status_code == 200
            async for line in stream.aiter_lines():
                if not line:
                    continue
                if line.startswith("event: artifact_chunk"):
                    artifact_chunks += 1
                elif line.startswith("data: ") and '"artifact_id":' in line:
                    try:
                        d = json.loads(line[6:])
                        artifact_id = d.get("artifact_id")
                    except Exception:
                        pass

        print(f"      Artifact chunks streamed: {artifact_chunks}")
        print(f"      Artifact ID: {artifact_id}")
        assert artifact_chunks > 0, "Expected artifact chunks streamed"
        assert artifact_id is not None, "Expected artifact_id in stream"
        print("      PASS: Small artifact streaming verified.")

        # 6. Verify Artifact Persistence via REST
        print("\n[6/6] Verifying artifact REST persistence...")
        art_resp = await client.get(f"/api/artifacts/{artifact_id}")
        assert art_resp.status_code == 200, f"Artifact fetch failed: {art_resp.status_code}"
        art_data = art_resp.json()
        assert art_data["id"] == artifact_id
        assert art_data["type"] == "markdown"
        assert len(art_data["content"]) > 0
        assert art_data["version"] >= 1
        print(f"      Persisted title: {art_data.get('title')}")
        print(f"      Persisted version: {art_data.get('version')}")
        print(f"      Content length: {len(art_data['content'])} chars")
        print("      PASS: Artifact REST persistence verified.")

    print("\n" + "=" * 60)
    print("ALL 6 BASIC INTEGRATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
