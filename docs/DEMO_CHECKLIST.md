# Lenny Growth Assistant — Demo Recording Pre-Flight Checklist

Ensure all items are checked and verified before pressing record.

---

## 📹 Video & Audio Setup
- [ ] **Camera Enabled**: Web camera positioned cleanly with proper lighting and video overlay in the corner of screen recording software (e.g. Loom, OBS, or QuickTime).
- [ ] **Audio Quality**: Microphone tested, clear input level, background noise eliminated.
- [ ] **Screen Resolution**: Display set to 1920x1080 (1080p) or 1440x900 for optimal text readability without UI scaling distortion.

---

## 🖥️ System & Service Readiness
- [ ] **Ollama Running**: Daemon active on `http://localhost:11434`.
  - [ ] Model `qwen2.5:7b` verified via `ollama list`.
  - [ ] Model `nomic-embed-text` verified via `ollama list`.
- [ ] **PostgreSQL Running**: Docker container `lenny-postgres` active on `localhost:5432` with 303 episodes and ~14,000 embedded chunks.
- [ ] **Backend API Running**: FastAPI active on `http://localhost:8000` with `HEALTHY` status verified at `http://localhost:8000/api/health`.
- [ ] **Frontend Dev Server Running**: Next.js active on `http://localhost:3000`.

---

## 🔒 Security & Hygiene
- [ ] **No Secrets Visible**: Verify terminal history and `.env` files are hidden. No actual API keys or passwords visible on screen.
- [ ] **Clean Browser Environment**: Browser opened in fresh window on `http://localhost:3000` with developer tools closed or positioned cleanly.
- [ ] **Pre-Warmed Model Cache**: Execute one quick test query in background prior to recording so Ollama weights (`qwen2.5:7b`) are loaded into RAM for fast TTFT during recording.

---

## 📋 Workspace & Window Layout
- [ ] **Main Window**: Browser displaying Next.js interface (`http://localhost:3000`).
- [ ] **Secondary Window**: Terminal window positioned on side showing `ollama list` or `docker compose ps`.
- [ ] **Demo Session Prepared**: Fresh session created via "New Chat" button.

---

## 🎯 Script Milestones Verification
- [ ] Milestone 1 (0:00–0:20): Problem & Product Introduction.
- [ ] Milestone 2 (0:20–0:55): Grounded Q&A + Citation Card.
- [ ] Milestone 3 (0:55–1:20): Follow-up Context & Session State.
- [ ] Milestone 4 (1:20–1:45): Ship 30 for 30 Skill Essay Generation.
- [ ] Milestone 5 (1:45–2:15): Artifact Viewer (Markdown + HTML sandbox isolation).
- [ ] Milestone 6 (2:15–2:40): Local Ollama Engine & Provider Flexibility.
- [ ] Milestone 7 (2:40–3:00): Engineering Trade-offs & Wrap-up.

---
