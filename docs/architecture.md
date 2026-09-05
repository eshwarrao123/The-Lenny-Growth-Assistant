# The Lenny Growth Assistant - Architecture Document

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │
│  │   Chat Pane     │  │      Artifact Viewer Pane           │  │
│  │  - Messages     │  │  - Iframe sandbox                   │  │
│  │  - Streaming    │  │  - Version tabs                     │  │
│  │  - Input        │  │  - Copy/Download                    │  │
│  └────────┬────────┘  └──────────────────┬──────────────────┘  │
│           │                                │                    │
│           └────────────────┬───────────────┘                    │
│                            ▼                                    │
│                    ┌─────────────┐                              │
│                    │  API Client │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼────────────────────────────────────┘
                            │ HTTP (SSE & REST)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Chat API    │ │  RAG Service │ │ Skill Router │             │
│  │  - Sessions  │ │  - Retrieval │ │  - Ship 30   │             │
│  │  - Messages  │ │  - Embedding │ │  - Artifact  │             │
│  │  - Streaming │ │  - pgvector  │ │  - Extensible│             │
│  └──────────────┘ └──────┬───────┘ └──────────────┘             │
│                           │                                      │
│              ┌────────────┼────────────┐                         │
│              ▼            ▼            ▼                         │
│       ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│       │ Provider │ │ Provider │ │ Provider │                    │
│       │  Ollama  │ │  OpenAI  │ │Anthropic │                    │
│       └──────────┘ └──────────┘ └──────────┘                    │
└───────────────────────────┼────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────────┐            ┌──────────────┐
       │  PostgreSQL  │            │    Ollama    │
       │  + pgvector  │            │  (on host)   │
       └──────────────┘            └──────────────┘
```

## 2. Database Schema

The database relies on PostgreSQL with the `pgvector` extension and UUID primary keys.

```sql
-- Episodes table (maps 1:1 with transcript files)
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id VARCHAR(255) UNIQUE, -- e.g., 'ada-chen-rekhi'
    title VARCHAR(500),
    guest_name VARCHAR(255),
    publish_date DATE,
    youtube_url VARCHAR(500),
    video_id VARCHAR(50),
    duration_seconds INTEGER,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcript Chunks (for RAG retrieval)
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    text TEXT,
    token_count INTEGER,
    speaker VARCHAR(255),
    start_time VARCHAR(50),
    embedding VECTOR(768),  -- using nomic-embed-text dimensionality
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW Index for fast cosine similarity search
CREATE INDEX idx_chunks_embedding ON transcript_chunks USING hnsw (embedding vector_cosine_ops);

