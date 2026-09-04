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
- **Ship 30 for 30 Skill**: Generates structured writing exercises
- **Artifact System**: Interactive HTML/React/Markdown artifacts with isolated viewer
- **Session Persistence**: Chat history survives browser restarts
- **Multi-Provider LLM**: Ollama (local) + cloud providers

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_BASE_URL` - Ollama API endpoint (default: http://host.docker.internal:11434)
- `OLLAMA_MODEL` - Chat model (default: qwen2.5:7b)
- `OPENAI_API_KEY` - Optional cloud provider
- `ANTHROPIC_API_KEY` - Optional cloud provider

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