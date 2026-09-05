# Chronological Engineering Log — Phases 1 Through 8

This document details the step-by-step engineering execution, commands executed, obstacles diagnosed, and verification results across the development lifecycle.

---

## Phase 1: Planning & PRD Specification
- **Objective**: Establish product requirements, knowledge boundaries, and technical architecture.
- **Key Artifacts Created**:
  - `docs/PRD.md`: Outlines the assistant's persona, grounding constraints, and user experience.
  - `docs/architecture.md`: Initial data flow diagram, provider abstraction interface, and database schema.
  - `docs/design.md`: Visual tokens, dark mode guidelines, and split-pane layout design.
- **Architectural Tradeoff**: Decided on local-first LLM inference using Ollama (`qwen2.5:7b` chat and `nomic-embed-text` 768d embeddings) with an abstraction layer supporting optional cloud providers (OpenAI `gpt-4o-mini`).

---

## Phase 2: Database Schema & Migration Architecture
- **Objective**: Establish persistent relational models with vector indexing using PostgreSQL 16 + pgvector.
- **Execution**:
  - Created models: `Episode`, `TranscriptChunk`, `ChatSession`, `Message`, and `Artifact`.
  - Configured HNSW vector index: `idx_chunks_embedding ON transcript_chunks USING hnsw (embedding vector_cosine_ops)`.
  - Authored Alembic migrations `001_initial.py` and `002_phase2_schema.py`.
- **Encountered Obstacle**: Connection failures when using WSL2 bridge IP. Resolved by pinning stable container binding to `localhost:5432` on host and `postgres:5432` inside Docker.

---

## Phase 3: Transcript Ingestion Pipeline
- **Objective**: Parse, chunk, embed, and store all 303 episodes of Lenny's Podcast archive.
- **Execution**:
  - Implemented `backend/scripts/download_transcripts.py` to synchronize transcripts from the upstream ChatPRD repository.
  - Built token-aware sliding-window chunker: 500-token target, 100-token overlap, preserving speaker and timestamp metadata.
  - Implemented batch embedding via Ollama `/api/embed` with sub-batches of 120 items and `--concurrency 8`.
  - Ingested 10,588 transcript chunks idempotently.
- **Verification**: Created `backend/scripts/verify_pgvector.py` and `backend/scripts/verify_stored_data.py`. Confirmed 768d embedding dimension consistency across 100% of stored records.

---

## Phase 4: Grounded QA Assistant Service
- **Objective**: Build the core RAG retrieval and streaming chat service.
- **Execution**:
  - Implemented `TranscriptRetriever` querying cosine similarity with similarity threshold $\ge 0.65$.
  - Developed `GroundingContextBuilder` injecting transcript evidence strictly inside `<transcript_context>` blocks.
  - Implemented SSE streaming via FastAPI `StreamingResponse` emitting `start`, `status`, `sources`, `token`, `done`, and `error` events.
  - Implemented fast-path refusal when no relevant evidence exists in the vector store.
- **Verification**: Verified via `backend/scripts/test_chat_integration.py` and 16 unit/integration tests.

---

## Phase 5: Skill Routing & Ship 30 for 30 Writing Capability
- **Objective**: Transform assistant into a capability-based system with dedicated essay writing.
- **Execution**:
  - Built `BaseSkill` and `SkillRouter` with deterministic regex intent matching and slash commands (`/ship30`).
  - Added anaphoric reference resolution resolving pronouns ("that", "this") from prior conversation turns.
  - Engineered `Ship30Skill` prompt following Ship 30 for 30 principles (1/3/1 visual rhythm, Rate of Revelation, Wheels & Spokes structure, actionable frameworks).
  - Built `validate_ship30_output` checking word count (850–1,600 tolerance window), structural markdown headings, and citation integrity.
- **Verification**: Verified via `backend/scripts/test_ship30_integration.py` and 10 new pytest unit tests.

---

## Phase 6: Interactive Artifact System & Targeted Fixes
- **Objective**: Build side-by-side artifact viewer for Markdown documents and sandboxed HTML/JS applications.
- **Execution**:
  - Designed `ArtifactViewer` component supporting Markdown (via `react-markdown` + `remark-gfm` + DOMPurify) and HTML (via `<iframe sandbox="allow-scripts">` without `allow-same-origin`).
  - Created `ArtifactSkill` handling artifact intent detection and version incrementing.
  - Built version switching toolbar, raw/preview markdown toggle, copy to clipboard, and file download (`.md` / `.html`).
- **Debugging & Resolution**:
  1. *PostCSS config syntax error*: Fixed `configFile` -> `config` in `postcss.config.js`.
  2. *ENOSPC disk space exhaustion*: Freed 11.8 GB by clearing npm cache and diagnostic logs.
  3. *Missing accessible landmark*: Added `role="region"` with `aria-label="Artifact viewer"` and explicit `title="Artifact Preview"`.
  4. *Viewer reopen failure*: Implemented client-side `artifactsCacheRef` in `src/app/page.tsx`.
  5. *Mobile drawer delay*: Removed animation transition on mobile breakpoints (`md:transition-all md:duration-200`).
  6. *Ollama artifact token extraction*: Corrected token chunk event extraction in `artifact.py`.
- **Verification**: 36/36 pytest tests passed; 31/31 Playwright E2E browser tests passed (including real CPU Ollama generations for both Markdown and HTML artifacts).

---

## Phase 7: UI Refinement & Interaction Design Polish
- **Objective**: Elevate aesthetic quality following Taste / Impeccable principles.
- **Execution**:
  - Refined zinc dark mode color palette (`#0A0A0B`, surface elevated `#27272A`, Lenny yellow-500 accents).
  - Added subtle micro-interactions, high-contrast focus rings (`focus-visible:ring-2 ring-yellow-500`), and accessible pill version tabs.
  - Ensured seamless responsive adaptation across desktop (1440x900), tablet (768x1024), and mobile (375x667).

---

## Phase 8: Production Hardening & Deployment Readiness
- **Objective**: Prepare repository for evaluation, handoff, and reproducible deployment.
- **Execution**:
  - Secret & environment hygiene audit: verified `.env` untracked, removed 5.6MB binary test traces from git index, reorganized `.env.example` with 768d embeddings.
  - Docker Compose hardening: added `extra_hosts` for host Ollama connectivity across Linux/WSL/Windows, added backend health checks, and configured service dependencies.
  - Multi-tier `/api/health` endpoint: evaluates application, database (`SELECT 1`), and Ollama tag availability, distinguishing `healthy` (HTTP 200), `degraded` (HTTP 200), and `unavailable` (HTTP 503).
  - Structured logging: enhanced `structlog` with log-level filtering, credential masking, and latency metrics (`retrieval_latency_ms`, `generation_latency_ms`, `total_latency_ms`).
  - Created comprehensive `docs/runbook.md` and `backend/scripts/test_basic_integration.py`.
- **Verification**:
  - Backend tests: 36/36 PASSED in 1.24s.
  - Basic integration check: 6/6 PASSED (Health, Session, Grounded QA, Message Persistence, Small Artifact, REST Persistence).
  - Health check: HTTP 200 `healthy`.
