import asyncio
import json
from app.core.database import async_session_maker
from app.rag.retriever import TranscriptRetriever

async def test_retrieval():
    queries = [
        "What does Elena Verna say about product-led sales?",
        "How do you improve product retention?"
    ]
    
    async with async_session_maker() as session:
        retriever = TranscriptRetriever(session)
        
        for q in queries:
            print("=" * 60)
            print(f"QUERY: {q}")
            print("=" * 60)
            results = await retriever.retrieve(query=q, top_k=5, threshold=0.4)
            print(f"Total results retrieved: {len(results)}")
            for idx, r in enumerate(results, 1):
                print(f"\n--- Result #{idx} ---")
                print(f"Episode: {r.episode_title}")
                print(f"Guest: {r.guest_name}")
                print(f"Speaker: {r.speaker}")
                print(f"Start Timestamp: {r.start_timestamp}")
                print(f"Chunk ID: {r.chunk_id}")
                print(f"Similarity Score: {r.similarity_score:.4f}")
                print(f"Text Snippet: {r.transcript_text[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
