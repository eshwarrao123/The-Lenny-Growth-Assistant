import asyncio
import json
import logging
import httpx
from httpx import ASGITransport
from app.main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ship30_integration")

async def parse_sse_stream(stream_resp):
    """Helper to parse SSE lines into structured events."""
    events = []
    current_event = None
    current_data = None
    
    async for line in stream_resp.aiter_lines():
        if not line:
            if current_event and current_data is not None:
                try:
                    parsed_data = json.loads(current_data)
                except Exception:
                    parsed_data = current_data
                events.append({"event": current_event, "data": parsed_data})
                if current_event == "error":
                    print(f"\n[SSE ERROR] {parsed_data}", flush=True)
                elif current_event == "start":
                    print(f"\n[SSE START] {parsed_data}", flush=True)
                elif current_event == "token":
                    content = parsed_data.get("content", "") if isinstance(parsed_data, dict) else ""
                    print(content, end="", flush=True)
            current_event = None
            current_data = None
            continue
            
        if line.startswith("event:"):
            current_event = line.replace("event:", "").strip()
        elif line.startswith("data:"):
            current_data = line.replace("data:", "").strip()
            
    if current_event and current_data is not None:
        try:
            parsed_data = json.loads(current_data)
        except Exception:
            parsed_data = current_data
        events.append({"event": current_event, "data": parsed_data})
        
    return events

