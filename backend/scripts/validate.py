import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text
from app.core.database import async_session_maker
from app.models import Episode, TranscriptChunk
from app.rag.embeddings import OllamaEmbeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_validation():
    logger.info("Starting Knowledge Base Validation...")
    
    async with async_session_maker() as session:
        # 1. Episode Count
        ep_count = await session.scalar(select(func.count(Episode.id)))
        logger.info(f"Total Episodes Ingested: {ep_count}")
        
        # 2. Chunk Count
        chunk_count = await session.scalar(select(func.count(TranscriptChunk.id)))
        logger.info(f"Total Chunks Generated: {chunk_count}")
        
        if ep_count == 0:
            logger.warning("Database is empty. Did you run the ingestion script?")
            return
            
        logger.info(f"Average chunks per episode: {chunk_count / ep_count:.1f}")
        
        # 3. Embedding Dimension check
        first_chunk = await session.scalar(select(TranscriptChunk).limit(1))
        if first_chunk and first_chunk.embedding:
            dim = len(first_chunk.embedding)
            logger.info(f"Verified embedding dimension: {dim}")
            if dim != 768:
                logger.error(f"FAIL: Expected dimension 768, got {dim}")
        else:
            logger.error("FAIL: No embeddings found in chunks.")
            
        # 4. HNSW Index Check
        try:
            # Generate a random test embedding using Ollama to run a real pgvector cosine distance query
            embedder = OllamaEmbeddings()
            is_healthy = await embedder.health_check()
            if not is_healthy:
                logger.error("Ollama not healthy. Cannot perform similarity check.")
            else:
                test_embed = await embedder.embed_batch(["growth and retention strategies"])
                vec = test_embed[0]
                
                logger.info("Executing pgvector cosine similarity test query...")
                
                stmt = (
                    select(
                        Episode.title,
                        TranscriptChunk.text,
                        TranscriptChunk.speaker,
                        TranscriptChunk.start_time,
                        TranscriptChunk.embedding.cosine_distance(vec).label("distance")
                    )
                    .join(Episode)
                    .order_by(TranscriptChunk.embedding.cosine_distance(vec))
                    .limit(1)
                )
                result = await session.execute(stmt)
                row = result.first()
                if row:
                    logger.info("SUCCESS: pgvector HNSW retrieval is functioning.")
                    logger.info(f"Best Match Episode: {row.title}")
                    logger.info(f"Speaker: {row.speaker} @ {row.start_time}")
                    logger.info(f"Distance: {row.distance:.4f}")
                else:
                    logger.error("FAIL: Query returned no results.")
        except Exception as e:
            logger.error(f"FAIL: Vector query failed: {e}")
            
    logger.info("Validation complete.")

if __name__ == "__main__":
    asyncio.run(run_validation())
