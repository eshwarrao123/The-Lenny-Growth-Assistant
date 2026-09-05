import asyncio
import asyncpg
from app.core.config import get_settings

async def verify():
    settings = get_settings()
    host = settings.postgres_host
    user = settings.postgres_user
    password = settings.postgres_password
    db = settings.postgres_db
    port = settings.postgres_port
    
    conn = await asyncpg.connect(f"postgresql://{user}:{password}@{host}:{port}/{db}")
    
    # 1. Extension check
    ext = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    print('[+] pgvector extension:', ext)
    
    # 2. Tables check
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    table_names = [t['table_name'] for t in tables]
    print('[+] Public tables:', table_names)
    
    # 3. Column dimension check
    dim_info = await conn.fetchrow("""
        SELECT a.attname, format_type(a.atttypid, a.atttypmod) as type_name
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        WHERE c.relname = 'transcript_chunks' AND a.attname = 'embedding';
    """)
    print('[+] Column type:', dim_info['type_name'])
    
    # 4. HNSW Index check
    indexes = await conn.fetch("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='transcript_chunks'")
    hnsw = [i for i in indexes if 'hnsw' in i['indexdef'].lower()]
    print('[+] HNSW index count:', len(hnsw))
    for i in hnsw:
        print('    -', i['indexname'], ':', i['indexdef'])
        
    # 5. Cosine distance query usability check
    dummy_vec = '[' + ','.join(['0.01']*768) + ']'
    res = await conn.fetch(f"SELECT id FROM transcript_chunks ORDER BY embedding <=> '{dummy_vec}' LIMIT 1;")
    print('[+] Cosine query executed successfully! Returned rows:', len(res))
    await conn.close()

if __name__ == '__main__':
    asyncio.run(verify())
