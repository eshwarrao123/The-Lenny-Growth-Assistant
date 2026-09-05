# The Lenny Growth Assistant

A production-ready, full-stack AI application that leverages Lenny's Podcast transcripts as a grounded knowledge base to provide expert product and growth advice through conversational chat, specialized skill routing (Ship 30 for 30 essays), and an interactive side-by-side artifact generation and viewing system.

---

## Table of Contents

1. [What the Project Does](#1-what-the-project-does)
2. [Architecture Overview](#2-architecture-overview)
3. [Prerequisites](#3-prerequisites)
4. [Environment Variable Configuration](#4-environment-variable-configuration)
5. [Ollama Setup (Local LLM & Embeddings)](#5-ollama-setup-local-llm--embeddings)
6. [Cloud Provider Setup (Optional OpenAI & Anthropic)](#6-cloud-provider-setup-optional-openai--anthropic)
7. [Database Setup (PostgreSQL 16 + pgvector)](#7-database-setup-postgresql-16--pgvector)
8. [Database Migrations (Alembic)](#8-database-migrations-alembic)
9. [Downloading & Syncing Transcripts](#9-downloading--syncing-transcripts)
10. [Knowledge Base Ingestion Pipeline](#10-knowledge-base-ingestion-pipeline)
11. [Running the Backend Locally](#11-running-the-backend-locally)
12. [Running the Frontend Locally](#12-running-the-frontend-locally)
13. [Running Full Stack via Docker Compose](#13-running-full-stack-via-docker-compose)
14. [Health Check Verification](#14-health-check-verification)
15. [Running Backend Tests (pytest)](#15-running-backend-tests-pytest)
16. [Running Frontend & E2E Tests (Playwright)](#16-running-frontend--e2e-tests-playwright)
17. [Troubleshooting & Operational Runbook](#17-troubleshooting--operational-runbook)
18. [Security Architecture & Sandboxing](#18-security-architecture--sandboxing)
19. [Artifact System Behavior](#19-artifact-system-behavior)
20. [Known Limitations & Trade-offs](#20-known-limitations--trade-offs)
21. [Project Structure](#21-project-structure)

---

## 1. What the Project Does

The **Lenny Growth Assistant** transforms 303 podcast episodes and ~14,000 transcript chunks from *Lenny's Podcast* into an interactive, high-trust intelligence assistant:

- **Grounded Conversational Q&A**: Answers product, growth, and startup questions strictly using transcript evidence retrieved via cosine similarity search over 768-dimensional pgvector embeddings. Every answer includes verifiable speaker and timestamp citations.
- **Dedicated Skill Routing (Ship 30 for 30)**: Automatically transforms transcript insights into structured, atomic essays (~1,250 words) adhering to Dickie Bush and Nicolas Cole's Ship 30 for 30 writing methodology (1/3/1 visual rhythm, rapid Rate of Revelation, and Wheels & Spokes formatting).
- **Interactive Split-Pane Artifact Viewer**: Generates standalone Markdown frameworks/checklists and live HTML/CSS/JS interactive calculators and dashboards. Artifacts render in an isolated, side-by-side pane on desktop and mobile drawer, supporting version history, copy, download, and raw/preview toggling.
- **Guaranteed Out-of-Domain Refusal**: Detects queries that lack sufficient transcript grounding ($\text{similarity} < 0.65$) and cleanly refuses to hallucinate facts.

---

## 2. Architecture Overview

For full technical specifications, see [docs/architecture.md](docs/architecture.md) and [docs/design.md](docs/design.md).

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                             NEXT.JS 14 FRONTEND                          │
│  (Port 3000: App Router, React 18, Tailwind CSS, DOMPurify, SplitPane)   │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ HTTP / SSE (/api/chat)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI BACKEND                              │
│         (Port 8000: Python 3.11+, SQLAlchemy Async, Pydantic v2)         │
│                                                                          │
│  ┌─────────────────┐   ┌──────────────────────┐   ┌───────────────────┐  │
│  │  Skill Router   │──▶│     RAG Engine       │──▶│  Provider Factory │  │
│  │ (QA/Ship30/Art) │   │ (pgvector cosine sim)│   │ (Ollama/OpenAI)   │  │
│  └─────────────────┘   └──────────────────────┘   └───────────────────┘  │
└───────────────────┬───────────────────────────────────┬──────────────────┘
                    │ SQLAlchemy Asyncpg                │ REST / Streaming
                    ▼                                   ▼
┌──────────────────────────────────────┐   ┌───────────────────────────────┐
│     POSTGRESQL 16 + PGVECTOR         │   │         OLLAMA ENGINE         │
│         (Port 5432)                  │   │   (Port 11434 / Local CPU)    │
│  - episodes                          │   │  - nomic-embed-text (768d)    │
│  - transcript_chunks (HNSW index)    │   │  - qwen2.5:7b (Chat & Skills) │
│  - chat_sessions & messages          │   └───────────────────────────────┘
│  - artifacts (versioned history)     │
└──────────────────────────────────────┘
```

---

## 3. Prerequisites

Before installing, ensure the host machine has:

- **Operating System**: Linux, macOS, or Windows 10/11 (WSL2 or PowerShell)
- **Docker & Docker Compose**: v24.0+ (Docker Desktop or Docker Engine)
- **Node.js**: v20.x or later with `npm`
- **Python**: v3.11 or later
- **Ollama**: Installed and running locally (default: `http://localhost:11434`)
- **System RAM**: 16 GB+ recommended for running Ollama `qwen2.5:7b` (4.7 GB model)

---

## 4. Environment Variable Configuration

Copy the example template to create your `.env` file:

```bash
cp .env.example .env
```

> [!IMPORTANT]
> The `.env` file is strictly ignored by `.gitignore`. Never commit actual API keys or credentials.

### Key Variables in `.env`

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `test`, `production`) |
| `POSTGRES_HOST` | `localhost` | Database host (use `postgres` in Docker Compose) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `lenny_assistant` | Database name |
| `EMBEDDING_DIMENSION` | `768` | **STRICT**: 768 for `nomic-embed-text` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint (`http://host.docker.internal:11434` in Docker) |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Primary chat and artifact generation model |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model (must generate 768d vectors) |
| `OPENAI_API_KEY` | *(Optional)* | Key for OpenAI fallback (`gpt-4o`) |
| `ANTHROPIC_API_KEY` | *(Optional)* | Key for Anthropic fallback (`claude-3-5-sonnet`) |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed origins for browser clients |

---

## 5. Ollama Setup (Local LLM & Embeddings)

1. Start the Ollama daemon:
   ```bash
   ollama serve
   ```
2. Pull the required models:
   ```bash
   # Embedding model (768 dimensions)
   ollama pull nomic-embed-text

   # Primary generation model
   ollama pull qwen2.5:7b
   ```
3. Verify models are available:
   ```bash
   curl http://localhost:11434/api/tags
   ```

> [!NOTE]
> On CPU-only environments, loading `qwen2.5:7b` into system memory can take 20–40 seconds on the first inference request. Backend timeouts are configured to 300s to support local CPU execution safely.

---

## 6. Cloud Provider Setup (Optional OpenAI & Anthropic)

To test against commercial cloud models:

1. Add your API keys to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```
2. Switch providers on any request by setting the `"provider"` field:
   ```bash
   curl -N -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "What is PMF?", "provider": "openai"}'
   ```
3. Or select the provider directly from the UI header dropdown.

---

## 7. Database Setup (PostgreSQL 16 + pgvector)

Start the official PostgreSQL container with the `pgvector` extension:

```bash
docker compose up -d postgres
```

Verify the database container is healthy:
```bash
docker compose ps postgres
```

The database initializes with the `vector` extension and standard tables.

---

## 8. Database Migrations (Alembic)

Apply all database schema migrations to initialize tables and indices:

```bash
cd backend
# Activate your virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Apply migrations
alembic upgrade head

# Verify pgvector extension and 768d schema
python scripts/verify_pgvector.py
```

Expected output:
```text
[SUCCESS] pgvector extension exists: version 0.6.0
[SUCCESS] Expected tables present: ['alembic_version', 'artifacts', 'chat_sessions', 'episodes', 'messages', 'transcript_chunks']
[SUCCESS] Dimension verified: 768
[SUCCESS] HNSW Index exists: ix_chunks_embedding
```

---

## 9. Downloading & Syncing Transcripts

The assistant uses real podcast transcripts from Lenny Rachitsky's show. Download/sync all 303 episodes:

```bash
cd backend
python scripts/download_transcripts.py
```

This verifies and writes episode markdown files to `backend/data/transcripts/episodes/`.

---

## 10. Knowledge Base Ingestion Pipeline

Run the idempotent batch ingestion pipeline to parse frontmatter, split paragraphs into semantic chunks, generate 768d embeddings, and populate PostgreSQL:

```bash
cd backend
python scripts/ingest.py --concurrency 8
```

Verify data integrity:
```bash
# Verify record counts and foreign key integrity
python scripts/verify_stored_data.py

# Run a live similarity retrieval test
python scripts/test_vector_retrieval.py
```

Expected verification stats:
- **Episodes**: 303
- **Transcript Chunks**: ~13,875
- **Embeddings Dimension**: 768 (100% verified)
- **Duplicate Episode IDs**: 0
- **Orphan Chunks**: 0

---

## 11. Running the Backend Locally

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Run FastAPI development server with reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

---

## 12. Running the Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

- Web Interface: `http://localhost:3000`
- Configured via `NEXT_PUBLIC_API_URL=http://localhost:8000`

---

## 13. Running Full Stack via Docker Compose

To launch the complete containerized stack:

```bash
docker compose up --build -d
```

Compose manages:
1. `postgres`: PostgreSQL 16 + pgvector on port 5432 with healthchecks.
2. `backend`: FastAPI API on port 8000 with `host.docker.internal` host gateway to connect to your host's Ollama instance.
3. `frontend`: Next.js production build on port 3000, dependent on `backend` being healthy.

Stop the stack:
```bash
docker compose down
```

---

## 14. Health Check Verification

The `/api/health` endpoint provides comprehensive component-level readiness:

```bash
curl -i http://localhost:8000/api/health
```

### Response Semantics:
- **`200 OK (healthy)`**: PostgreSQL is connected via fast `SELECT 1` and Ollama is reachable with required models loaded.
- **`200 OK (degraded)`**: Core database is online, but an optional cloud provider (e.g. OpenAI) has missing keys.
- **`503 Service Unavailable (unavailable)`**: Critical dependency (PostgreSQL database) is unreachable.

### Sample Response:
```json
{
  "status": "healthy",
  "application": "ok",
  "db": "ok",
  "ollama": "ok",
  "openai": "missing_key",
  "components": {
    "database": { "status": "ok" },
    "ollama": {
      "status": "ok",
      "model": "qwen2.5:7b",
      "embedding_model": "nomic-embed-text",
      "reachable": true,
      "chat_model": true,
      "embed_model": true
    },
    "openai": { "status": "missing_key" }
  },
  "environment": "development"
}
```

---

## 15. Running Backend Tests (pytest)

Run the full backend test suite covering unit tests, RAG retrieval, skill routing, provider abstractions, and session lifecycles:

```bash
cd backend
pytest -v
```

Status: **36 passed in ~1.1s**.

---

## 16. Running Frontend & E2E Tests (Playwright)

Run the Playwright test suite against the running frontend and backend stack:

```bash
cd frontend

# Run all E2E specs
npx playwright test

# Targeted test runs:
npx playwright test tests/e2e/core.spec.ts           # Core chat, streaming, sessions, versioning (13 tests)
npx playwright test tests/e2e/security.spec.ts       # Iframe sandbox, DOMPurify, XSS defense (3 tests)
npx playwright test tests/e2e/accessibility.spec.ts  # a11y landmarks, iframe title, focus trap (6 tests)
npx playwright test tests/e2e/responsive.spec.ts     # Desktop split pane, tablet, mobile drawer (3 tests)
npx playwright test tests/e2e/copy-download.spec.ts  # Copy and file download verification (4 tests)
npx playwright test tests/e2e/real-ollama.spec.ts    # Real end-to-end Ollama generation (2 tests)
```

Status: **31 passed**.

---

## 17. Troubleshooting & Operational Runbook

For complete operational diagnosis and incident recovery, consult **[docs/runbook.md](docs/runbook.md)**.

### Common Issues:

1. **Database Connection Refused**:
   - Verify container is running: `docker compose ps postgres`.
   - Ensure `POSTGRES_HOST=localhost` in `.env` for local runs, or `POSTGRES_HOST=postgres` inside Docker. Avoid ephemeral WSL2 internal IP addresses.
2. **Ollama Read Timeout on CPU**:
   - Initial generation on CPU requires loading model weights into RAM (30–45s). Ensure `httpx` timeouts are set to 300s (configured by default in `OllamaProvider`).
3. **Embedding Dimension Mismatch**:
   - Error `expected 768 dimensions, got ...` indicates an incorrect model was used. Pull `nomic-embed-text` explicitly.
4. **Port In Use (8000 / 3000 / 5432)**:
   - Identify blocking process: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux/macOS).

---

## 18. Security Architecture & Sandboxing

1. **Sandboxed Iframe Isolation**:
   - All HTML artifacts are rendered inside an `<iframe sandbox="allow-scripts">`.
   - `allow-same-origin` is **strictly omitted**, giving the iframe a null origin. Untrusted code cannot access parent cookies, `localStorage`, `sessionStorage`, or the host DOM.
2. **Markdown DOMPurify Sanitization**:
   - Markdown documents are rendered via `react-markdown` and sanitized with strict DOMPurify rules forbidding inline `<script>` tags, `javascript:` URIs, and event handlers (`onload`, `onerror`).
3. **Payload Safeguards**:
   - Artifact bodies and chat messages are capped at 5MB at the API and database levels to prevent memory exhaustion attacks.
4. **Credential Redaction**:
   - Structlog filters automatically redact sensitive keys (`authorization`, `api_key`, `password`, `token`, `cookie`) before emitting JSON logs.

---

## 19. Artifact System Behavior

- **Side-by-Side Coexistence**: On screens $\ge 1024\text{px}$, the chat pane occupies `flex: 1 1 0%` while the artifact viewer expands smoothly with a 260px minimum width up to 70% width. Neither pane overlaps or displaces messages.
- **Mobile Drawer**: On mobile viewports ($< 768\text{px}$), the sidebar navigation slides off-canvas (`-translate-x-full`), and artifacts present in an accessible full-screen modal.
- **Live Streaming**: Emits `artifact_start`, `artifact_chunk`, and `artifact_done` SSE events, rendering content incrementally as the LLM generates tokens.
- **Version Switcher**: Modifying an artifact produces a new version (`v1`, `v2`, ...). Users can click version buttons in the header toolbar to inspect or restore prior iterations.
- **Raw / Preview Mode**: Toggle between formatted preview and monospace markdown source code.
- **Export Controls**: One-click copy to clipboard and direct file download (`.md` or `.html`).

---

## 20. Known Limitations & Trade-offs

1. **Local CPU Generation Latency**: Running Ollama on local CPU without dedicated GPU acceleration generates tokens at ~5–12 tokens/sec. Complex HTML artifacts may take 60–90 seconds. Cloud providers (OpenAI/Anthropic) offer sub-second TTFT when API keys are supplied.
2. **Single-Node In-Memory SSE State**: SSE streaming chunks are streamed directly from the backend worker. In a multi-replica cluster, sticky sessions or a shared pub/sub bus (e.g., Redis) would be required.
3. **Theme Support**: The interface is intentionally locked to a dark mode aesthetic tailored to the Lenny brand palette. Light mode toggle is not implemented.
4. **External CDNs in Sandboxed Iframes**: Sandboxed null-origin iframes require network connectivity to load external CSS/JS frameworks. Artifacts generated with vanilla CSS and inline JavaScript provide the highest reliability in offline environments.

---

## 21. Project Structure

```text
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routers (chat, sessions, artifacts, health)
│   │   ├── core/                # Configuration, logging, database engine
│   │   ├── models/              # SQLAlchemy models (Episode, Chunk, Session, Message, Artifact)
│   │   ├── providers/           # LLM provider abstractions (Ollama, OpenAI, Anthropic, Factory)
│   │   ├── schemas/             # Pydantic v2 schemas and validation
│   │   ├── services/            # Chat service, RAG engine, skill routing
│   │   │   └── skills/          # Grounded QA, Ship 30 essay, Artifact generator
│   │   └── main.py              # Application lifecycle and middleware
│   ├── alembic/                 # Database schema migrations
│   ├── scripts/                 # Download, ingestion, verification, and test scripts
│   ├── tests/                   # Pytest suite (36 tests)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages and layout
│   │   ├── components/          # React components (ArtifactViewer, SandboxedIframe, MarkdownArtifact)
│   │   ├── lib/                 # Utilities and API client
│   │   └── styles/              # Global CSS, design tokens, and animations
│   ├── tests/
│   │   └── e2e/                 # Playwright test specs (31 tests)
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── PRD.md                   # Product requirements document
│   ├── architecture.md          # System architecture and data flows
│   ├── design.md                # UI design tokens, component inventory, and interaction patterns
│   └── runbook.md               # Operational runbook and troubleshooting guide
├── agent_transcripts/
│   ├── README.md                # Development trajectory index
│   └── PHASE_1_TO_8_DEVELOPMENT_LOG.md  # Detailed phase log with decisions and corrections
├── docker-compose.yml           # Multi-service production orchestration
├── .env.example                 # Comprehensive environment variable template
├── .gitignore                   # Rigorous secret, artifact, and build exclusion rules
└── README.md                    # Project documentation and operational handoff
```

---

## License

MIT License. See LICENSE for details.