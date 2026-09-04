# The Lenny Growth Assistant - Product Requirements Document

## Overview
A full-stack AI application that uses Lenny's Podcast transcripts as a grounded knowledge base to provide expert product/growth advice through conversational chat with artifact generation capabilities.

## Core Features

### 1. Chat Interface
- Streaming responses from LLM
- Persistent chat sessions with history
- Multi-turn conversations with context
- Session management (create, list, delete, rename)

### 2. RAG over Lenny's Podcast Transcripts
- Grounded responses using episode transcripts
- Semantic search with pgvector
- Source citation with episode references
- Configurable retrieval parameters

### 3. Agent/Skill Layer
- **Ship 30 for 30 Writing Skill**: Generate structured writing exercises
- **Artifact Generation Skill**: Create interactive HTML artifacts
- Extensible skill registry for future skills

### 4. Artifact System
- In-app artifact viewer (Claude Artifacts style)
- Secure HTML isolation via iframe sandbox
- Artifact versioning and persistence
- Support for HTML, React components, Markdown, Code

### 5. LLM Provider Abstraction
- Ollama (local) - primary for demo
- OpenAI (cloud) - optional
- Anthropic (cloud) - optional
- Unified interface for chat, embeddings, streaming

## Technical Requirements

### Backend
- FastAPI with async support
- PostgreSQL + pgvector
- SQLAlchemy async ORM
- Structured logging (structlog)
- WebSocket for streaming
- Health checks

### Frontend
- Next.js 14+ App Router
- TypeScript
- Tailwind CSS
- Split-pane layout (chat + artifact viewer)
- Real-time streaming UI
- Responsive design

### Infrastructure
- Docker Compose for local development
- PostgreSQL with pgvector extension
- Ollama running on host (not in Docker)
- .env.example for configuration

### Testing
- pytest for backend unit/integration tests
- Playwright for E2E browser testing
- CI-ready test configuration

## Data Model

### Episodes
- id, guest, title, youtube_url, video_id, publish_date
- description, duration_seconds, view_count, channel
- transcript_content, embedding vector

### Chat Sessions
- id, title, created_at, updated_at
- messages (JSONB array)

### Messages
- id, session_id, role, content, metadata
- sources (episode references)
- artifacts (generated artifact IDs)

### Artifacts
- id, session_id, message_id, type, content
- version, created_at

## User Flows

1. **New Chat**: User opens app → creates new session → starts chatting
2. **RAG Query**: User asks question → system retrieves relevant episodes → generates grounded response
3. **Skill Invocation**: User requests writing exercise → Ship 30 skill generates structured output → artifact created
4. **Artifact View**: User clicks artifact → opens in side pane → can iterate/regenerate
5. **Session Persistence**: User closes browser → returns later → sessions restored

## Acceptance Criteria

- [ ] Streaming chat works with Ollama
- [ ] RAG returns relevant episodes with citations
- [ ] Ship 30 for 30 skill produces valid writing exercises
- [ ] Artifacts render safely in isolated viewer
- [ ] Sessions persist across browser restarts
- [ ] Docker Compose starts all services
- [ ] Tests pass (unit + E2E)
- [ ] Documentation complete for handoff

## Out of Scope (Phase 0)
- Full transcript ingestion pipeline
- Production deployment config
- Authentication/authorization
- Multi-user support
- Analytics/metrics