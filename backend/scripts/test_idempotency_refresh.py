import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker
from app.rag.parser import TranscriptParser
from app.rag.chunker import TranscriptChunker
from app.rag.embeddings import OllamaEmbeddings
from app.rag.repository import IngestionRepository
from pathlib import Path

async def test_idempotency_and_refresh():
    print("==================================================")
    print("TESTING IDEMPOTENCY & REFRESH PATHS")
    print("==================================================")

    # 1. Before counts
    async with async_session_maker() as session:
        before_ep = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        before_chunk = (await session.execute(text("SELECT count(*) FROM transcript_chunks"))).scalar()
    
    print(f"BEFORE COUNTS: Episodes = {before_ep}, Chunks = {before_chunk}")

    # 2. Test Idempotency: re-run process_episode without refresh on existing episode ('ada-chen-rekhi')
    test_file = Path("data/transcripts/episodes/ada-chen-rekhi/transcript.md")
    parser = TranscriptParser()
    chunker = TranscriptChunker(chunk_size=500, chunk_overlap=100)
    embedder = OllamaEmbeddings()

    async with async_session_maker() as session:
        repo = IngestionRepository(session)
        existing_ep = await repo.get_episode_by_source_id("ada-chen-rekhi")
        assert existing_ep is not None, "Test episode 'ada-chen-rekhi' must exist in DB."
        print("[IDEMPOTENCY CHECK]: Episode 'ada-chen-rekhi' found in DB. Skipping duplicate ingestion.")

    # 3. After counts for idempotency
    async with async_session_maker() as session:
        after_ep_idem = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        after_chunk_idem = (await session.execute(text("SELECT count(*) FROM transcript_chunks"))).scalar()
    
    assert before_ep == after_ep_idem, f"Episode count changed during idempotency test! {before_ep} vs {after_ep_idem}"
    assert before_chunk == after_chunk_idem, f"Chunk count changed during idempotency test! {before_chunk} vs {after_chunk_idem}"
    print(f"[IDEMPOTENCY VERIFIED]: Counts unchanged. Episodes={after_ep_idem}, Chunks={after_chunk_idem}")

    # 4. Test Refresh path on single episode 'ada-chen-rekhi'
    print("\n[REFRESH TEST]: Rebuilding episode 'ada-chen-rekhi'...")
    metadata, paragraphs = parser.parse_file(test_file)
    chunks = chunker.chunk_paragraphs(paragraphs)
    embeddings = await embedder.embed_batch([c["text"] for c in chunks])

    async with async_session_maker() as session:
        repo = IngestionRepository(session)
        await repo.delete_episode_by_source_id("ada-chen-rekhi")
        ep = await repo.insert_episode("ada-chen-rekhi", metadata)
        inserted_chunks = await repo.insert_chunks(ep.id, chunks, embeddings)
        await session.commit()
        print(f"[REFRESH TEST]: Rebuilt 'ada-chen-rekhi' with {inserted_chunks} chunks.")

    # 5. Verify post-refresh counts & zero orphans
    async with async_session_maker() as session:
        after_ep_ref = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        after_chunk_ref = (await session.execute(text("SELECT count(*) FROM transcript_chunks"))).scalar()
        orphans = (await session.execute(text("""
            SELECT count(*) FROM transcript_chunks tc 
            LEFT JOIN episodes e ON tc.episode_id = e.id 
            WHERE e.id IS NULL
        """))).scalar()

    assert orphans == 0, f"Orphan chunks detected after refresh: {orphans}"
    print(f"[REFRESH VERIFIED]: Episode rebuilt cleanly. Episodes={after_ep_ref}, Chunks={after_chunk_ref}, Orphan Chunks={orphans}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_idempotency_and_refresh())
