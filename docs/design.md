# The Lenny Growth Assistant - Design Document

## Design Principles (from Taste skill)

1. **Clarity over cleverness** - Obvious interactions, clear hierarchy
2. **Consistency** - Reusable patterns, predictable behavior
3. **Respect user attention** - No unnecessary animations, purposeful motion
4. **Trustworthy** - Honest loading states, clear error messages
5. **Accessible by default** - Semantic HTML, keyboard navigation, contrast

## Visual Language

### Color Palette
- **Background**: `#0A0A0B` (near black)
- **Surface**: `#18181B` (zinc-950)
- **Surface Elevated**: `#27272A` (zinc-900)
- **Border**: `#3F3F46` (zinc-700)
- **Primary**: `#EAB308` (yellow-500) - Lenny brand
- **Primary Muted**: `#CA8A04` (yellow-600)
- **Text Primary**: `#FAFAFA` (zinc-50)
- **Text Secondary**: `#A1A1AA` (zinc-400)
- **Text Muted**: `#71717A` (zinc-500)
- **Success**: `#22C55E` (green-500)
- **Error**: `#EF4444` (red-500)

### Typography
- **Font Family**: `Geist` (or system fallback)
- **Heading Scale**:
  - H1: 2.5rem / 1.1 tracking-tight
  - H2: 1.875rem / 1.1 tracking-tight
  - H3: 1.5rem / 1.2
  - H4: 1.25rem / 1.2
- **Body**: 1rem / 1.6 leading-relaxed
- **Small**: 0.875rem / 1.5
- **Code**: `Geist Mono`, 0.875rem

### Spacing System (4px base)
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px
- 3xl: 64px

### Border Radius
- sm: 4px
- md: 8px
- lg: 12px
- full: 9999px

### Shadows
- sm: `0 1px 2px rgba(0,0,0,0.3)`
- md: `0 4px 6px rgba(0,0,0,0.4)`
- lg: `0 10px 15px rgba(0,0,0,0.4)`

## Layout

