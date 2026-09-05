import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models import Episode, TranscriptChunk

logger = logging.getLogger(__name__)

class IngestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_episode_by_source_id(self, source_id: str) -> Optional[Episode]:
        stmt = select(Episode).where(Episode.source_id == source_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_episode_by_source_id(self, source_id: str) -> bool:
        """
        Deletes the episode and cascades to chunks.
        Returns True if something was deleted.
        """
        ep = await self.get_episode_by_source_id(source_id)
        if ep:
            await self.session.delete(ep)
            await self.session.commit()
            return True
        return False

    async def insert_episode(self, source_id: str, metadata: Dict[str, Any]) -> Episode:
        ep = Episode(
            source_id=source_id,
            title=metadata.get("title"),
            guest_name=metadata.get("guest"),
            publish_date=metadata.get("publish_date"),
            youtube_url=metadata.get("youtube_url"),
            video_id=metadata.get("video_id"),
            duration_seconds=metadata.get("duration_seconds"),
            description=metadata.get("description"),
            metadata_={k: v for k, v in metadata.items() if k in ["keywords", "channel", "view_count", "duration"]}
        )
        self.session.add(ep)
        await self.session.commit()
        await self.session.refresh(ep)
        return ep

    async def insert_chunks(self, episode_id: str, chunks_data: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Inserts chunks rapidly using bulk operations if needed, but simple add_all is fine for chunks of a single episode.
        """
        db_chunks = []
        for c, emb in zip(chunks_data, embeddings):
            chunk = TranscriptChunk(
                episode_id=episode_id,
                chunk_index=c["chunk_index"],
                text=c["text"],
                token_count=c["token_count"],
                speaker=c["speaker"],
                start_time=c["start_time"],
                embedding=emb,
                metadata_={}
            )
            db_chunks.append(chunk)
            
        self.session.add_all(db_chunks)
        await self.session.commit()
        return len(db_chunks)

    async def search_similar_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a vector cosine distance search against stored transcript chunks using pgvector.
        Returns top-K matching chunks with episode metadata and similarity score.
        """
        from sqlalchemy import text
        stmt = (
            select(
                TranscriptChunk,
                Episode,
                TranscriptChunk.embedding.cosine_distance(query_vector).label("distance")
            )
            .join(Episode, TranscriptChunk.episode_id == Episode.id)
            .order_by(text("distance ASC"))
            .limit(top_k)
        )
        result = await self.session.execute(stmt)
        results = []
        for chunk, episode, distance in result.all():
            similarity_score = 1.0 - float(distance) if distance is not None else 0.0
            results.append({
                "chunk": chunk,
                "episode": episode,
                "distance": distance,
                "similarity_score": similarity_score
            })
        return results
