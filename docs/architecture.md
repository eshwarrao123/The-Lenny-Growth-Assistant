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
* `GET /api/health`: Returns detailed multi-tier operational status:
  - `healthy` (HTTP 200): PostgreSQL database reachable via `SELECT 1`, Ollama reachable with both `qwen2.5:7b` chat model and `nomic-embed-text` embedding model verified via `/api/tags`.
  - `degraded` (HTTP 200): Database reachable, but one LLM model is missing or optional cloud provider is unconfigured.
  - `unavailable` (HTTP 503): Primary PostgreSQL database unreachable. Triggers container orchestrator failure detection without leaking credentials.

## 7. Security Boundaries

* **User Input**: Sanitized and parameterized via SQLAlchemy.
* **Transcripts**: Evaluated as untrusted `<context>` chunks to prevent prompt injection overriding core agent instructions.
* **HTML Artifacts**: Strictly sandboxed on the client-side via `<iframe sandbox="allow-scripts">` (explicitly omitting `allow-same-origin`) to ensure zero access to parent DOM, storage, or cookies.
* **Secrets**: Managed purely server-side via `.env` (Pydantic `BaseSettings`) with structured logging filters masking sensitive keys.

## 8. Docker Topology

* `postgres`: Official `pgvector/pgvector:pg16` image on port `5432` with volume `postgres_data` and healthcheck `pg_isready -U postgres -d lenny`.
* `backend`: FastAPI Python container. Connects to `postgres:5432` and host Ollama via `http://host.docker.internal:11434`. Configured with `extra_hosts: ["host.docker.internal:host-gateway"]` for seamless cross-platform Linux/WSL2/Windows host gateway access, plus container healthcheck inspecting `/api/health`.
* `frontend`: Next.js Node container on port `3000`, configured with `depends_on: { backend: { condition: service_healthy } }`.
* **Host OS**: Ollama runs directly on the host to maximize hardware capability and avoid GPU passthrough complexities.
* **Network**: Dedicated bridge network `lenny-network` isolating internal inter-service traffic.

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

## 11. Skill Routing & Capability Architecture (Phase 5)

Phase 5 transitions the Lenny Growth Assistant from a single-mode chat endpoint into an extensible capability-based system.

### 11.1 Skill Abstraction (`BaseSkill`)
All skills implement the abstract `BaseSkill` interface (`backend/app/services/skills/base.py`):
```python
class BaseSkill(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute_stream(
        self, context: SkillContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass
```
The execution context (`SkillContext`) encapsulates:
- `session_id`: Active session UUID
- `user_message`: Raw user prompt
- `history`: Prior conversation turns from PostgreSQL (`List[Message]`)
- `provider_name`: Configured LLM provider (`"ollama"`, `"openai"`)
- `retriever`: Shared `TranscriptRetriever` instance
- `resolved_query`: Cleaned or anaphorically-resolved subject query

### 11.2 Deterministic Skill Routing (`SkillRouter`)
The `SkillRouter` routes incoming chat queries without introducing extra LLM classification latency or non-determinism:
1. **Explicit Skill Parameter**: If the client provides `skill="qa"` or `skill="ship30"`, that skill executes directly.
2. **Slash Commands**: Supports `/ship30 <topic>` or `/qa <question>` shortcuts.
3. **Deterministic Pattern Matching**: Matches explicit Ship 30 intent phrases (e.g., `"ship 30"`, `"ship30"`, `"ship 30 for 30 essay"`, `"turn this into an essay"`, `"1,250 word essay"`).
4. **Anaphoric Reference Resolution**: When the user asks *"Turn that into a Ship 30 essay"* or *"Give me the Ship 30 version of that"*, the router resolves the subject topic from the preceding session turns (last assistant response or user question).
5. **Default Fallback**: Normal questions default to `GroundedQASkill`.

### 11.3 Grounded Q&A Skill (`GroundedQASkill`)
* Preserves 100% of Phase 4 grounded QA behavior.
* Retrieves top-K chunks ($K=5$, threshold $\ge 0.65$).
* Fallback to conversational context when user asks follow-up questions.
* Fast-path refusal if no relevant transcript chunks exist in the vector database.

### 11.4 Ship 30 for 30 Writing Skill (`Ship30Skill`)
Transforms Lenny transcript wisdom into published-quality atomic essays (~1,250 words) adhering strictly to official Ship 30 for 30 principles:
- **Visual Rhythm (1/3/1 and 1/5/1 Structure)**: Alternates single-sentence hooks, short 2–3 sentence explanatory blocks, and punchy single-line takeaways. Eliminates walls of text.
- **Fast Rate of Revelation**: High velocity of new insights per paragraph, cutting preamble and filler.
- **Wheels & Spokes Architecture**: Clear modular subheadings (`##`) containing:
  1. *Headline*: Strong, specific claim.
  2. *Anchor / Evidence*: Real insights from Lenny guests.
  3. *Actionable Takeaway*: Direct framework or tactical exercise.
