# The Lenny Growth Assistant - Architecture Document

## High-Level Architecture

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
                            │ HTTP/WS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Chat API    │ │  RAG Service │ │ Skill Router │             │
│  │  - Sessions  │ │  - Retrieval │ │  - Ship 30   │             │
│  │  - Messages  │ │  - Embedding │ │  - Artifact  │             │
│  │  - Streaming │ │  - Rerank    │ │  - Extensible│             │
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

## Component Details

### Backend Services

#### 1. Chat Service (`backend/app/services/chat.py`)
- Session CRUD operations
- Message persistence
- Streaming response handling
- WebSocket connection management

#### 2. RAG Service (`backend/app/services/rag.py`)
- Transcript chunking strategy
- Embedding generation
- Vector similarity search
- Source attribution

#### 3. Skill Router (`backend/app/services/skills/`)
- Base skill interface
- Ship 30 for 30 implementation
- Artifact generation skill
- Skill registry and dispatch

#### 4. Provider Abstraction (`backend/app/providers/`)
- `BaseLLMProvider` interface
- `OllamaProvider` implementation
- `OpenAIProvider` implementation
- `AnthropicProvider` implementation
- Factory for provider selection

### Database Schema

```sql
-- Episodes table
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest VARCHAR(255),
    title VARCHAR(500),
    youtube_url VARCHAR(500),
    video_id VARCHAR(50),
    publish_date DATE,
    description TEXT,
    duration_seconds INTEGER,
    duration VARCHAR(50),
    view_count BIGINT,
    channel VARCHAR(255),
    transcript_content TEXT,
    embedding VECTOR(1536),  -- pgvector
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50),  -- user, assistant, system
    content TEXT,
    metadata JSONB DEFAULT '{}',
    sources JSONB DEFAULT '[]',  -- episode references
    artifact_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Artifacts
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    type VARCHAR(50),  -- html, react, markdown, code
    content TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_episodes_embedding ON episodes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
```

### Frontend Architecture

#### Pages (App Router)
- `/` - Main chat interface (split pane)
- `/sessions/[id]` - Session view with history
- `/artifacts/[id]` - Standalone artifact view

#### Components
- `ChatPane` - Message list, streaming display, input
- `ArtifactViewer` - Iframe sandbox, version tabs, controls
- `SessionSidebar` - Session list, new session, search
- `MessageBubble` - User/assistant messages with sources
- `StreamingResponse` - Real-time token display

#### State Management
- React Query for server state
- Local state for UI (panes, modals)
- WebSocket for streaming

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}` | Get session with messages |
| DELETE | `/api/sessions/{id}` | Delete session |
| PATCH | `/api/sessions/{id}` | Update session title |
| POST | `/api/chat` | Send message (streaming) |
| WS | `/api/chat/ws/{session_id}` | WebSocket for streaming |
| GET | `/api/artifacts/{id}` | Get artifact |
| POST | `/api/artifacts` | Create artifact |
| POST | `/api/rag/query` | RAG search |

### Streaming Protocol

**Server-Sent Events (SSE)** for HTTP streaming:
```
data: {"type": "token", "content": "Hello"}
data: {"type": "token", "content": " world"}
data: {"type": "sources", "sources": [...]}
data: {"type": "artifact", "artifact_id": "..."}
data: {"type": "done"}
```

**WebSocket** for bidirectional:
```json
{"type": "user_message", "content": "..."}
{"type": "assistant_token", "content": "..."}
{"type": "sources", "sources": [...]}
{"type": "artifact", "artifact_id": "..."}
{"type": "done"}
```

### Security Considerations

1. **Artifact Isolation**: HTML artifacts rendered in sandboxed iframe
   - `sandbox="allow-scripts allow-forms"` (no `allow-same-origin`)
   - Separate origin via `srcdoc` or blob URL
   - CSP headers on artifact endpoint

2. **Input Validation**: Pydantic models for all API inputs

3. **CORS**: Restricted to configured origins

4. **Secrets**: Never in code, only via environment variables

### Configuration Strategy

- Pydantic Settings (`BaseSettings`) for type-safe config
- `.env.example` documents all options
- Environment-specific overrides via `.env.local`
- Docker Compose injects env vars

### Migration Strategy

- Alembic for schema migrations
- Initial migration creates all tables
- Version-controlled migration files
- Run on container startup

## Decisions to Validate

| Decision | Status | Notes |
|----------|--------|-------|
| Next.js App Router vs Vite | To validate | App Router preferred for RSC |
| async SQLAlchemy vs asyncpg | To validate | SQLAlchemy for ORM benefits |
| Ollama in Docker vs host | Host | Avoid GPU passthrough complexity |
| SSE vs WebSocket | To validate | SSE simpler for unidirectional |
| pgvector index type | To validate | IVFFLAT vs HNSW |
| Chunking strategy | To validate | Semantic vs fixed-size |