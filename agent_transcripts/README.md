# Agent Interaction Transcripts & Engineering Audit Log

This directory contains real, unedited engineering logs and transcripts produced by autonomous AI pair-programming agents during the design, implementation, debugging, and verification of **The Lenny Growth Assistant** across all phases.

---

## Overview of Development Phases

| Phase | Focus Area | Key Decisions & Technical Milestones | Failures & Corrections |
|---|---|---|---|
| **Phase 1** | Scoping, PRD, Technical Specifications | Defined system architecture, PostgreSQL 16 + pgvector schema, Ollama local-first runtime, and strict prompt injection defenses. | Evaluated cloud vs. local tradeoff; selected Ollama `qwen2.5:7b` + `nomic-embed-text` for zero-cost offline reproducibility. |
| **Phase 2** | Database Schema & Alembic Migrations | Implemented UUID primary keys, HNSW cosine similarity index (`vector_cosine_ops`), cascading session deletions, and migration head `002_phase2_schema`. | Addressed Alembic transactional DDL compatibility and dynamic WSL2 interface IP changes. |
| **Phase 3** | Knowledge Base Ingestion Pipeline | Ingested 303 episodes (~10,588 transcript chunks) using batch embeddings via Ollama `/api/embed` with token sliding-window chunking. | Handled malformed YAML frontmatter across raw podcast transcripts without aborting ingestion. |
| **Phase 4** | Grounded Q&A Assistant Service | Built FastAPI backend, async SQLAlchemy sessions, RAG retrieval engine, and SSE streaming with verified timestamp citations. | Resolved ephemeral Docker networking binding by switching to host localhost / host-gateway. |
| **Phase 5** | Skill Routing & Ship 30 for 30 Writing | Implemented `SkillRouter` with deterministic pattern matching, slash commands (`/ship30`), and anaphora resolution for 1,250-word atomic essays. | Calibrated local 7B model token generation budget and word count tolerance window (850–1,600 words). |
| **Phase 6** | Interactive Artifact System & Targeted Fixes | Implemented side-by-side split pane, sandboxed HTML `<iframe>`, version switcher, DOMPurify markdown sanitization, copy/download controls, and 5MB payload safeguard. | **Multiple major debugging corrections** (see below): PostCSS config syntax, disk ENOSPC cleanup, a11y accessible names, Ollama streaming token extraction, and mobile drawer timing. |
| **Phase 7** | UI Refinement & Interaction Polish | Refined dark-mode design system, high-contrast focus rings, typography, and responsive breakpoints. | Verified 31/31 Playwright tests across chromium viewport configurations. |
| **Phase 8** | Production Hardening & Deployment Readiness | Implemented multi-tier `/api/health` endpoint, structured logging with latency metrics, Docker Compose networking hardening, and comprehensive runbook. | Pruned 5.6MB binary test traces from git index; standardized .env.example configuration. |

---

## Detailed Chronology of Failed Attempts and Corrections

The assignment explicitly requires documenting genuine failed attempts and corrections during the build process:

### 1. PostCSS Configuration & Tailwind Class Crash (Phase 6)
- **Failure**: The Next.js frontend threw HTTP 500 compilation errors (`The border-border class does not exist`).
- **Root Cause**: `frontend/postcss.config.js` specified `{ configFile: ... }` instead of `{ config: ... }`. PostCSS silently loaded the default Tailwind configuration without custom project colors.
- **Correction**: Changed key to `config` in `postcss.config.js`, defined explicit `borderColor` in `tailwind.config.js`, and added fallback CSS variable declarations in `globals.css`.

### 2. Disk Space Exhaustion (`ENOSPC`) During Browser Testing (Phase 6)
- **Failure**: `npm` and `next dev` crashed with `Error: ENOSPC: no space left on device, write`.
- **Root Cause**: Accumulation of Windows diagnostic logs (`DiagOutputDir`) and npm cache consumed all remaining disk space on drive C.
- **Correction**: Executed cleanup commands purging stale diagnostic directories and npm caches, immediately recovering >11.8 GB of free storage.

### 3. Artifact Viewer Reopen State Loss (`accessibility.spec.ts:47`)
- **Failure**: After closing the Artifact Viewer pane, clicking "View Artifact" on a message card failed to reopen the viewer.
- **Root Cause**: Closing the viewer wiped component state, and clicking "View Artifact" attempted a REST fetch for an artifact ID that was either stubbed or still in-flight in PostgreSQL.
- **Correction**: Added an in-memory `artifactsCacheRef` in `src/app/page.tsx` caching incoming chunks on `artifact_start` and `artifact_done`. `handleArtifactClick` was updated to check local memory cache first before hitting the database.

### 4. Ollama Provider Token Dropping in Artifact Skill (`artifact.py`)
- **Failure**: Real Ollama generation streamed SSE start and status events, but generated artifact content remained completely empty.
- **Root Cause**: `backend/app/services/skills/artifact.py` checked `if chunk.get("type") == "content"`. However, both `OllamaProvider` and `OpenAIProvider` yield chunks formatted as `{"event": "token", "data": {"content": ...}}`. Real provider tokens were completely ignored!
- **Correction**: Updated `artifact.py` to extract content from both `event == "token"` (`chunk["data"]["content"]`) and `type == "content"`.

### 5. Mobile Drawer Bounding Box Timing Race (`responsive.spec.ts:78`)
- **Failure**: Playwright assertion failed on mobile drawer opening (`Received: -263px`, expected `0px`).
- **Root Cause**: The `<aside>` navigation bar had `transition-all duration-200`. When the hamburger button was clicked, Playwright queried the bounding box mid-animation.
- **Correction**: Scoped transitions to desktop/tablet (`md:transition-all md:duration-200`) so the mobile drawer immediately snaps between `-translate-x-full` and `translate-x-0` without animation delay.

### 6. Tablet Split-Pane Minimum Width Collisions (`responsive.spec.ts:59`)
- **Failure**: At 768px tablet viewport, the artifact split pane measured 191px, failing the assertion requiring `> 250px`.
- **Root Cause**: A percentage-based split (40%) at 768px width minus padding resulted in too narrow an artifact container.
- **Correction**: Added explicit CSS flex sizing: `.chat-pane-host` (`flex: 1 1 0%; min-width: 0;`) and `.artifact-pane-host` (`min-width: 260px; max-width: 70%; flex-shrink: 0;`).

---

## Verification Records

All transcripts and verification runs are backed by automated tests:
- **Backend**: `pytest` 36/36 tests passing in `tests/`.
- **Frontend**: Playwright 31/31 tests passing across `accessibility.spec.ts`, `copy-download.spec.ts`, `core.spec.ts`, `responsive.spec.ts`, `security.spec.ts`, and `real-ollama.spec.ts`.
- **Integration**: `python scripts/test_basic_integration.py` passing all 6 integration checkpoints.