### Main Application (Split Pane)
```
┌─────────────────────────────────────────────────────────────┐
│  Header (64px) - Logo, Session switcher, Settings          │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│      Chat Pane           │      Artifact Viewer Pane        │
│      (60% default)       │      (40% default)               │
│                          │                                  │
│  ┌────────────────────┐  │  ┌────────────────────────────┐  │
│  │  Message List      │  │  │  Artifact Toolbar          │  │
│  │  (flex-1, scroll)  │  │  │  - Version tabs            │  │
│  └────────────────────┘  │  │  - Copy/Download           │  │
│  ┌────────────────────┐  │  ├────────────────────────────┤  │
│  │  Input Area        │  │  │  Iframe Sandbox            │  │
│  │  - Textarea        │  │  │  (flex-1)                  │  │
│  │  - Send button     │  │  │                            │  │
│  │  - Skill triggers  │  │  │                            │  │
│  └────────────────────┘  │  └────────────────────────────┘  │
│                          │                                  │
├──────────────────────────┴──────────────────────────────────┤
│  Resize handle (drag to adjust split)                        │
└─────────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints (Implemented)
- **Desktop (≥1024px)**: Coexisting side-by-side split pane. The chat pane (`.chat-pane-host`) occupies `flex: 1 1 0%` with independent scrolling, while the artifact viewer pane (`.artifact-pane-host`) scales smoothly with a minimum width of 260px up to 70% of available viewport width. Neither pane overlaps or displaces the other.
- **Tablet (768px–1023px)**: Side-by-side split pane layout with a collapsible navigation sidebar to conserve horizontal real estate. The artifact pane maintains at least 260px width.
- **Mobile (<768px)**: Complete off-canvas sliding navigation drawer (`-translate-x-full` off-canvas when closed, `translate-x-0` when opened via hamburger button) and full-screen overlay artifact viewer (`fixed inset-0 z-50`) without horizontal scrolling or viewport overflow.

### Component Inventory

#### 1. SplitPane Layout
- **Desktop (≥1024px)**: Coexisting side-by-side split pane (`.chat-pane-host` occupies `flex: 1 1 0%` with independent scrolling; `.artifact-pane-host` scales smoothly with a minimum width of 260px up to 70% of available viewport width). Neither pane overlaps or displaces the other.
- **Tablet (768px–1023px)**: Side-by-side split pane layout with a collapsible navigation sidebar to conserve horizontal real estate. The artifact pane maintains at least 260px width.
- **Mobile (<768px)**: Full-screen overlay artifact viewer (`fixed inset-0 z-50`) without horizontal scrolling or viewport overflow.

#### 2. Navigation Drawer (Mobile & Collapsible Sidebar)
- **State**: Toggled via hamburger button or collapse arrow; on mobile, slides completely off-canvas using `-translate-x-full` transition when closed and `translate-x-0` when opened.
- **Contents**: "New Chat" primary action button, session list grouped chronologically, settings trigger, and collapse/expand controls.

#### 3. Chat & Message List
- **Scroll Container**: Independent vertical scroll with auto-scroll lock to the bottom during active SSE streaming. Manual scroll upward disengages auto-scroll to preserve reading position.
- **Message Bubble (User)**: Right-aligned pill in primary Lenny yellow (`bg-primary text-background`), medium font weight, `rounded-2xl` styling.
- **Message Bubble (Assistant)**: Left-aligned, preceded by an avatar badge with `Sparkles` icon (`bg-primary/10 border-primary/20`). Rendered using Tailwind typography prose classes (`prose prose-invert max-w-none`) supporting Markdown headings, lists, bold text, and code blocks.

#### 4. SourceCitations
- **Trigger**: Rendered at the foot of assistant messages when `sources` array is present in the API response or SSE stream.
- **Layout**: Elevated container (`bg-surface-elevated border-border p-3 rounded-lg`) with label `"Sources (Grounded in):"` followed by interactive pill tags.
- **Pill Content**: Small badge displaying guest name, episode title, and speaker label with a pulsing accent dot (`w-1.5 h-1.5 rounded-full bg-primary/60`).

#### 5. Chat Input & Skill Triggers
- **Input Textarea**: Auto-resizing multi-line textarea (`bg-surface border-border focus:border-primary`) with placeholder `"Ask about product, growth, or create artifacts..."`.
- **Keybindings**: `Enter` sends message; `Shift+Enter` inserts newline.
- **Skill Suggestions & Triggers**: Quick-action buttons (`/ship30 Write about onboarding`, `Create a PLG framework`, `How do I improve retention?`, `Make a pricing calculator`) populate the input instantly.
- **Send Button**: High-contrast icon button (`bg-primary text-background hover:bg-primary-hover`) disabled when input is empty or when stream is active.

#### 6. ProviderSelector
- **Location**: Top bar / settings header.
- **Options**: Local default (`Ollama (qwen2.5:7b)`), Cloud providers (`OpenAI (gpt-4o)`, `Anthropic (claude-3-5-sonnet)`).
- **Indicators**: Visual status badge indicating whether provider is currently reachable, active, or missing API keys.

#### 7. ArtifactViewer
- **Region**: Semantic landmark `<aside role="region" aria-label="Artifact viewer">`.
- **Header Toolbar**:
  - Title and type badge (`HTML` in green, `MARKDOWN` in yellow).
  - Version switcher buttons.
  - Raw / Preview view mode toggle (`Eye` / `Code` icons).
  - One-click Copy (with temporary checkmark feedback).
  - Direct Download (`.md` / `.html` with appropriate MIME headers).
  - Close button (`X` icon, `Escape` key trigger).
- **Markdown Mode**: Rendered via `react-markdown` + `remark-gfm`, strictly sanitized with client-side `DOMPurify` to forbid un-whitelisted scripts and inline handlers.
- **HTML Mode**: Rendered via `SandboxedIframe` with `sandbox="allow-scripts"` (strictly omitting `allow-same-origin`), ensuring zero access to parent cookies, local storage, or DOM.

#### 8. VersionHistory (Version Switcher)
- **Component**: Accessible button group (`role="group" aria-label="Artifact version"`) inside the artifact header.
- **Interactions**: Allows switching between version states (`v1`, `v2`, ...). Active version receives `aria-pressed="true"` and `bg-primary text-background` styling. Historical versions are fetched on-demand or loaded from client cache.

## Interaction Patterns (Emil Kowalski / Transitions.dev)

### Pane Coexistence & Split Layout
- Desktop: Chat and Artifact Viewer panes live side-by-side without overlap. Chat flexes with `flex: 1 1 0%` and artifact pane occupies up to 70% width with a strict 260px minimum width.
- Tablet: Preserves side-by-side view with collapsible navigation drawer.
- Mobile: Instant snap off-canvas drawer (`-translate-x-full` to `translate-x-0`) and full-screen artifact overlay modal.

### Artifact Open / Close / Reopen Cycle
- Opening: Automatically slides in and gains focus on `artifact_start` SSE event.
- Closing: Close button (`aria-label="Close artifact viewer"`) or `Escape` key immediately closes the viewer and returns keyboard focus directly to the chat textarea (`#chat-input`).
- Reopening: Clicking the "View Artifact" button on any message card immediately re-opens the cached or retrieved artifact in the viewer pane without state corruption.