- **Content Differentiation ("The Tequila Test")**: Forces radical specificity to the featured guest (e.g., Elena Verna, Shreyas Doshi) so the essay cannot be confused with generic business writing.
- **Strict Transcript Grounding**: Transcript chunks are injected inside `<transcript_context>` tags as raw reference data, not system instructions. The model is forbidden from inventing quotes or citing guests not present in the evidence.

### 11.5 Output Validation
The `validate_ship30_output` function performs lightweight structural validation:
- **Word Count**: Targets ~1,250 words with an operational tolerance of 850–1,600 words for local 7B models.
- **Markdown Integrity**: Ensures presence of structural headings (`#`, `##`).
- **Citation Traceability**: Verifies format `[Source: Guest Name — Episode Title — HH:MM:SS]`.
- **Injection / Leakage Defense**: Confirms internal system prompt tags (`<transcript_context>`, `SYSTEM INSTRUCTIONS`) are not leaked into the user-facing text.

### 11.6 SSE Streaming & Persistence Integration
- Reuses the existing Server-Sent Events contract (`event: start`, `sources`, `token`, `done`, `error`).
- Emits the active skill identifier in the `start` event payload (`{"session_id": "...", "skill": "ship30"}`).
- Persists both user requests and generated essays to the PostgreSQL `messages` table with complete JSONB `sources` citations.

## 12. Artifact Architecture & Security System (Phase 6)

Phase 6 implements the complete interactive artifact generation, streaming, rendering, versioning, and sandboxed preview system.

### 12.1 Artifact Pipeline & Routing (`ArtifactSkill`)
Artifact creation requests are identified via deterministic trigger detection in `SkillRouter`:
- **Triggers**: Explicit `/artifact <prompt>` commands or natural language keywords such as `create a markdown checklist`, `create an html tool`, `build a component`, `create an interactive calculator`.
- **Precedence**: Evaluated immediately following Ship 30 intent checks, ensuring specialized writing prompts retain their dedicated formatting while artifact generation activates for documents and interactive apps.
- **Grounding Support**: The `ArtifactSkill` inspects the user query for Lenny podcast domain relevance. When grounding is warranted, it calls `retriever.retrieve(query)` and provides relevant transcript evidence inside `<transcript_context>` blocks. Pure standalone tools (e.g., calculators, timers) bypass transcript retrieval for minimal latency.
- **Generation Formats**:
  - `markdown`: Checklists, frameworks, strategy documents, guides, and tables.
  - `html`: Single-file interactive applications containing embedded `<style>` and `<script>` blocks.

### 12.2 Server-Sent Events (SSE) Streaming Protocol
Artifact tokens are streamed in real time to the frontend via dedicated SSE events, bypassing the main chat message bubble:
1. `event: start` -> `{"session_id": "...", "skill": "artifact"}`
2. `event: status` -> `{"message": "Creating artifact..."}`
3. `event: artifact_start` -> `{"id": "uuid", "title": "Checklist", "type": "markdown"|"html"}`
4. `event: artifact_chunk` -> `{"content": "chunk text"}` (streamed progressively into the active Artifact Viewer pane)
5. `event: artifact_done` -> `{"artifact_id": "uuid"}` (signals completion; frontend caches and updates message card link)
6. `event: done` -> `{}` (closes stream)

