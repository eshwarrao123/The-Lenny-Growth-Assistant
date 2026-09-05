# The Lenny Growth Assistant

A full-stack AI application that uses Lenny's Podcast transcripts as a grounded knowledge base to provide expert product/growth advice through conversational chat with artifact generation capabilities.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy async, Pydantic v2
- **Database**: PostgreSQL 16 + pgvector
- **AI**: Ollama (local), OpenAI/Anthropic (cloud optional)
- **Infrastructure**: Docker Compose
- **Testing**: pytest, Playwright

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Ollama (running locally with `qwen2.5:7b` model)

### Development Setup

```bash
# Clone and enter project
cd lenny-growth-assistant

# Copy environment template
cp .env.example .env

# Start infrastructure (PostgreSQL + pgvector)
docker compose up -d postgres

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head

# Frontend setup
cd ../frontend
npm install
npm run dev

# Start backend (in separate terminal)
cd ../backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose (Full Stack)

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Project Structure

```
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Config, security, database
│   │   ├── models/        # SQLAlchemy models
│   │   ├── providers/     # LLM provider abstractions
│   │   ├── services/      # Business logic (chat, RAG, skills)
│   │   └── main.py        # App entry point
│   ├── alembic/           # Database migrations
│   ├── tests/             # pytest tests
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities, API client
│   │   └── styles/        # Global styles
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── design.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Key Features

- **Streaming Chat**: Real-time token streaming via SSE/WebSocket
- **RAG Pipeline**: Semantic search over podcast transcripts with citations
- **Ship 30 for 30 Skill**: Transforms transcript insights into structured, grounded atomic essays (~1,250 words) adhering to Ship 30 for 30 principles
- **Artifact System**: (Planned for Phase 6) Interactive HTML/React/Markdown artifacts with isolated viewer
- **Session Persistence**: Chat history and source citations survive browser restarts
- **Multi-Provider LLM**: Ollama (local default) + optional cloud providers

## Usage Examples

### 1. Grounded Q&A (Default Skill)
Ask questions across Lenny's 303 podcast episodes:
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-uuid",
    "message": "What does Elena Verna say about product-led sales?",
    "provider": "ollama"
  }'
```
* **Routing**: Automatically routes to `grounded_qa`.
* **Behavior**: Retrieves transcript chunks with similarity $\ge 0.65$, streams real-time SSE tokens, and provides verifiable timestamp citations (e.g. `[Source: Elena Verna — The ultimate guide to product-led sales — 01:16:33]`).

### 2. Ship 30 for 30 Essay (Dedicated Capability)
Request a published-quality atomic essay directly or as a conversational follow-up:
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-uuid",
    "message": "Turn that into a Ship 30 for 30 essay.",
    "provider": "ollama"
  }'
```
* **Routing**: Deterministically routes to `ship30` (also supports `/ship30 <topic>` and explicit `"skill": "ship30"`).
* **Context Resolution**: Resolves anaphoric references ("that", "this") from conversation history to target Elena Verna's product-led sales principles.
* **Style**: Employs 1/3/1 visual rhythm, rapid Rate of Revelation, Wheels & Spokes subheadings, and actionable takeaways, grounded strictly in Lenny transcript evidence.

### 3. Out-of-Domain Refusal
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-uuid",
    "message": "Write a Ship 30 essay about quantum computing qubits.",
    "provider": "ollama"
  }'