async def run_integration_test():
    print("==================================================", flush=True)
    print("PHASE 5: REAL LOCAL OLLAMA SHIP 30 INTEGRATION TEST", flush=True)
    print("==================================================", flush=True)
    
    timeout = httpx.Timeout(360.0, connect=30.0)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver", timeout=timeout) as client:
        # ----------------------------------------------------
        # 1. Create Session
        # ----------------------------------------------------
        print("\n--- 1. Creating Session A ---")
        resp = await client.post("/api/sessions", json={"title": "Elena Verna PLS to Ship30"})
        assert resp.status_code == 200, f"Failed to create session: {resp.text}"
        session_id = resp.json()["id"]
        print(f"Session A Created: {session_id}")
        
        # ----------------------------------------------------
        # 2. Ask Grounded QA Question
        # ----------------------------------------------------
        print("\n--- 2. Turn 1: Grounded QA Question ---")
        q1 = "What does Elena Verna say about product-led sales?"
        print(f"User: '{q1}'")
        
        payload1 = {
            "session_id": session_id,
            "message": q1,
            "provider": "ollama",
            "skill": "auto"
        }
        
        async with client.stream("POST", "/api/chat", json=payload1) as stream_resp:
            assert stream_resp.status_code == 200
            events1 = await parse_sse_stream(stream_resp)
            
        start_event1 = next((e for e in events1 if e["event"] == "start"), None)
        assert start_event1 is not None, "Missing start event in Turn 1"
        routed_skill1 = start_event1["data"].get("skill")
        print(f"Turn 1 Routed Skill: {routed_skill1}")
        assert routed_skill1 == "grounded_qa", f"Expected grounded_qa, got {routed_skill1}"
        
        sources_event1 = next((e for e in events1 if e["event"] == "sources"), None)
        assert sources_event1 is not None, "Missing sources event in Turn 1"
        sources1 = sources_event1["data"].get("sources", [])
        print(f"Turn 1 Retrieved Sources: {len(sources1)} chunks")
        assert len(sources1) > 0, "Expected at least 1 retrieved source chunk"
        for s in sources1[:2]:
            print(f"  - [{s.get('guest', 'Unknown')}] {s.get('title', 'Unknown')} (similarity: {s.get('similarity', 0):.3f})")
            
        tokens1 = [e["data"].get("content", "") for e in events1 if e["event"] == "token"]
        q1_response = "".join(tokens1)
        print(f"Turn 1 Answer Sample ({len(q1_response.split())} words):\n{q1_response[:300]}...\n")
        assert len(tokens1) > 0, "No answer tokens generated in Turn 1"
        
        # Verify Turn 1 DB persistence
        session_detail1 = (await client.get(f"/api/sessions/{session_id}")).json()
        assert len(session_detail1["messages"]) == 2
        assert session_detail1["messages"][0]["role"] == "user"
        assert session_detail1["messages"][1]["role"] == "assistant"
        assert len(session_detail1["messages"][1]["sources"]) > 0
        print("Turn 1 Persisted Successfully in PostgreSQL.")
        
        # ----------------------------------------------------
        # 3. Ask Ship 30 Follow-Up ("Turn that into a Ship 30 for 30 essay.")
        # ----------------------------------------------------
        print("\n--- 3. Turn 2: Follow-up Ship 30 Essay Request ---")
        q2 = "Turn that into a Ship 30 for 30 essay."
        print(f"User: '{q2}'")
        
        payload2 = {
            "session_id": session_id,
            "message": q2,
            "provider": "ollama",
            "skill": "auto"
        }
        
        print("Invoking real Ollama qwen2.5:7b generation for Ship 30 essay (this may take 30-90s)...")
        async with client.stream("POST", "/api/chat", json=payload2) as stream_resp:
            assert stream_resp.status_code == 200
            events2 = await parse_sse_stream(stream_resp)
            
        start_event2 = next((e for e in events2 if e["event"] == "start"), None)
        assert start_event2 is not None, "Missing start event in Turn 2"
        routed_skill2 = start_event2["data"].get("skill")
        print(f"Turn 2 Routed Skill: {routed_skill2}")
        assert routed_skill2 == "ship30", f"Expected ship30, got {routed_skill2}"
        
        sources_event2 = next((e for e in events2 if e["event"] == "sources"), None)
        assert sources_event2 is not None, "Missing sources event in Turn 2"
        sources2 = sources_event2["data"].get("sources", [])
        print(f"Turn 2 Retrieved Sources: {len(sources2)} chunks")
        assert len(sources2) > 0, "Ship 30 skill should retrieve relevant chunks using resolved topic"
        
        tokens2 = [e["data"].get("content", "") for e in events2 if e["event"] == "token"]
        ship30_essay = "".join(tokens2)
        word_count = len(ship30_essay.split())
        print(f"\nShip 30 Essay Generated! Word count: {word_count} words")
        print("--------------------------------------------------")
        print(ship30_essay[:1200] + "\n...[truncated for display]...\n" + ship30_essay[-400:])
        print("--------------------------------------------------")
        
        # Verify Essay Quality & Format
        assert word_count >= 500, f"Essay is too short ({word_count} words)"
        assert "# " in ship30_essay or "## " in ship30_essay, "Essay must contain Markdown headings"
        assert "Elena Verna" in ship30_essay or "product-led" in ship30_essay.lower() or "sales" in ship30_essay.lower(), "Essay must be grounded in Elena Verna's PLS insights"
        
        # Verify Turn 2 DB persistence
        session_detail2 = (await client.get(f"/api/sessions/{session_id}")).json()
        assert len(session_detail2["messages"]) == 4, f"Expected 4 messages, got {len(session_detail2['messages'])}"
        ship30_msg = session_detail2["messages"][3]
        assert ship30_msg["role"] == "assistant"
        assert len(ship30_msg["sources"]) > 0, "Ship 30 message must persist sources"
        print(f"Turn 2 Persisted Successfully with {len(ship30_msg['sources'])} sources.")
        
        # ----------------------------------------------------
        # 4. Refusal Test on Insufficient Evidence
        # ----------------------------------------------------
        print("\n--- 4. Turn 3: Refusal Test on Out-of-Domain Ship 30 Request ---")
        resp_b = await client.post("/api/sessions", json={"title": "Refusal Session"})
        session_b_id = resp_b.json()["id"]
        
        q_refusal = "Write a Ship 30 for 30 essay about quantum computing qubits in superconducting circuits."
        print(f"User: '{q_refusal}'")
        
        payload_refusal = {
            "session_id": session_b_id,
            "message": q_refusal,
            "provider": "ollama",
            "skill": "auto"
        }
        
        async with client.stream("POST", "/api/chat", json=payload_refusal) as stream_resp:
            assert stream_resp.status_code == 200
            events_refusal = await parse_sse_stream(stream_resp)
            
        start_refusal = next((e for e in events_refusal if e["event"] == "start"), None)
        assert start_refusal["data"].get("skill") == "ship30", "Out-of-domain request should still route to ship30"
        
        tokens_refusal = [e["data"].get("content", "") for e in events_refusal if e["event"] == "token"]
        refusal_response = "".join(tokens_refusal)
        print(f"Refusal Response: '{refusal_response.strip()}'")
        
        assert "sufficient information" in refusal_response.lower(), "Expected grounded refusal phrase on insufficient evidence"
        print("Success: Ship 30 Skill correctly refused out-of-domain request without hallucinating!")
        
        print("\n==================================================")
        print("ALL REAL OLLAMA SHIP 30 INTEGRATION CHECKS PASSED!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