### 12.3 Persistence & Versioning Data Model
Artifact records are persisted in the PostgreSQL `artifacts` table:
```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,        -- 'html' | 'markdown'
    title VARCHAR(255) NOT NULL,      -- e.g. 'Calculator'
    content TEXT NOT NULL,            -- raw markup or markdown
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
- **Incremental Versioning**: When an artifact with the same `title` is generated or updated within the same `session_id`, the system queries the maximum existing `version` and increments it (`version = max_version + 1`).
- **REST Retrieval**:
  - `GET /api/artifacts/{id}`: Returns `{ id, session_id, message_id, type, title, content, version, created_at, updated_at }`.
  - `GET /api/artifacts/versions/{session_id}/{title}`: Returns an array of all historical versions for the artifact, enabling instant switching via the viewer tabs.

### 12.4 Client-Side Sandboxing & Isolation (HTML Artifacts)
Security is paramount when rendering user-requested or LLM-generated HTML/JavaScript:
- **Sandbox Attribute**: Rendered in an `<iframe>` with `sandbox="allow-scripts"`.
- **Strictly No `allow-same-origin`**: Omitting `allow-same-origin` forces the iframe into an opaque, unique origin. Any attempts by scripts inside the iframe to access:
  - `window.parent.document`
  - `window.parent.localStorage`
  - `window.parent.sessionStorage`
  - `window.parent.cookie`
  - `window.top`
  will immediately throw a browser `SecurityError` (cross-origin DOMException).
- **Navigation Isolation**: `allow-top-navigation` is deliberately excluded, preventing malicious artifacts from redirecting the parent window or executing clickjacking attacks.
- **Form Submissions**: Forms are isolated within the sandbox context (`allow-forms` only if explicitly needed, default restricted).

### 12.5 DOMPurify & Markdown Sanitization
- Markdown content is rendered into React components using `react-markdown` and `remark-gfm`.
- Embedded raw HTML is passed through `DOMPurify.sanitize()` configured with strict allowlists. Dangerous elements (`<script>`, `<object>`, `<embed>`, `<iframe>`, `<base>`) and inline event handlers (`onload`, `onerror`, `onclick`, `onmouseover`) are excised before DOM insertion.

### 12.6 Payload Limits & Safety Safeguards
- **5MB Size Limit**: Artifact content payloads are restricted to a maximum of 5,242,880 bytes (5MB). Requests exceeding this limit are rejected with HTTP 413 / `error` SSE event to prevent client and database denial-of-service.
- **Client Cache**: The frontend maintains an in-memory `artifactsCacheRef` mapping artifact IDs to content and metadata. This provides zero-latency reopening even during active streaming or temporary network glitches.

### 12.7 UI Layout & Responsive Adaptation
- **Desktop (≥1024px)**: Coexisting side-by-side split pane (`.chat-pane-host` with `flex: 1 1 0%` and `.artifact-pane-host` with `min-width: 260px; max-width: 70%`). Both panes remain fully interactive simultaneously.
- **Tablet (768px–1023px)**: Side-by-side layout with a collapsible navigation sidebar to maximize workspace. The artifact viewer retains a minimum width of 260px.
- **Mobile (<768px)**: Off-canvas navigation drawer (`-translate-x-full` when closed, `translate-x-0` when open) and full-screen overlay artifact viewer (`z-50`) with no horizontal scroll overflow.

### 12.8 Accessibility & Keyboard Navigation
- Registered as an accessible region with `role="region"` and `aria-label="Artifact viewer"`.
- Contains an explicit `title="Artifact Preview"` on the `<iframe>`.
- Full keyboard trap prevention: `Escape` closes the viewer and returns focus to the chat textarea; tabs cycle cleanly across copy, download, raw/preview, and version buttons with high-contrast focus rings.

## 14. Production Hardening, Logging & Observability (Phase 8)

Phase 8 hardens the application for deterministic evaluator startup, operational diagnostics, and resilient recovery.

### 14.1 Multi-Tier Health Check System
The `/api/health` endpoint serves as an active readiness probe for Docker Compose and evaluators:
- **Fast Database Probe**: Executes `SELECT 1` without table scans. If unreachable, immediately signals `status: "unavailable"` and HTTP 503.
- **Model Registry Inspection**: Verifies presence of both chat model (`qwen2.5:7b`) and embedding model (`nomic-embed-text`) via `/api/tags` with a 5-second timeout, avoiding costly generation latency during health polls.
- **Degraded Execution Awareness**: Distinguishes between critical infrastructure failure (database offline) and non-blocking dependency absence (cloud API keys unconfigured).

### 14.2 Structured Logging & Metric Telemetry
Configured using `structlog` to emit JSON in non-interactive environments and colored output in terminal sessions:
- **Structured Fields**: Every chat generation emits `session_id`, `skill`, `provider`, `message_len`, `retrieval_count`, `has_artifact`, and `total_latency_ms`.
- **Sensitive Data Scrubbing**: An automated log processor inspects all event dictionaries, redacting authorization headers, API keys, passwords, session tokens, and cookie strings to `[REDACTED]`.
- **Payload Truncation**: Prevents multi-kilobyte transcript chunks or prompt bodies from polluting operational log streams.

### 14.3 Error Handling & Failure Boundaries
- **Database Failures**: Cleanly surfaces connection drops with fallback error states in SSE stream (`event: error\ndata: {"code": "database_error"}`).
- **LLM Interruptions & Timeouts**: Configured with explicit `httpx.Timeout(300.0, connect=30.0)` tuned for CPU-based Ollama execution. Client stream disruptions terminate async generators cleanly without leaking connections.
- **Deterministic Migrations**: Database schema creation is strictly managed via Alembic (`002_phase2_schema`). The application startup validates migration state without running destructive drops.
- **Operational Runbook**: Standard operating procedures, failure remediation workflows, and disaster recovery commands are documented in `docs/runbook.md`.

## 15. Decisions Intentionally Deferred (Post-Phase 8)
- Hybrid search (BM25 + Dense reciprocal rank fusion).
- Web container / Node.js execution environment in browser (WebAssembly).
- Multi-user authentication & workspace collaboration (RBAC).
- Real-time collaborative artifact editing via CRDTs.