```
* **Behavior**: Detects insufficient transcript evidence in the vector index and issues a safe refusal rather than hallucinating facts.

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_BASE_URL` - Ollama API endpoint (default: http://host.docker.internal:11434)
- `OLLAMA_MODEL` - Chat model (default: qwen2.5:7b)
- `OPENAI_API_KEY` - Optional cloud provider
- `ANTHROPIC_API_KEY` - Optional cloud provider

## Knowledge Base Ingestion & Verification

The Lenny Growth Assistant retrieves facts directly from Lenny's Podcast transcripts ingested into PostgreSQL + pgvector.

### Step-by-Step Production Setup

1. **Start Docker Infrastructure (PostgreSQL + pgvector)**:
   ```powershell
   # Run PostgreSQL 16 container with pgvector extension
   docker compose up -d postgres
   docker version
   docker compose version
   ```

2. **Verify & Start Ollama Embedding Engine**:
   Ensure Ollama is running and pull the official `nomic-embed-text` 768-dimension embedding model:
   ```powershell
   ollama pull nomic-embed-text
   # Verify reachable at http://localhost:11434/api/tags
   ```

3. **Synchronize Real Podcast Transcripts**:
   Download/sync the latest transcript repository from ChatPRD:
   ```powershell
   cd backend
   $env:PYTHONPATH="."
   python scripts/download_transcripts.py
   ```
   *Discovers and validates all 303 episode directories under `backend/data/transcripts/episodes/`.*

4. **Apply Alembic Migrations**:
   ```powershell
   alembic upgrade head
   python scripts/verify_pgvector.py
   ```
   *Validates `vector` extension, 768d embedding columns, and HNSW cosine distance index (`<=>`).*

5. **Run High-Speed Pipeline Ingestion**:
   ```powershell
   python scripts/ingest.py --concurrency 8
   ```
   *Parses frontmatter metadata, chunks paragraphs by token limits while maintaining speaker/timestamp context, generates 768d embeddings in batches via Ollama `/api/embed`, and performs idempotent database writes.*

6. **Verify Data Integrity & Retrieval**:
   ```powershell
   # Comprehensive database verification
   python scripts/verify_stored_data.py

   # Real similarity vector retrieval test
   python scripts/test_vector_retrieval.py
   ```

### Verified Pipeline Outputs

- **pgvector Check (`verify_pgvector.py`)**:
  ```text
  [SUCCESS] pgvector extension exists: version 0.6.0
  [SUCCESS] Expected tables present: ['alembic_version', 'artifacts', 'chat_sessions', 'episodes', 'messages', 'transcript_chunks']
  [SUCCESS] Dimension verified: 768
  [SUCCESS] HNSW Index exists: ix_chunks_embedding
  [SUCCESS] Cosine distance query executed cleanly with <=> operator
  ```

- **Stored Data Statistics (`verify_stored_data.py`)**:
  ```text
  Episode Count: 303
  Chunk Count: ~13,875
  Embedding Count: ~13,875
  Embedding Dimension: 768 (100% verified)
  Duplicate Episode IDs: 0
  Missing Citation Metadata: 0
  Orphan Chunks (FK Violation): 0
  ```

- **Vector Similarity Search (`test_vector_retrieval.py`)**:
  Query: *"How do you measure product-market fit?"*
  Returns top-K matching chunks with episode title, guest name, speaker label, timestamp citation, chunk UUID, and cosine similarity score.

### Troubleshooting

- **PostgreSQL Connection Refused**:
  Ensure `POSTGRES_HOST=localhost` in `.env` matches your container binding on port 5432. Avoid using ephemeral WSL2 virtual interface IPs as they change across host system reboots.
- **Ollama Dimension Mismatch**:
  Ensure `OLLAMA_EMBEDDING_MODEL=nomic-embed-text` is configured in `.env`. Do NOT substitute with 384d or 1536d models without updating migration schema.
- **Idempotency & Rebuild**:
  Running `python scripts/ingest.py` without `--refresh` skips existing episodes without duplicating records. Use `python scripts/ingest.py --refresh` to delete and rebuild specific episodes cleanly.

## Testing

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm test

# E2E tests
cd frontend
npx playwright test
```

## Documentation

- [PRD](docs/PRD.md) - Product requirements
- [Architecture](docs/architecture.md) - Technical architecture
- [Design](docs/design.md) - Visual and interaction design

## License

MIT