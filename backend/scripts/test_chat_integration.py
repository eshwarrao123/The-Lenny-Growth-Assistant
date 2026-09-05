import asyncio
import httpx
from httpx import ASGITransport
from app.main import app

async def run_integration_test():
    print("Starting Integration Test...")
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Create a session
        print("\n--- 1. Creating Session ---")
        response = await client.post("/api/sessions")
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["id"]
        print(f"Session Created: {session_id}")
        
        # 2. Ask a real Lenny-related question
        print("\n--- 2. Asking Lenny-related question ---")
        payload = {
            "session_id": session_id,
            "message": "What does Elena Verna say about product-led sales?",
            "provider": "ollama"
        }
        
        async with client.stream("POST", "/api/chat", json=payload) as stream_resp:
            assert stream_resp.status_code == 200
            async for line in stream_resp.aiter_lines():
                if line:
                    print(line)
        
        # 3. Verify session persisted correctly
        print("\n--- 3. Verifying Persistence ---")
        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        messages = data.get("messages", [])
        assert len(messages) == 2 # 1 user, 1 assistant
        user_msg = messages[0]
        assistant_msg = messages[1]
        
        assert user_msg["role"] == "user"
        assert assistant_msg["role"] == "assistant"
        
        sources = assistant_msg.get("sources", [])
        print(f"Number of sources persisted: {len(sources)}")
        if sources:
            print("Sources found! Grounding successful.")
        else:
            print("Warning: No sources found. Ensure DB has transcripts ingested.")
            
        # 4. Ask a follow-up question
        print("\n--- 4. Asking Follow-up question ---")
        payload2 = {
            "session_id": session_id,
            "message": "Can you summarize that in one sentence?",
            "provider": "ollama"
        }
        async with client.stream("POST", "/api/chat", json=payload2) as stream_resp:
            assert stream_resp.status_code == 200
            async for line in stream_resp.aiter_lines():
                if line:
                    print(line)
                    
        # 5. Out-of-domain question
        print("\n--- 5. Asking Out-of-domain question ---")
        payload3 = {
            "session_id": session_id,
            "message": "What is the capital of France?",
            "provider": "ollama"
        }
        refusal_found = False
        async with client.stream("POST", "/api/chat", json=payload3) as stream_resp:
            assert stream_resp.status_code == 200
            async for line in stream_resp.aiter_lines():
                if line:
                    print(line)
                    if "sufficient information" in line:
                        refusal_found = True
                        
        if refusal_found:
            print("\nSuccess: Out-of-domain question was correctly refused.")
        else:
            print("\nWarning: Out-of-domain refusal phrase not found.")

        # 6. Session Isolation Test
        print("\n--- 6. Testing Session Isolation ---")
        resp_b = await client.post("/api/sessions")
        assert resp_b.status_code == 200
        session_b_id = resp_b.json()["id"]
        print(f"Session B Created: {session_b_id}")
        
        detail_b = (await client.get(f"/api/sessions/{session_b_id}")).json()
        assert len(detail_b.get("messages", [])) == 0
        print("Session B verified empty (isolated from Session A).")

        # 7. Invalid Provider Routing Test
        print("\n--- 7. Testing Invalid Provider Routing ---")
        payload_inv = {
            "session_id": session_id,
            "message": "Hello",
            "provider": "invalid_provider"
        }
        response_inv = await client.post("/api/chat", json=payload_inv)
        assert response_inv.status_code == 422
        print("Success: Invalid provider correctly rejected with HTTP 422 validation error.")

        print("\nIntegration test completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