-- Chat sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50),  -- user, assistant, system
    content TEXT,
    sources JSONB DEFAULT '[]',  -- array of citation references
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Artifacts
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    type VARCHAR(50),  -- html, markdown
    title VARCHAR(255),
    content TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Essential Indexes
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
```

## 3. Embedding & Retrieval Strategy

### 3.1 pgvector & Embeddings
* **Model**: Local Ollama `nomic-embed-text` (768 dimensions). It balances speed, local independence, and reasonable retrieval accuracy.
* **Index**: HNSW (Hierarchical Navigable Small World). Chosen over IVFFLAT for improved recall and zero-training requirement prior to insertions.
* **Operator**: `vector_cosine_ops` (Cosine distance).

### 3.2 Chunking Strategy
* **Method**: Sliding-window semantic chunker.
* **Target Size**: ~500 tokens with ~100 token overlap.
* **Metadata Tracking**: The parsing logic retains the `speaker` (e.g., `Ada Chen Rekhi (00:00:00):`) and `start_time` mapping for the dominant speaker within each chunk to support detailed citations.

### 3.3 Retrieval Contract
**Input:** `retrieve(query: str, top_k: int = 5, threshold: float = 0.65)`
**Output:** Array of `RetrievalResult` objects:
```json
{
  "chunk_id": "uuid",
  "episode_id": "uuid",
  "episode_title": "...",
  "guest_name": "...",
  "text": "transcript snippet...",
  "score": 0.82,
  "speaker": "Ada Chen Rekhi",
  "start_time": "00:01:21"
}
```

## 4. LLM Provider Abstraction

### 4.1 Interface Contract
All model interactions pass through the `BaseLLMProvider` interface to decouple business logic from API specifics:
- `generate_stream(messages: List[dict], **kwargs) -> AsyncGenerator[dict, None]`
- `generate_embeddings(texts: List[str]) -> List[List[float]]`
- `health_check() -> bool`

### 4.2 Supported Providers
1. **Ollama (Primary / Local)**: Default execution path for zero-cost, offline deployment (model: `qwen2.5:7b`).
2. **OpenAI (Cloud)**: Scalable cloud alternative for deeper reasoning (model: `gpt-4o-mini`).

## 5. SSE Streaming Contract

Server-Sent Events (SSE) stream highly structured JSON payloads to the frontend.

| Event Type | Payload Schema | Description |
|---|---|---|
| `status` | `{"message": str}` | UI loading states (e.g., "Retrieving context...") |
| `sources` | `[{"guest": str, "title": str, "text": str}]` | The retrieved context used to ground the upcoming response |
| `token` | `{"content": str}` | LLM string token for standard message stream |
| `artifact_start` | `{"type": str, "id": str, "title": str}` | Triggers Artifact Viewer to open (type: `html` or `markdown`) |
| `artifact_chunk` | `{"content": str}` | Streams code blocks bypassing the main chat window |
| `artifact_done` | `{"id": str}` | Signals completion of artifact generation |
| `error` | `{"message": str}` | Halts stream and renders error in UI |
| `done` | `{}` | Graceful termination of request |

## 6. API Contracts

### 6.1 Sessions & Chat
* `POST /api/sessions`: Returns `{ "id": "uuid", "title": "New Chat" }`
* `GET /api/sessions/{session_id}`: Returns full hydrated history `{ "session": {...}, "messages": [...], "artifacts": [...] }`
* `POST /api/chat`: Expects `{ "session_id": "uuid", "message": "str", "provider": "ollama|openai" }`. Returns `Content-Type: text/event-stream`.

### 6.2 Health & Observability
* `GET /api/health`: Returns detailed dependency status `{ "status": "ok", "db": "ok", "ollama": "ok" }`. 

## 7. Security Boundaries

* **User Input**: Sanitized and parameterized via SQLAlchemy.
* **Transcripts**: Evaluated as untrusted `<context>` chunks to prevent prompt injection overriding core agent instructions.
* **HTML Artifacts**: Strictly sandboxed on the client-side via `<iframe sandbox="allow-scripts allow-forms">` (explicitly missing `allow-same-origin`) to ensure zero access to parent DOM/cookies.
* **Secrets**: Managed purely server-side via `.env` (Pydantic `BaseSettings`).

## 8. Docker Topology

* `postgres`: Official `pgvector/pgvector:pg16` image on port `5432`.
* `backend`: FastAPI Python container. Connects to `postgres:5432` and host Ollama via `host.docker.internal:11434`.
* `frontend`: Next.js Node container on port `3000`.
* **Host OS**: Ollama runs directly on the host to avoid GPU passthrough complexities.

## 9. Knowledge Base Ingestion Pipeline
* **Source**: `https://github.com/ChatPRD/lennys-podcast-transcripts` (303 episode transcripts).
* **Parser**: Custom regex-based parser mapping `Speaker (Timestamp):` to semantic blocks. Robust against missing YAML frontmatter keys (e.g. missing publish_date/youtube_url in raw files like `daniel-lereya`).
* **Chunker**: Token-aware sliding-window chunking. 500 max limit, 100 overlap. Hard splits large paragraphs deterministically.
* **Embeddings**: Native Ollama `/api/embed` batching endpoint with `nomic-embed-text` (768 dimensions), split into sub-batches of 120 items and run with configurable concurrency (default `--concurrency 8`).
* **SQLAlchemy & pgvector**: Implements native SQLAlchemy `Vector(768)` type from `pgvector.sqlalchemy` for type-safe schema binding and migration safety.
* **Idempotency**: Transcript folder names act as `source_id`. `ingest.py` checks existing source IDs and skips duplicate processing or rebuilds cleanly when `--refresh` is supplied.

## 10. Testing Architecture
* **Backend Unit**: Pytest for Pydantic schema validation, sliding-window chunking logic, and mocked provider interfaces.
* **Integration**: Testing pgvector HNSW insert/retrieve flows.
* **E2E Browser**: Playwright tests to validate Artifact Viewer sandboxing (XSS attempts) and provider toggling.

## 11. Decisions Intentionally Deferred (Phase 4+)
- Hybrid search (BM25 + Dense) implementation.
- Real-time cloud audio ingestion.
- Multi-user authentication (RBAC).