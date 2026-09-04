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

### Responsive Breakpoints
- **Desktop**: ≥1024px - Full split pane
- **Tablet**: 768-1023px - Collapsible artifact pane
- **Mobile**: <768px - Bottom sheet for artifacts

### Component Specifications

#### Chat Message
```
┌─────────────────────────────────────────────────────────┐
│  [Avatar]  Assistant                          [Copy]    │
│                                                         │
│  Response content with markdown rendering...           │
│                                                         │
│  ─────────────────────────────────────────────────      │
│  Sources: Episode 42 (Lenny Rachitsky) • Episode 15... │
│                                                         │
│  [Artifact badge] [Regenerate] [Thumbs up/down]        │
└─────────────────────────────────────────────────────────┘
```

#### Streaming State
- Skeleton shimmer while loading first token
- Token-by-token appearance (no typewriter effect)
- "Stop" button appears during streaming

#### Artifact Viewer
```
┌─────────────────────────────────────────────────────────┐
│  Artifact Title                    v1.0  v1.1  v1.2  ⋮ │
├─────────────────────────────────────────────────────────┤
│                                                         │
│         [Sandboxed Iframe - fills available space]     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Copy Code] [Download] [Open Fullscreen] [Close]      │
└─────────────────────────────────────────────────────────┘
```

#### Session Sidebar (Collapsible)
```
┌────────────────────────────┐
│  [+] New Chat              │
│  ────────────────────────  │
│  Today                     │
│  ├─ Product Strategy Q&A  │
│  ├─ Writing Exercise #3   │
│  ────────────────────────  │
│  This Week                 │
│  ├─ Growth Metrics Deep...│
│  └─ Retention Analysis    │
│  ────────────────────────  │
│  [Search sessions...]      │
└────────────────────────────┘
```

## Interaction Patterns (Emil Kowalski / Transitions.dev)

### Pane Resize
- Drag handle with visual feedback
- Persist ratio in localStorage
- Smooth transition (150ms ease-out)

### Artifact Open/Close
- Slide in from right (desktop)
- Slide up from bottom (mobile)
- 200ms spring animation
- ESC to close

### Message Streaming
- No artificial delay
- Smooth scroll to bottom (auto-scroll when at bottom)
- Preserve scroll position when not at bottom

### Session Switch
- Fade out old messages (100ms)
- Fade in new messages (100ms)
- Staggered entrance for message list

### Skill Trigger
- Slash command menu (`/ship30`, `/artifact`)
- Keyboard navigable
- Preview on hover

## Accessibility

- All interactive elements keyboard reachable
- Focus visible with 2px outline (yellow-500)
- ARIA labels on icon buttons
- Live regions for streaming updates
- Color contrast ≥4.5:1 for text
- Reduced motion respected

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

## Decisions to Validate

| Decision | Status | Notes |
|----------|--------|-------|
| Font loading strategy | To validate | Self-host Geist vs CDN |
| Animation library | To validate | Framer Motion vs CSS only |
| Markdown renderer | To validate | React-markdown + plugins |
| Syntax highlighting | To validate | Shiki vs Prism |
| Virtualization for messages | To validate | react-window if needed |