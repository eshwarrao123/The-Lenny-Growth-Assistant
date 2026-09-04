import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.rag.parser import TranscriptParser
from app.rag.chunker import TranscriptChunker
from app.rag.embeddings import OllamaEmbeddings
from app.rag.repository import IngestionRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def process_episode(
    file_path: Path, 
    parser: TranscriptParser, 
    chunker: TranscriptChunker, 
    embedder: OllamaEmbeddings, 
    repo: IngestionRepository, 
    refresh: bool
) -> dict:
    source_id = file_path.parent.name
    
    # Idempotency check
    existing_ep = await repo.get_episode_by_source_id(source_id)
    if existing_ep:
        if not refresh:
            logger.info(f"Skipping {source_id}: already exists. Use --refresh to rebuild.")
            return {"status": "skipped"}
        else:
            logger.info(f"Rebuilding {source_id}: deleting existing records.")
            await repo.delete_episode_by_source_id(source_id)
            
    # Parse
    metadata, paragraphs = parser.parse_file(file_path)
    if not paragraphs:
        logger.warning(f"No paragraphs found for {source_id}")
        return {"status": "failed", "reason": "No paragraphs"}
        
    # Chunk
    chunks = chunker.chunk_paragraphs(paragraphs)
    if not chunks:
        logger.warning(f"No chunks generated for {source_id}")
        return {"status": "failed", "reason": "No chunks"}
        
    # Embed
    texts_to_embed = [c["text"] for c in chunks]
    try:
        embeddings = await embedder.embed_batch(texts_to_embed)
    except Exception as e:
        logger.error(f"Failed to generate embeddings for {source_id}: {e}")
        return {"status": "failed", "reason": "Embedding failed"}
        
    # Save
    ep = await repo.insert_episode(source_id, metadata)
    inserted = await repo.insert_chunks(ep.id, chunks, embeddings)
    
    return {"status": "success", "chunks": inserted}

async def run_ingestion(data_dir: str, refresh: bool):
    settings = get_settings()
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.error(f"Data directory {data_path} does not exist.")
        sys.exit(1)
        
    parser = TranscriptParser()
    chunker = TranscriptChunker(
        chunk_size=settings.rag_chunk_size, 
        chunk_overlap=settings.rag_chunk_overlap
    )
    embedder = OllamaEmbeddings()
    
    # Validate Ollama
    is_healthy = await embedder.health_check()
    if not is_healthy:
        logger.error("Ollama health check failed. Ingestion aborted.")
        sys.exit(1)
        
    # Discover files
    transcript_files = list(data_path.glob("episodes/*/transcript.md"))
    logger.info(f"Found {len(transcript_files)} transcript files.")
    
    stats = {
        "discovered": len(transcript_files),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "chunks_inserted": 0
    }
    
    async with async_session_maker() as session:
        repo = IngestionRepository(session)
        
        for idx, file_path in enumerate(transcript_files, 1):
            logger.info(f"Processing [{idx}/{len(transcript_files)}]: {file_path.parent.name}")
            result = await process_episode(file_path, parser, chunker, embedder, repo, refresh)
            
            if result["status"] == "success":
                stats["processed"] += 1
                stats["chunks_inserted"] += result["chunks"]
            elif result["status"] == "skipped":
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
                
    logger.info("====================================")
    logger.info("INGESTION COMPLETE")
    logger.info("====================================")
    logger.info(f"Files Discovered: {stats['discovered']}")
    logger.info(f"Episodes Processed: {stats['processed']}")
    logger.info(f"Episodes Skipped:   {stats['skipped']}")
    logger.info(f"Episodes Failed:    {stats['failed']}")
    logger.info(f"Chunks Inserted:    {stats['chunks_inserted']}")

def main():
    parser = argparse.ArgumentParser(description="Ingest transcripts into PostgreSQL.")
    parser.add_argument("--data-dir", type=str, default=str(Path(__file__).parent.parent / "data" / "transcripts"), help="Path to cloned repository.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild all existing episodes.")
    args = parser.parse_args()
    
    asyncio.run(run_ingestion(args.data_dir, args.refresh))

if __name__ == "__main__":
    main()
