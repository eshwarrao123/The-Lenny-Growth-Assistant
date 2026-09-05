# The Lenny Growth Assistant — Operational Runbook

This runbook provides step-by-step procedures for operating, diagnosing, and recovering the Lenny Growth Assistant in production and local evaluator environments.

---

## 1. System Topology & Architecture Quick Reference

```
[ Browser Client ]
       │
       ▼ (HTTP / SSE on :3000 -> :8000)
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose Network (lenny-network)                      │
│                                                             │
│   ┌───────────────┐     HTTP/SSE      ┌─────────────────┐   │
│   │ lenny-frontend│ ────────────────> │  lenny-backend  │   │
│   │ (Next.js :3000│                   │  (FastAPI :8000)│   │
│   └───────────────┘                   └────────┬────────┘   │
│                                                │            │
│               PostgreSQL asyncpg :5432         │            │
│               ┌────────────────────────────────┘            │
│               ▼                                             │
│       ┌───────────────┐                                     │
│       │ lenny-postgres│                                     │
│       │  (+ pgvector) │                                     │
│       └───────────────┘                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼ (host.docker.internal:11434)
             ┌─────────────────────┐
             │ Host-Based Ollama   │
             │ - qwen2.5:7b        │
             │ - nomic-embed-text  │
             └─────────────────────┘
```

---

## 2. Standard Startup Workflow

### Option A: Complete Docker Compose Stack (Recommended)
```bash
# 1. Start all infrastructure and application services
docker compose up -d

# 2. Inspect running container health status
docker compose ps
```

### Option B: Local Hybrid Development
```bash
# 1. Start database container
docker compose up -d postgres

# 2. Run backend migrations
cd backend
python -m alembic upgrade head

# 3. Start backend API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start frontend (in a separate terminal)
cd ../frontend
npm run dev
```

---

## 3. Health & Status Verification

### Inspecting `/api/health`
Query the health check endpoint:
```bash
curl -s http://localhost:8000/api/health | jq .
```

#### Expected Healthy Response (HTTP 200)
```json
{
  "status": "healthy",
  "application": "ok",
  "db": "ok",
  "ollama": "ok",
  "openai": "missing_key",
  "components": {
    "database": {
      "status": "ok"
    },
    "ollama": {
      "status": "ok",
      "model": "qwen2.5:7b",
      "embedding_model": "nomic-embed-text",
      "reachable": true,
      "chat_model": true,
      "embed_model": true
    },
    "openai": {
      "status": "missing_key"
    }
  },
  "environment": "development"
}
```

### Operational Status Semantics
- **`healthy` (HTTP 200)**: Database is reachable and Ollama is reachable with required chat and embedding models installed.
- **`degraded` (HTTP 200)**: Database is reachable, but Ollama is missing one model, or optional cloud providers are unconfigured. Chat QA can still operate with degraded functionality.
- **`unavailable` (HTTP 503)**: Primary PostgreSQL database is unreachable. Immediate remediation required.

---

## 4. Common Failure Modes & Remediation

### Failure Mode 1: Ollama Service Unavailable or Model Missing
**Symptoms**:
- `/api/health` returns `"ollama": "unavailable"` or `"status": "degraded"`.
- Chat queries return SSE `error` event: `{"code": "provider_unavailable"}`.

**Root Causes**:
1. Ollama daemon is not running on host port 11434.
2. Required model (`qwen2.5:7b` or `nomic-embed-text`) has not been pulled.
3. Linux/Docker container networking cannot reach `host.docker.internal`.

**Remediation**:
```bash
# Verify Ollama is running on the host
curl http://localhost:11434/api/tags

# Pull required models if missing
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# For Linux Docker hosts, ensure docker-compose.yml has:
# extra_hosts:
#   - "host.docker.internal:host-gateway"
```

---

### Failure Mode 2: Database Connection Failure
**Symptoms**:
- `/api/health` returns HTTP 503 with `"db": "unavailable"`.
- FastAPI startup hangs or logs `ConnectionRefusedError`.

**Remediation**:
```bash
# 1. Check if postgres container is running
docker compose ps postgres

# 2. Inspect postgres container logs
docker compose logs postgres --tail 50

# 3. Restart container if stopped
docker compose restart postgres

# 4. Verify port 5432 is not occupied by a local PostgreSQL service
netstat -ano | findstr 5432  # Windows
lsof -i :5432               # macOS / Linux
```

---

### Failure Mode 3: Migration Drift or Schema Mismatch
**Symptoms**:
- Logs report `relation "episodes" does not exist` or `column does not exist`.

**Remediation**:
```bash
cd backend

# Inspect current migration version
python -m alembic current

# Upgrade to latest schema
python -m alembic upgrade head

# Validate pgvector extension and table structures
python scripts/verify_pgvector.py
```

---

### Failure Mode 4: Re-running Knowledge Base Ingestion
**Symptoms**:
- Vector retrieval returns empty results.
- `verify_stored_data.py` shows 0 chunks or missing embeddings.

**Remediation**:
```bash
cd backend

# Step 1: Sync / download raw transcript repository
python scripts/download_transcripts.py

# Step 2: Ingest with idempotent skipping (skips existing episodes)
python scripts/ingest.py --concurrency 8

# To completely wipe and rebuild knowledge base cleanly:
python scripts/ingest.py --refresh --concurrency 8

# Step 3: Verify stored data integrity
python scripts/verify_stored_data.py
python scripts/test_vector_retrieval.py
```

---

### Failure Mode 5: Artifact Rendering or Generation Interruption
**Symptoms**:
- Artifact generation halts mid-stream or viewer reports `Execution error`.

**Diagnostic Steps**:
1. Check backend logs for `chat_stream_failed` event and error code:
   ```bash
   docker compose logs backend | grep "chat_stream_failed"
   ```
2. Verify artifact size did not exceed the 5MB payload limit (`ARTIFACT_MAX_BYTES`).
3. Check browser developer console: Sandboxed iframes run under `sandbox="allow-scripts"` without `allow-same-origin`. Any script attempting to access parent cookies, storage, or parent DOM will cleanly throw a `SecurityError` without crashing the application.
4. Use the "Raw" view button in the Artifact Viewer toolbar to inspect exact streamed source.

---

## 5. Automated Verification Checklist

Run this command sequence to verify an operational deployment:

```bash
# 1. Backend test suite (36/36 tests)
cd backend
python -m pytest tests/ -v

# 2. Automated basic integration check (health, QA, artifact, persistence)
python scripts/test_basic_integration.py

# 3. Frontend Playwright E2E verification
cd ../frontend
npx playwright test tests/e2e/core.spec.ts tests/e2e/security.spec.ts tests/e2e/accessibility.spec.ts
```
