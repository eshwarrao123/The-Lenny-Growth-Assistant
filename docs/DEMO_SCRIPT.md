# Lenny Growth Assistant — Demo Video Script

**Target Duration**: 2 minutes 45 seconds (Strictly under 3 minutes)  
**Presenter Setup**: Screen recording with camera overlay enabled in lower-right corner. High-contrast terminal and browser windows open side-by-side.

---

## ⏱️ Timeline & Dialogue

### 0:00 – 0:20 | Problem & Product Overview
- **Visual**: Show Next.js web application home screen on `http://localhost:3000` with the dark-mode split pane and prompt suggestions.
- **Presenter**:
  > *"Hi! I'm presenting the Lenny Growth Assistant — a production-grade AI system built on 303 episodes of Lenny's Podcast. Product leaders and founders get instant, expert growth advice grounded strictly in transcript evidence, formatted into conversational answers, structured Ship 30 atomic essays, or live interactive artifacts."*

---

### 0:20 – 0:55 | Grounded Q&A + Citation Verification
- **Visual**: Type query: *"What does Elena Verna say about product-led sales?"* into the chat box and hit Enter. Show real-time token streaming via Server-Sent Events (SSE) and the appearance of the `"Sources:"` citation card.
- **Presenter**:
  > *"Let's ask a grounded question. Notice how the response streams tokens in real time via SSE. At the bottom, the assistant provides exact, verifiable transcript citations — highlighting the guest name, episode title, and timestamp. The vector search runs over 768-dimensional pgvector HNSW embeddings, ensuring zero hallucination on out-of-domain topics."*

---

### 0:55 – 1:20 | Source Attribution & Follow-Up Context
- **Visual**: Hover over source citation badge `[Elena Verna on PLG]`, then type follow-up: *"What are the top 3 mistakes to avoid?"*
- **Presenter**:
  > *"The system maintains full conversation session state in PostgreSQL, resolving follow-up questions seamlessly while preserving grounded evidence across multi-turn turns."*

---

### 1:20 – 1:45 | Dedicated Skill Routing (Ship 30 for 30)
- **Visual**: Type: `"/ship30 Write about onboarding friction"` or click suggestion. Watch system route to `ship30` skill and stream an atomic essay with 1/3/1 visual rhythm, rapid Rate of Revelation, and Wheels & Spokes subheadings.
- **Presenter**:
  > *"Next, we trigger the dedicated Ship 30 for 30 skill. The skill router automatically classifies intent, pulling transcript evidence into a published-quality ~1,250-word atomic essay formatted with 1/3/1 visual rhythm and actionable key takeaways."*

---

### 1:45 – 2:15 | Interactive Artifact Viewer & HTML Sandbox
- **Visual**: Type: *"Make an HTML pricing calculator component"*. Watch the right split pane open automatically. Show the interactive calculator inside the iframe, toggle Raw/Preview mode, switch version tabs (`v1` / `v2`), and click Copy / Download.
- **Presenter**:
  > *"Here is the Artifact Viewer. For complex layouts or interactive tools, the assistant generates standalone Markdown or live HTML/CSS/JS components in a side-by-side pane. Security is paramount: HTML artifacts execute inside a sandboxed iframe with `allow-scripts` strictly omitting `allow-same-origin`. This creates a null-origin context that cannot touch parent cookies, local storage, or host DOM."*

---

### 2:15 – 2:40 | Ollama Local Engine & Provider Flexibility
- **Visual**: Switch to terminal showing `ollama list` (`qwen2.5:7b` and `nomic-embed-text`), then highlight the Provider Selector dropdown in the app header (showing Local Ollama default alongside optional Cloud providers).
- **Presenter**:
  > *"The stack is powered locally by Ollama running `qwen2.5:7b` for reasoning and `nomic-embed-text` for 768-dimensional embeddings, giving users 100% local privacy and zero API costs. Cloud providers like OpenAI and Anthropic are also supported out of the box."*

---

### 2:40 – 3:00 | Engineering Trade-off & Closing
- **Visual**: Return to the full application interface showing side-by-side chat and artifact pane.
- **Presenter**:
  > *"A key engineering trade-off was local CPU inference latency versus browser sandboxing. To deliver high-trust interactive tools safely on CPU without blocking the UI, we implemented debounced SSE stream parsing and a decoupled iframe event channel. The repository is fully containerized, tested with 36 backend tests and 31 Playwright E2E specs, and ready for deployment. Thanks for watching!"*

---
