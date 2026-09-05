import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.repository import IngestionRepository
from app.rag.embeddings import OllamaEmbeddings
from app.schemas.rag_schemas import RetrievalResult
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class TranscriptRetriever:
    """
    Service responsible for retrieving relevant transcript chunks for a given query.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = IngestionRepository(session)
        self.embeddings = OllamaEmbeddings()
        self.settings = get_settings()

    async def retrieve(self, query: str, top_k: int = None, threshold: float = None) -> List[RetrievalResult]:
        """
        Embeds the query and fetches similar chunks from the database.
        """
        if top_k is None:
            top_k = self.settings.rag_top_k
        if threshold is None:
            threshold = self.settings.rag_similarity_threshold

        logger.info(f"Retrieving for query: '{query}' (top_k={top_k}, threshold={threshold})")
        
        # 1. Embed query
        query_vectors = await self.embeddings.embed_batch([query])
        if not query_vectors:
            logger.warning("Failed to generate embeddings for query.")
            return []
            
        query_vector = query_vectors[0]
        
        # 2. Query pgvector
        raw_results = await self.repository.search_similar_chunks(query_vector=query_vector, top_k=top_k)
        
        # 3. Filter by threshold and map to schema
        results: List[RetrievalResult] = []
        for result in raw_results:
            chunk = result["chunk"]
            episode = result["episode"]
            similarity_score = result["similarity_score"]
            
            if similarity_score >= threshold:
                results.append(
                    RetrievalResult(
                        chunk_id=chunk.id,
                        episode_id=episode.id,
                        episode_title=episode.title or "Unknown Title",
                        guest_name=episode.guest_name or "Unknown Guest",
                        source_path=episode.source_id,
                        transcript_text=chunk.text,
                        similarity_score=similarity_score,
                        speaker=chunk.speaker,
                        start_timestamp=chunk.start_time,
                        end_timestamp=None # End timestamp not tracked natively yet
                    )
                )
                
        logger.info(f"Retrieved {len(results)} chunks above threshold.")
        return results
