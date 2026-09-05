import asyncio
import numpy as np
from sqlalchemy import text
from app.core.database import async_session_maker

async def verify_stored_data():
    async with async_session_maker() as session:
        print("==================================================")
        print("LIVE DATABASE & STORED DATA VERIFICATION REPORT")
        print("==================================================")

        # 1. Episode Count
        ep_count = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        print(f"1. Episode Count: {ep_count}")

        # 2. Chunk Count
        chunk_count = (await session.execute(text("SELECT count(*) FROM transcript_chunks"))).scalar()
        print(f"2. Chunk Count: {chunk_count}")

        # 3. Embedding Count
        emb_count = (await session.execute(text("SELECT count(*) FROM transcript_chunks WHERE embedding IS NOT NULL"))).scalar()
        print(f"3. Embedding Count: {emb_count}")

        # 4. Chunks per Episode Statistics
        res = await session.execute(text("""
            SELECT episode_id, count(*) as c 
            from transcript_chunks 
            group by episode_id
        """))
        chunk_counts = [row[1] for row in res.fetchall()]
        if chunk_counts:
            min_c = min(chunk_counts)
            max_c = max(chunk_counts)
            avg_c = np.mean(chunk_counts)
            std_c = np.std(chunk_counts)
            median_c = np.median(chunk_counts)
            print(f"4. Chunks per Episode Stats: Min={min_c}, Max={max_c}, Avg={avg_c:.2f}, Median={median_c:.1f}, Std={std_c:.2f}")
        else:
            print("4. Chunks per Episode Stats: N/A")

        # 5. Metadata Completeness
        meta_res = await session.execute(text("""
            SELECT 
                count(*) FILTER (WHERE title IS NULL OR title = '') as missing_title,
                count(*) FILTER (WHERE guest_name IS NULL OR guest_name = '') as missing_guest,
                count(*) FILTER (WHERE publish_date IS NULL) as missing_date,
                count(*) FILTER (WHERE youtube_url IS NULL OR youtube_url = '') as missing_url,
                count(*) FILTER (WHERE video_id IS NULL OR video_id = '') as missing_videoid
            FROM episodes
        """))
        missing_m = meta_res.fetchone()
        print(f"5. Metadata Completeness: Missing Title={missing_m[0]}, Missing Guest={missing_m[1]}, Missing Date={missing_m[2]}, Missing URL={missing_m[3]}, Missing VideoID={missing_m[4]}")

        # 6. Embedding Dimension Validation
        dim_res = await session.execute(text("""
            SELECT vector_dims(embedding) as dim, count(*) 
            FROM transcript_chunks 
            GROUP BY vector_dims(embedding)
        """))
        dims = dim_res.fetchall()
        print(f"6. Embedding Dimensions Distribution: {dict(dims)}")

        # 7. Duplicate Episode Identities
        dup_res = await session.execute(text("""
            SELECT source_id, count(*) 
            FROM episodes 
            GROUP BY source_id 
            HAVING count(*) > 1
        """))
        dups = dup_res.fetchall()
        print(f"7. Duplicate Episode Source IDs: {len(dups)}")

        # 8. Chunks with Missing Citation Metadata
        cit_res = await session.execute(text("""
            SELECT count(*) 
            FROM transcript_chunks 
            WHERE episode_id IS NULL OR chunk_index IS NULL OR text IS NULL OR text = ''
        """))
        missing_cit = cit_res.scalar()
        print(f"8. Chunks with Missing Citation Metadata: {missing_cit}")

        # 9. Referential Integrity Check
        orphan_res = await session.execute(text("""
            SELECT count(*) 
            FROM transcript_chunks tc 
            LEFT JOIN episodes e ON tc.episode_id = e.id 
            WHERE e.id IS NULL
        """))
        orphans = orphan_res.scalar()
        print(f"9. Orphan Chunks (FK Violation): {orphans}")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(verify_stored_data())
