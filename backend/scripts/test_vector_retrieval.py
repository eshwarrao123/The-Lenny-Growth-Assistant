import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker
from app.rag.embeddings import OllamaEmbeddings
from app.rag.repository import IngestionRepository

async def test_retrieval(query: str, top_k: int = 3):
    embedder = OllamaEmbeddings()
    print(f"\n[QUERY]: '{query}'")
    
    # Generate query embedding
    embeddings = await embedder.embed_batch([query])
    query_vector = embeddings[0]
    print(f"Query Embedding Generated: Dimension = {len(query_vector)}")

    async with async_session_maker() as session:
        repo = IngestionRepository(session)
        results = await repo.search_similar_chunks(query_vector, top_k=top_k)
        
        print(f"\n--- TOP {len(results)} RETRIEVAL RESULTS ---")
        for idx, item in enumerate(results, 1):
            score = item["similarity_score"]
            chunk = item["chunk"]
            ep = item["episode"]
            
            print(f"\nResult #{idx} (Similarity Score: {score:.4f}):")
            print(f"  Chunk ID:        {chunk.id}")
            print(f"  Episode Title:   {ep.title}")
            print(f"  Guest Name:      {ep.guest_name}")
            print(f"  Speaker:         {chunk.speaker or 'N/A'}")
            print(f"  Start Time:      {chunk.start_time or 'N/A'}")
            print(f"  Snippet:         {chunk.text[:200]}...")

async def main():
    queries = [
        "How do you measure product-market fit?",
        "What are the best frameworks for activation and onboarding growth?",
        "How to handle pricing and subscription retention?"
    ]
    for q in queries:
        await test_retrieval(q)

if __name__ == "__main__":
    asyncio.run(main())