### Raw / Preview Switching
- For Markdown artifacts, a toolbar toggle button allows users to switch between the sanitized rendered preview (`react-markdown` + `remark-gfm`) and the raw monospace markdown source (`<pre><code>`).

### Version Navigation
- When multiple versions of an artifact exist (e.g. revisions to a document), accessible pill tabs allow instantaneous switching. Version switching loads historical states via `/api/artifacts/versions/{session_id}/{title}`.

### Message Streaming
- Server-Sent Events stream tokens in real-time.
- Automatic scroll follows new tokens; manual upward scrolling pauses auto-scroll to preserve reading position.

### Skill Trigger
- Slash command menu (`/ship30`, `/artifact`, `/qa`) or deterministic natural language pattern matching.
- Immediate UI status indication ("Routing to Ship 30...", "Creating artifact...").

## Accessibility & Assistive Technology

- **Semantic Landmarks**: The artifact viewer declares `role="region"` with `aria-label="Artifact viewer"`.
- **Iframe Title**: All HTML artifact iframes declare `title="Artifact Preview"` satisfying WCAG 2.1 Principle 4.1.2.
- **Keyboard Trap Prevention**: Tabbing cycles predictably through artifact action buttons (Raw/Preview, Copy, Download, Version Switcher, Close) and seamlessly transfers focus back to the chat textarea upon closing or escaping.
- **Focus Rings**: High-contrast `focus-visible:ring-2 ring-yellow-500` outline on all interactive buttons, tabs, and input controls.
- **Screen Reader Labels**: Icon-only buttons include descriptive `aria-label` attributes (e.g., `"Close artifact viewer"`, `"Copy artifact content"`, `"Download artifact"`).
- **DOMPurify Sanitization**: Raw HTML within markdown is strictly scrubbed of scripts and event handlers before rendering.
- **Color Contrast**: Main text exceeds WCAG AA 4.5:1 contrast against dark background.

## Dark Mode Only
- Single theme (dark) per assignment
- No theme switching complexity
- CSS variables for all colors

## Icon System
- Lucide React (consistent, tree-shakeable)
- 20px default, 16px compact, 24px large
- Stroke width 2

## Loading States
- Skeleton screens for initial load
- Spinner only for discrete actions
- Progress for multi-step operations
- No flash of unloaded content

## Error States
- Inline validation errors
- Toast for non-blocking errors
- Full-page error for catastrophic failure
- Retry action always available

## Empty States
- Welcome illustration + prompt suggestions
- "No sessions yet" with CTA
- "No artifacts" in viewer

## Motion Guidelines
- Entrance: 200ms ease-out
- Exit: 150ms ease-in
- Micro-interactions: 100ms
- No loops, no infinite animations
- Respect `prefers-reduced-motion`

## Architecture Decisions (Final Status)

| Decision | Status | Implementation Notes |
|----------|--------|----------------------|
| Typography | Resolved | System sans-serif font stack with Geist fallbacks for maximum performance and zero layout shift |
| Animation & Motion | Resolved | Native CSS transitions and Tailwind utility classes; zero extraneous bundle weight |
| Markdown Rendering | Resolved | `react-markdown` with `remark-gfm` and strict client-side DOMPurify sanitization |
| Syntax Highlighting | Resolved | Styled `<pre><code>` blocks via Tailwind Typography `prose prose-invert` for dark mode consistency |
| Message Scroll Management | Resolved | Native browser scroll anchoring with smooth `scrollIntoView` and user-scroll override detection |
| Iframe Sandboxing | Resolved | `<iframe sandbox="allow-scripts">` (strictly omitting `allow-same-origin`) to prevent token/cookie/storage access |