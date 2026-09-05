import asyncio
from app.core.database import async_session_maker
from sqlalchemy import text

async def main():
    async with async_session_maker() as session:
        ep_count = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        chunk_count = (await session.execute(text("SELECT count(*) FROM transcript_chunks"))).scalar()
        emb_count = (await session.execute(text("SELECT count(*) FROM transcript_chunks WHERE embedding IS NOT NULL"))).scalar()
        print(f"EPISODES: {ep_count}")
        print(f"CHUNKS: {chunk_count}")
        print(f"EMBEDDINGS: {emb_count}")

if __name__ == "__main__":
    asyncio.run(main())
