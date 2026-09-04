# The Lenny Growth Assistant — Product Requirements Document (PRD)

**Document Version:** 1.0.0  
**Phase:** Phase 1 — Forward Deployment Discovery & Product Requirements  
**Status:** Approved for Implementation  
**Role Context:** Forward Deployed Engineer / Lead Solutions Architect  

---

## 1. Executive Summary

**The Lenny Growth Assistant** is an internal, AI-powered growth knowledge system that transforms the unstructured knowledge base of [Lenny's Podcast transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) (200+ interviews with premier product leaders, founders, and growth practitioners) into a trustworthy, grounded conversational assistant and deliverable generation engine.

Unlike generic conversational wrappers that hallucinate advice or cite vague platitudes, the Lenny Growth Assistant is designed for zero-trust enterprise rigor:
1. **Verifiably Grounded Answers**: Every claim attributes specific insights to named guests, episodes, and transcript excerpts. When the archive lacks sufficient depth on a question, the assistant explicitly declines to answer rather than fabricating advice.
2. **Direct-to-Deliverable Workflow**: Beyond answering questions, the system converts conversation threads into concrete, formatted outputs: structured frameworks, actionable checklists, **Ship 30 for 30** atomic essays (~1,250 words), and interactive HTML/CSS calculations or visual teardowns rendered inside a sandboxed, zero-trust in-app Artifact Viewer.
3. **Hybrid Model Architecture**: Built to run entirely locally using Ollama (`qwen2.5:7b` / local embeddings) for zero cloud cost and offline evaluation, while supporting seamless toggling to frontier cloud models (OpenAI `gpt-4o-mini` / `gpt-4o`) when maximum reasoning depth or expanded context is required.

---

## 2. Forward Deployment Discovery Brief

### 2.1 Engagement Background
The client seeks an internal AI tool to democratize product and growth institutional knowledge distilled from world-class practitioners (e.g., Elena Verna, Brian Balfour, Casey Winters, Gustaf Alströmer, Sean Ellis). Today, this knowledge exists as raw conversational transcripts across 200+ episodes. Operators cannot effectively utilize it because the knowledge is locked inside long, conversational audio dialogues and fragmented files.

### 2.2 Key Discovery Takeaways
* **Knowledge Retrieval Alone Is Insufficient**: Merely finding what a guest said does not solve the operator's problem. Operators require *synthesis across guests* and *translation into deliverables* (e.g., converting a discussion on retention into an onboarding audit checklist or a leadership strategy memo).
* **The "Hallucination Barrier" to Adoption**: If an internal tool produces an inaccurate attribution (e.g., attributing Brian Balfour's growth loop model to an unrelated founder, or inventing non-existent quotes), users will immediately lose trust and abandon the platform.
* **Dual Runtime Need**: The product must run friction-free on a single machine for evaluation and local offline privacy (via Ollama), while providing a clean pathway to cloud LLMs for production throughput and complex multi-turn reasoning.
* **Zero Infrastructure Friction for End Users**: The user experience must be: **Ask $\rightarrow$ Understand $\rightarrow$ Refine $\rightarrow$ Create $\rightarrow$ Reuse**. The operator should never need to manage embeddings, vector indices, chunking strategies, or model parameters.

---

## 3. User & Persona Definition

### 3.1 Primary Persona: The Growth Product Manager (Growth PM)
* **Title**: Senior / Staff Growth Product Manager, Head of Growth
* **Context**: Working at a B2B SaaS, consumer subscription, or PLG marketplace company. Responsible for activation, conversion, retention loops, monetization, and growth experimentation.
* **Daily Workflow**:
  - Investigates funnel bottlenecks (e.g., "Why is Day 7 retention dropping for self-serve users?").
  - Prepares experiment design briefs, PRDs, and onboarding teardowns.
  - Presents growth models and strategic bets to leadership and cross-functional teams (engineering, design, marketing).
* **Why Primary**: Growth PMs have the highest intersection of theoretical inquiry ("How did Miro structure their freemium tier?") and tactical deliverable requirements ("Draft an experimentation memo comparing reverse-trial vs freemium based on Elena Verna's benchmarks"). Serving this persona ensures both retrieval depth and deliverable generation are rigorously exercised.

### 3.2 Secondary Personas

| Persona | Role & Context | Core Use Case |
|---|---|---|
| **Early-Stage Founder / Operator** | Seed/Series A founder wearing PM and growth hats without dedicated growth staff | Retrieves first-principles advice on finding PMF, pricing validation, and acquiring the first 1,000 customers. |
| **Product Leader (VP/CPO)** | Executive managing multiple product squads | Benchmarks team org design, career progression frameworks, and strategic positioning for board decks. |
| **Evaluator / Technical Reviewer** | Assessing this take-home project for engineering rigor and UX excellence | Validates local Ollama execution, RAG grounding precision, test coverage, artifact sandboxing, and codebase hygiene. |

---

## 4. Problem Statement

1. **Volume & Fragmentation**: The transcript archive spans 200+ episodes, representing over 400 hours of conversational audio transcribed into millions of unstructured words. Manual search is slow, keyword-dependent, and misses conceptual context.
2. **Conversational Obfuscation**: Key growth insights are rarely stated as clean bullet points; they are buried in anecdotes, banter, tangents, and conversational back-and-forths across 90-minute interviews.
3. **Cross-Episode Synthesis Friction**: No manual workflow allows an operator to easily compare contrasting methodologies (e.g., Casey Winters on SEO growth loops vs. Elena Verna on product-led sales) without days of reading.
4. **Deliverable Production Deficit**: Moving from an insight to an actionable team deliverable (strategy essay, audit checklist, ROI calculator) requires substantial synthesis time from scratch.
5. **AI Hallucination & Citation Skepticism**: Generic public LLMs fabricate advice, confuse guest attributions, or produce generic platitudes that lack the tactical authority of Lenny's actual interviewees.

---

## 5. Job To Be Done (JTBD)

> **When I am** diagnosing or solving an ambiguous product or growth challenge (such as fixing activation friction, architecting growth loops, or restructuring onboarding),  
> **I want to** instantly retrieve authoritative, battle-tested advice from Lenny's expert guest archive, synthesize contrasting viewpoints, and transform those insights into structured, defensible deliverables (frameworks, Ship 30 essays, checklists, interactive calculators),  
> **So that I can** validate our team's strategy against world-class operator benchmarks and align cross-functional stakeholders in hours instead of days without fearing AI hallucination.

---

## 6. Goals & Non-Goals

### 6.1 Goals
* **Authoritative Grounding**: Ensure $\ge 90\%$ of factual assertions are directly backed by retrieved transcript chunks with clickable episode/guest citations.
* **Explicit Negative Fallback**: Gracefully decline to answer out-of-domain or unrepresented queries rather than guessing.
* **Frictionless Deliverables**: Provide single-click transformation of conversation threads into structured Markdown artifacts and sandboxed interactive HTML artifacts.
* **Ship 30 for 30 Skill**: Built-in capability to generate high-impact, ~1,250-word atomic essays adhering to the Ship 30 methodology (hook, rhythm, skimmable headings, grounded takeaways).
* **Zero-Trust Artifact Sandboxing**: Strict iframe isolation preventing generated HTML from accessing cookies, parent DOM, or local storage.
* **Local & Cloud Interoperability**: Support 100% offline local execution via Ollama (`qwen2.5:7b`) with smooth toggling to OpenAI.
* **Production-Grade Ergonomics**: Real-time streaming UI, persistent sessions, Dockerized PostgreSQL + pgvector, structured logging, health checks, and end-to-end automated test suites.

### 6.2 Non-Goals
* **No Real-Time Audio / Video Transcription**: Ingesting live YouTube streams or running local Whisper transcription is out of scope; the system relies on the provided transcript repository.
* **No Complex Enterprise Multi-Tenancy / RBAC**: The application assumes a single-tenant or internal team environment; SSO and enterprise user management are excluded for MVP.
* **No Autonomous Web Crawling**: The assistant does not browse the live internet; its domain is strictly the curated transcript corpus.
* **No Silent / Hidden Model Fallback**: The system will not automatically switch from local to paid cloud models without explicit user awareness and configuration.

---

## 7. Success Metrics & Validation Targets

| Metric | Target | Tier | Measurement Methodology |
|---|---|---|---|
| **Citation Grounding Accuracy** | $\ge 90\%$ | MVP Target | Automated evaluation of 20 benchmark Q&A pairs; verification that claims directly trace to cited transcript excerpts. |
| **Negative Fallback Precision** | $100\%$ | MVP Target | Automated evaluation on 10 out-of-domain / negative-control prompts; system must explicitly decline. |
| **Artifact Security (XSS Isolation)** | $0$ Vulnerabilities | MVP Target | Playwright security test injecting malicious scripts (`parent.cookie`, storage access); verifying iframe sandbox blocks access. |
| **Time to First Token (TTFT) - Cloud** | $< 1.5\text{ s}$ | MVP Target | Measured at frontend from query submission to first streaming token received over SSE. |
| **Time to First Token (TTFT) - Local** | $< 4.0\text{ s}$ | Validation Target | Ollama `qwen2.5:7b` execution on host GPU (or $< 7.0\text{ s}$ on host CPU). |
| **Session Persistence Integrity** | $100\%$ | MVP Target | Refreshing browser or reopening session restores full multi-turn history and associated artifacts. |
| **Docker Compose Bootstrap** | $< 45\text{ s}$ | MVP Target | `docker compose up` starts healthy PostgreSQL/pgvector and application backend from clean state. |

---

## 8. Assumptions

1. **Transcript Repository Completeness**: We assume the markdown files in `ChatPRD/lennys-podcast-transcripts` contain adequate episode metadata (guest name, episode title, video ID, publish date) in frontmatter or headers to enable accurate source attribution.
2. **Single-Tenant / Internal Knowledge Context**: We assume the MVP is operated locally or within an internal team network; authentication and user account management are not required by the client brief.
3. **Local Machine Hardware Constraints**: We assume the evaluator's machine runs a modern multi-core CPU with at least 16GB RAM, capable of running quantized 7B parameter models via Ollama.
4. **Untrusted Generated Content**: We assume that any HTML generated by an LLM could contain dangerous or malformed scripts; therefore, client-side rendering must treat all artifact code as completely untrusted.
5. **Model Variance**: We assume local 7B models will produce shorter, more concise summaries than frontier cloud models, requiring well-engineered system prompts to meet the ~1,250-word Ship 30 essay target.

---

## 9. MVP Scope (MoSCoW Prioritization)

```
┌────────────────────────────────────────────────────────────────────────┐
│                               MVP SCOPE                                │
│                                                                        │
│  [MUST HAVE]                                                           │
│  • pgvector transcript ingestion & semantic chunk retrieval            │
│  • Grounded RAG with guest/episode citations                           │
│  • Explicit negative fallback for ungrounded queries                   │
│  • Persistent chat sessions & multi-turn message history in Postgres   │
│  • SSE streaming token responses                                       │
│  • Local Ollama (qwen2.5:7b) + Cloud (OpenAI) provider switching       │
│  • Ship 30 for 30 skill (~1,250-word structured essays)                │
│  • In-app split-pane Artifact Viewer (Markdown + sandboxed HTML)       │
│  • Docker Compose deployment & health checks                           │
│  • Automated unit (pytest) and E2E (Playwright) test suites            │
│                                                                        │
│  [SHOULD HAVE]                                                         │
│  • Hybrid retrieval (dense vector + BM25 keyword matching)             │
│  • Artifact version history toggle (v1, v2)                            │
│  • Raw code / preview toggle in Artifact Viewer                        │
│                                                                        │
│  [COULD HAVE]                                                          │
│  • Anthropic Claude provider integration                               │
│  • Direct YouTube timestamp deep-links                                 │
│  • Download artifact as PDF / Markdown file                            │
│                                                                        │
│  [OUT OF SCOPE]                                                        │
│  • User authentication / multi-tenancy / RBAC                          │
│  • Live audio transcription / Whisper pipeline                         │
│  • Autonomous internet browsing                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Key User Flows

### Flow 1: First-Time User Experience
1. User navigates to application URL (`http://localhost:3000`).
2. System displays clean dark-themed interface with collapsible sidebar, active session empty state, and suggested prompt starters (e.g., *"How do I design a B2B onboarding flow based on Elena Verna's advice?"*).
3. Header clearly displays active provider status: `Local (Ollama: qwen2.5:7b)` or `Cloud (OpenAI)`.

### Flow 2: Asking a Grounded Growth Question
1. User enters a growth question in the prompt input.
2. UI displays immediate loading state and streams response tokens in real time via Server-Sent Events (SSE).
3. System retrieves relevant transcript chunks using pgvector cosine similarity.
4. Response streams markdown text, followed by structured Source Citation Cards (Guest Name, Episode Title, YouTube link, and transcript excerpt preview).
5. User clicks a citation card to inspect the exact quoted transcript context.

### Flow 3: Multi-Turn Exploration & Context Preservation
1. User asks a follow-up: *"How does Brian Balfour's perspective on that differ?"*
2. System maintains session message history, retrieves comparative chunks for Brian Balfour, and streams a comparative analysis highlighting nuances and contrasting approaches.

### Flow 4: Out-of-Domain / Insufficient Information Fallback
1. User enters a query not represented in Lenny's podcast (e.g., *"How do I configure quantum computing qubits?"* or an obscure niche topic).
2. RAG similarity score falls below the confidence threshold ($< 0.65$).
3. Assistant responds with standard fallback: *"The Lenny Podcast archive does not contain sufficient information on this topic to provide a grounded answer. Would you like to explore related topics in product management, growth loops, or hiring?"*
4. No fake sources or fabricated quotes are presented.

### Flow 5: Model / Provider Switching
1. User clicks the Model Switcher in the top header or settings drawer.
2. Selects between **Local (Ollama)** and **Cloud (OpenAI)**.
3. System verifies provider availability:
   - If Ollama is chosen and reachable, status displays a green health indicator.
   - If Cloud is chosen but `OPENAI_API_KEY` is not set, UI displays a non-blocking configuration prompt.
4. Active provider is saved in session state; subsequent queries route to the selected provider.

### Flow 6: Generating a Ship 30 for 30 Essay
1. In an active conversation discussing a growth topic, user triggers the skill via UI button or typing `/ship30`.
2. Backend routes request to the dedicated `Ship30Skill` service with the active transcript context.
3. System streams an atomic essay adhering to Ship 30 standards (~1,250 words, magnetic hook, bold section headers, short rhythmic paragraphs, grounded quotes, actionable framework).
4. System automatically encapsulates the output as a Markdown Artifact and opens the split-pane Artifact Viewer.

### Flow 7: Generating an Interactive HTML Artifact
1. User requests: *"Generate an interactive CAC:LTV calculator based on David Sacks' startup benchmarks discussed in the podcast."*
2. Backend generates self-contained HTML/CSS/JS code wrapped in `<artifact type="html">` tags.
3. The Artifact Viewer slides in from the right (taking 40–50% of the viewport).
4. The HTML is rendered inside a sandboxed `<iframe>` (`sandbox="allow-scripts"`).
5. User can interact with sliders/inputs directly inside the viewer.

### Flow 8: Artifact Iteration & Versioning
1. With the calculator open, user prompts in chat: *"Add a sensitivity toggle for monthly vs annual churn."*
2. Assistant updates the artifact, increments version to `v2`, and refreshes the sandbox.
3. User can click version pills (`v1`, `v2`) in the artifact toolbar to compare changes.

### Flow 9: Responsive Artifact Viewing (Mobile / Small Screen)
1. On viewport width $< 768\text{px}$, split-pane transforms into a slide-over drawer / bottom sheet.
2. User can toggle between chat view and artifact view with a single tap.

### Flow 10: Session Persistence & Reopening
1. User closes browser tab and reopens later.
2. Session sidebar loads previous conversations from PostgreSQL.
3. Selecting a session restores all messages, citations, and generated artifacts in their exact prior state.

### Flow 11: Error & Offline Handling
1. If Ollama terminates or becomes unresponsive during inference, stream aborts cleanly.
2. UI displays inline error card: *"Inference failed: Local Ollama service not reachable. Ensure Ollama is running (`ollama serve`) or switch to Cloud provider."*
3. A **Retry** button allows re-submitting the prompt without re-typing.

### Flow 12: View / Update / Close Artifact Flow
1. While an artifact is open, user clicks the "Close" button ($X$) or hits `Esc`.
2. Artifact pane smoothly collapses (150ms animation), returning chat pane to full viewport.
3. A persistent badge inside the corresponding chat message reads `Artifact: CAC:LTV Calculator (v2) [Open]`.
4. User clicks the badge at any point to reopen the artifact viewer in its last known state.

---

## 11. Functional Requirements

### 11.1 Chat & RAG Engine
* **FR-1.1**: The backend must chunk podcast transcripts into semantically coherent segments (approx. 400–600 tokens with 100-token overlap) preserving episode metadata.
* **FR-1.2**: Vector similarity search must utilize PostgreSQL `pgvector` with cosine distance (`vector_cosine_ops`).
* **FR-1.3**: The prompt builder must inject retrieved transcript context into the system prompt with strict instructions: *"Rely only on provided context. If context is insufficient, state so clearly."*
* **FR-1.4**: All factual claims derived from retrieved context must cite the episode title and guest name.

### 11.2 Persistence & Session Management
* **FR-2.1**: All sessions and messages must be persisted in PostgreSQL.
* **FR-2.2**: Users can create, view, rename, and delete chat sessions from the sidebar.
* **FR-2.3**: Message objects must record: role, content, timestamp, citations (JSONB array), and associated artifact IDs.

### 11.3 Streaming Protocol
* **FR-3.1**: Token streaming must use standard Server-Sent Events (SSE) via FastAPI `StreamingResponse`.
* **FR-3.2**: Stream chunks must transmit structured JSON events: `token`, `sources`, `artifact_start`, `artifact_chunk`, `artifact_done`, and `error`.

### 11.4 LLM Provider Abstraction
* **FR-4.1**: Providers must implement a unified `BaseLLMProvider` interface with methods: `generate_stream()` and `generate_embeddings()`.
* **FR-4.2**: Supported providers: `OllamaProvider` (default local) and `OpenAIProvider` (cloud).
* **FR-4.3**: Provider switching must take effect immediately on subsequent requests without server restarts.

---

## 12. Grounding & Trust Requirements

```
                     User Query
                         │
                         ▼
              Dense Embedding Query
                         │
                         ▼
             pgvector Cosine Search
                         │
                         ▼
            Score >= Threshold (0.65)?
                    /         \
                 YES           NO
                 /               \
                ▼                 ▼
      Construct RAG Prompt     Explicit Fallback:
      with Transcript Chunks   "Archive does not contain
                │               sufficient information..."
                ▼
       Stream Answer with
       Clickable Citations
```

1. **Thresholded Retrieval**: If top cosine similarity score is below $0.65$, the system triggers the explicit fallback response.
2. **Citation Granularity**: Citations must include:
   - Guest Name
   - Episode Title
   - Video / Episode Link
   - Relevant Transcript Excerpt (1–3 sentences)
3. **Multi-Perspective Synthesis**: If two guests provide conflicting advice (e.g., gating features vs. full freemium), the prompt requires presenting both perspectives clearly attributed to their respective sources rather than forcing artificial consensus.

---

## 13. Ship 30 for 30 Skill Requirement

The **Ship 30 for 30** capability is treated as a first-class, reusable product skill, not just a casual prompt tweak.

### 13.1 Editorial Anatomy
Every Ship 30 essay generated by the assistant must adhere to these editorial standards:
1. **Target Word Count**: Approximately $1,250$ words ($\pm 150$ words).
2. **The Hook (First 50–75 words)**: A provocative, problem-agitating opening that states a counterintuitive truth, identifies a common founder/PM trap, and promises a clear outcome.
3. **Formatting & Visual Rhythm**:
   - Short 1–2 sentence paragraphs.
   - Distinct, bolded section headings that convey the core point even if the reader only skims.
   - Bulleted frameworks with bold lead-in phrases.
   - No dense, academic walls of text.
4. **Grounded Substance**: Incorporates quotes and concrete case studies directly from Lenny's guests.
5. **The Actionable Takeaway**: Concludes with a bulleted, step-by-step implementation framework the reader can execute this week.

### 13.2 System Architecture
* Encapsulated as an independent skill module (`backend/app/services/skills/ship30.py`).
* Accessible via dedicated UI button or `/ship30` slash command.
* Output is automatically piped into the Artifact Viewer as a formatted Markdown artifact.

---

## 14. Artifact Capability & Viewer

### 14.1 Purpose
Eliminate context-switching friction. When an operator asks for an analysis, essay, or calculator, the deliverable renders immediately alongside the conversation in a clean split pane.

### 14.2 Supported Artifact Formats
* **Markdown**: Essays, strategy memos, audit checklists, PRDs, interview guides.
* **HTML/CSS/JS**: Interactive ROI/growth calculators, interactive funnel charts, visual teardowns.

### 14.3 Viewer States & UX Behavior

| State | Split Pane (Desktop) | Drawer (Mobile) | Controls Active |
|---|---|---|---|
| **Empty / Closed** | Hidden; chat occupies 100% width | Closed | "Open Artifacts" button if session has artifacts |
| **Generating** | Slides in from right (45% width); skeleton loader with pulsing badge | Slide-up modal; loading indicator | Cancel generation button |
| **Available / Ready** | Split-pane active; rendered preview | Full-screen modal with tab bar | Copy Raw, Download, View Source, Close |
| **Updated (v2+)** | Automatically reloads with latest version | Updates active modal | Version switcher tabs (`v1`, `v2`, `v3`) |
| **Error Boundary** | Displays friendly error card with raw code toggle | Displays error alert | "Retry Generation", "View Raw Code" |

---

## 15. Model Provider Experience

### 15.1 Provider Matrix

| Feature | Local: Ollama (`qwen2.5:7b`) | Cloud: OpenAI (`gpt-4o-mini` / `gpt-4o`) |
|---|---|---|
| **Primary Use** | Evaluation demo, offline use, privacy | High-concurrency, maximum reasoning depth |
| **Cost** | $0.00 / completely free | API usage costs (BYO Key) |
| **First Token Latency** | ~2–5 seconds (hardware dependent) | ~0.8–1.5 seconds |
| **Context Window** | 8K–32K tokens | 128K tokens |
| **Setup Requirement** | Ollama running on host machine | `OPENAI_API_KEY` set in environment |

### 15.2 Graceful Error Handling
* **Ollama Offline**: Display banner: *"Cannot connect to Ollama at localhost:11434. Please verify `ollama serve` is running or select Cloud in settings."*
* **Missing API Key**: Display banner: *"OpenAI API Key not detected. Configure OPENAI_API_KEY in .env or switch to Local Ollama."*
* **Timeout**: If inference takes $> 30\text{ s}$, trigger graceful timeout with clear retry prompt.

---

## 16. Security & Trust Architecture

### 16.1 Untrusted HTML Sandboxing
* All HTML artifacts are rendered inside an `<iframe>` configured with:
  ```html
  <iframe sandbox="allow-scripts allow-forms" srcdoc="..." />
  ```
* **Critical Rule**: The attribute `allow-same-origin` is **strictly prohibited**.
* **Impact**: The sandboxed iframe executes in a unique null origin, preventing it from accessing:
  - Parent DOM / window
  - `document.cookie`
  - `localStorage` / `sessionStorage`
  - Network requests to parent origin APIs

### 16.2 Secret Isolation & Config
* No API keys or credentials stored in repository code or client-side bundles.
* Frontend only communicates with internal FastAPI proxy endpoints.
* Environment variables managed exclusively via `.env` (validated by Pydantic `BaseSettings`).

### 16.3 Prompt Injection Defense
* Transcript content retrieved from the database is tagged as untrusted data in system prompts using XML-style delimiters (`<transcript_context>...</transcript_context>`).
* System prompt explicitly instructs the LLM to ignore any instructions embedded inside the transcript text that attempt to override system behavior.

---

## 17. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Residual Concern |
|---|---|---|---|---|
| **Hallucination of Quotes / Data** | High | Medium | Strict system prompt constraints, cosine distance cutoff ($0.65$), mandatory quote extraction directly from chunks. | Evaluators asking highly obscure questions where chunks have partial match. |
| **Local Model Latency on CPU** | High | High | Default to quantized `qwen2.5:7b`; implement immediate SSE token streaming so user sees continuous progress; provide Cloud toggle. | Evaluators running on low-spec laptops with $< 16$GB RAM. |
| **XSS via Generated HTML Artifacts** | Critical | Low | Sandboxed `<iframe>` without `allow-same-origin`, CSP enforcement, client-side input sanitization. | Malicious links inside markdown rendering (mitigated via `rel="noopener noreferrer"`). |
| **Transcript Chunk Boundary Loss** | Medium | Medium | Implement sliding-window chunking (500 tokens with 100-token overlap) to avoid splitting key conversational insights. | Long multi-turn anecdotes spanning $> 1,000$ words. |
| **Ship 30 Essay Length Deficit on 7B Models** | Medium | Medium | Specialized prompt engineering with multi-stage structural guidance and target section lengths. | Smaller 7B models may occasionally produce ~900 words rather than 1,250. |

---

## 18. Architectural & Product Trade-offs

### Trade-off 1: Split-Pane Desktop Layout vs. Full-Screen Modal
* **Decision**: Split-pane layout (60% chat / 40% artifact).
* **Rationale**: The core value proposition is conversational iteration. The user must be able to read the artifact while typing refinement instructions in chat. Modals sever the conversational connection.

### Trade-off 2: Client-Side iframe `srcdoc` vs. Dedicated Subdomain Sandbox
* **Decision**: `srcdoc` with `sandbox="allow-scripts"` (without `allow-same-origin`).
* **Rationale**: Avoids the operational overhead of configuring multi-domain DNS/SSL for local Docker evaluation, while providing the exact same browser-enforced origin isolation.

### Trade-off 3: Server-Sent Events (SSE) vs. WebSockets
* **Decision**: Server-Sent Events (SSE) for token and artifact streaming.
* **Rationale**: LLM responses are fundamentally unidirectional streams. SSE operates natively over standard HTTP, works seamlessly through HTTP/2 and Docker proxies, reconnects automatically, and avoids WebSocket connection state overhead.

### Trade-off 4: Static Embedding vs. Full Model Reranking
* **Decision**: Single-stage dense vector retrieval via `pgvector` with cosine similarity for MVP.
* **Rationale**: Avoids introducing heavy cross-encoder models that would cripple local CPU/GPU performance on evaluator machines. Reranking is marked as a post-MVP enhancement.

---

## 19. Acceptance Criteria (Testable Given / When / Then)

### AC-1: Grounded Response with Citation
* **Given** a user query whose topic exists in the transcript archive (e.g., "Elena Verna on B2B product-led growth"),
* **When** the assistant processes the query,
* **Then** it streams a grounded response citing Elena Verna with episode title, and displays citation cards with direct transcript excerpts.

### AC-2: Negative Fallback for Unrepresented Queries
* **Given** a query with no relevant podcast data (e.g., "How do I build a nuclear reactor?"),
* **When** the vector retrieval score falls below the confidence cutoff ($0.65$),
* **Then** the assistant states that the Lenny archive does not contain sufficient information and does not invent any claims or citations.

### AC-3: Model Provider Toggling
* **Given** the application is running,
* **When** the user toggles from Local (Ollama) to Cloud (OpenAI) in the UI,
* **Then** the next query is routed to OpenAI without page reload, and the header indicator reflects the active provider.

### AC-4: Ship 30 for 30 Skill Generation
* **Given** an active chat thread with retrieved growth concepts,
* **When** the user triggers the `/ship30` action,
* **Then** the assistant generates a structured essay (~1,250 words, hook, rhythmic headings, grounded takeaways) and opens it directly in the Artifact Viewer.

### AC-5: Secure HTML Artifact Sandboxing
* **Given** an HTML artifact containing an interactive script,
* **When** rendered in the Artifact Viewer,
* **Then** it executes inside a sandboxed `<iframe>` without `allow-same-origin`, and any attempt to access `parent.document` or `localStorage` throws a browser security violation.

### AC-6: Session State Persistence
* **Given** an active conversation with multiple messages and an artifact,
* **When** the user refreshes the browser or restarts the client container,
* **Then** navigating back to that session restores all prior messages, citations, and artifacts.

---

## 20. Implementation Prioritization

To earn the highest evaluator trust, engineering focus across subsequent phases will follow this strict hierarchy:

1. **Grounding & RAG Quality (Highest Priority)**: If the system hallucinates, no amount of UI polish will save the product. Retrieval precision and citation integrity are paramount.
2. **Artifact Security & Rendering**: The sandbox must be impenetrable and the split-pane UX must feel fluid and responsive.
3. **Local Ollama Reliability**: The demo must execute cleanly on a standard developer machine without requiring cloud API keys.
4. **Ship 30 for 30 Skill Execution**: The output must feel like an authentic, high-caliber essay, not a generic bulleted summary.
5. **UI Polish & Interaction Details**: Dark theme consistency, streaming feedback, keyboard ergonomics, and responsive layout.
6. **Documentation & Architecture Clarity**: Clean, defensible codebase ready for enterprise handoff.

---

## 21. Open Questions & Items to Validate (Phase 2 Roadmap)

| Item | Context | Validation Strategy in Phase 2 |
|---|---|---|
| **Embedding Model Selection** | Need balanced embedding model compatible with both Ollama and pgvector (e.g., `nomic-embed-text` with 768 dims vs. OpenAI 1536 dims). | Benchmark retrieval latency and cosine separation across sample transcript queries. |
| **Chunking Strategy** | Dialogues feature natural speaker alternation. A pure character-count split may divide a guest's core answer. | Test 500-token sliding window with speaker turn boundary preservation. |
| **Ollama Context Window Limits** | Running 1,250-word Ship 30 generation on Ollama requires at least 4K–8K context tokens. | Validate `num_ctx: 8192` memory footprint on standard 16GB host machine. |
| **Database Migration Tooling** | Alembic configuration must smoothly handle `pgvector` extension creation on clean Docker startup. | Verify automated migration execution during `docker compose up`. |