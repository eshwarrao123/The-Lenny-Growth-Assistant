import type { Page, Route } from '@playwright/test'

/**
 * Shared helpers for the E2E suite.
 *
 * The app under test is the real running stack. Chat SSE streams are stubbed
 * with realistic backend event sequences (same event names and payloads as
 * backend/app/services/chat_service.py) so tests are deterministic, while
 * sessions/artifacts REST endpoints hit the real FastAPI backend.
 */

export const MOCK_ARTIFACT_ID = '11111111-1111-4111-8111-111111111111'
export const MOCK_ARTIFACT_V2_ID = '22222222-2222-4222-8222-222222222222'
export const MOCK_SESSION_ID = '33333333-3333-4333-8333-333333333333'

export interface SseEvent {
  event: string
  data: unknown
}

/** Format events exactly like the backend: `event: <name>\ndata: <json>\n\n`. */
export function sse(events: SseEvent[]): string {
  return events.map(e => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`).join('')
}

export const MARKDOWN_ARTIFACT = [
  '# Growth Checklist',
  '',
  'A short checklist for activation work.',
  '',
  '## Steps',
  '',
  '1. Define the activation metric',
  '2. Instrument the funnel',
  '3. Review weekly',
  '',
  '**Grounded in:** Lenny\'s Podcast',
].join('\n')

export const MARKDOWN_ARTIFACT_V2 = [
  '# Growth Checklist (v2)',
  '',
  'Updated checklist with owners.',
  '',
  '## Steps',
  '',
  '1. Define the activation metric (PM)',
  '2. Instrument the funnel (Data)',
  '3. Review weekly (Growth)',
].join('\n')

/** Interactive HTML artifact that follows the component's DOMPurify allow-list:
 *  inline <script> tags are allowed; inline on* handlers are not. */
export const HTML_ARTIFACT = [
  '<!DOCTYPE html>',
  '<html>',
  '<head><meta charset="UTF-8"><title>Calculator</title></head>',
  '<body style="font-family: sans-serif">',
  '  <h1>Tiny Calculator</h1>',
  '  <button id="calc-btn">Add 1+1</button>',
  '  <div id="out">?</div>',
  '  <script>',
  "    document.getElementById('calc-btn').addEventListener('click', function () {",
  "      document.getElementById('out').textContent = '2';",
  '    });',
  '  </script>',
  '</body>',
  '</html>',
].join('\n')

/** Safe-looking artifact whose script tries to escape the sandbox.
 *  It logs `BREACH:` on success and `ISOLATED:` when the sandbox blocks it. */
export const MALICIOUS_HTML_ARTIFACT = [
  '<!DOCTYPE html>',
  '<html>',
  '<head><title>Sneaky</title></head>',
  '<body>',
  '  <h1 id="proof">Sneaky artifact</h1>',
  '  <script>',
  "    function attempt(label, fn) {",
  '      try {',
  '        var result = fn();',
  "        console.log('BREACH: ' + label + ' -> ' + String(result).slice(0, 80));",
  '      } catch (e) {',
  "        console.log('ISOLATED: ' + label + ' (' + e.name + ')');",
  '      }',
  '    }',
  "    attempt('parent.document', function () {",
  "      window.parent.document.body.innerHTML = 'HACKED';",
  '      return window.parent.document.title;',
  '    });',
  "    attempt('parent.localStorage', function () {",
  "      window.parent.localStorage.setItem('hacked', 'true');",
  "      return window.parent.localStorage.getItem('hacked');",
  '    });',
  "    attempt('parent.cookie', function () {",
  "      window.parent.document.cookie = 'hacked=1';",
  '      return window.parent.document.cookie;',
  '    });',
  "    attempt('window.top', function () {",
  '      return window.top.location.href;',
  '    });',
  "    attempt('top navigation', function () {",
  "      window.top.location.href = 'https://attacker.invalid/';",
  '      return true;',
  '    });',
  '  </script>',
  '</body>',
  '</html>',
].join('\n')

/** Markdown artifact containing classic XSS payloads. */
export const XSS_MARKDOWN_ARTIFACT = [
  '# Safe Heading',
  '',
  'Regular **markdown** content should render.',
  '',
  "<script>alert('xss-script')</script>",
  '',
  "<img src=\"x\" onerror=\"alert('xss-img')\">",
  '',
  "[click me](javascript:alert('xss-link'))",
  '',
  "![payload](javascript:alert('xss-mdimg'))",
  '',
  "<iframe src=\"javascript:alert('xss-iframe')\"></iframe>",
  '',
  "<svg><animate attributeName=\"href\" onbegin=\"alert('xss-svg')\" dur=\"1s\"></animate></svg>",
  '',
  "<a href=\"javascript:alert('xss-anchor')\">bad anchor</a>",
].join('\n')

/** Intercept POST /api/chat and answer with the given SSE event stream. */
export async function mockChatStream(page: Page, events: SseEvent[]): Promise<void> {
  await page.route('**/api/chat', async (route: Route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
      body: sse(events),
    })
  })
}

/** Standard grounded-QA stream (no artifact). */
export function groundedQaEvents(): SseEvent[] {
  return [
    { event: 'start', data: { session_id: MOCK_SESSION_ID, skill: 'grounded_qa' } },
    { event: 'status', data: { message: 'Retrieving transcript evidence...' } },
    {
      event: 'sources',
      data: {
        sources: [
          {
            chunk_id: '99999999-9999-4999-8999-999999999999',
            episode: 'Elena Verna on PLG',
            guest: 'Elena Verna',
            timestamp: '00:12:34',
            similarity: 0.82,
          },
        ],
      },
    },
    { event: 'token', data: { content: 'Elena Verna recommends starting with ' } },
    { event: 'token', data: { content: 'self-serve onboarding before sales.' } },
    { event: 'done', data: {} },
  ]
}

/** Markdown artifact stream (chunks split like the backend would). */
export function markdownArtifactEvents(artifactId: string, content = MARKDOWN_ARTIFACT, title = 'Checklist'): SseEvent[] {
  return [
    { event: 'start', data: { session_id: MOCK_SESSION_ID, skill: 'artifact' } },
    { event: 'status', data: { message: 'Generating markdown artifact...' } },
    { event: 'artifact_start', data: { type: 'markdown', title } },
    { event: 'artifact_chunk', data: { content: content.slice(0, Math.floor(content.length / 2)) } },
    { event: 'artifact_chunk', data: { content: content.slice(Math.floor(content.length / 2)) } },
    { event: 'artifact_done', data: { artifact_id: artifactId } },
    { event: 'done', data: {} },
  ]
}

/** HTML artifact stream. */
export function htmlArtifactEvents(artifactId: string, content = HTML_ARTIFACT, title = 'Calculator'): SseEvent[] {
  return [
    { event: 'start', data: { session_id: MOCK_SESSION_ID, skill: 'artifact' } },
    { event: 'status', data: { message: 'Generating HTML artifact...' } },
    { event: 'artifact_start', data: { type: 'html', title } },
    { event: 'artifact_chunk', data: { content } },
    { event: 'artifact_done', data: { artifact_id: artifactId } },
    { event: 'done', data: {} },
  ]
}

/** Stub GET /api/artifacts/{id} with an artifact payload. */
export async function mockArtifactGet(
  page: Page,
  artifactId: string,
  artifact: Record<string, unknown>
): Promise<void> {
  await page.route(`**/api/artifacts/${artifactId}`, async (route: Route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(artifact) })
  })
}

/** Stub GET /api/artifacts/versions/{sessionId}/{title}. */
export async function mockArtifactVersions(
  page: Page,
  title: string,
  versions: Array<Record<string, unknown>>
): Promise<void> {
  await page.route(`**/api/artifacts/versions/*/${title}`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ versions }),
    })
  })
}

export function artifactPayload(
  id: string,
  type: 'html' | 'markdown',
  title: string,
  content: string,
  version = 1
): Record<string, unknown> {
  return {
    id,
    session_id: MOCK_SESSION_ID,
    message_id: null,
    type,
    title,
    content,
    version,
    created_at: '2026-09-05T00:00:00Z',
    updated_at: '2026-09-05T00:00:00Z',
  }
}

/** Open the app and create a fresh session through the real backend. */
export async function startNewChat(page: Page): Promise<void> {
  await page.goto('/')
  await createSession(page)
}

/** Click the sidebar's New Chat button, waiting for the real POST /api/sessions. */
export async function createSession(page: Page): Promise<void> {
  const created = page.waitForResponse(
    res => res.url().includes('/api/sessions') && res.request().method() === 'POST' && res.ok(),
    { timeout: 15_000 }
  )
  await page.locator('aside button.btn-primary').first().click()
  await created
}

export async function expectSessionActive(page: Page): Promise<void> {
  await page.waitForResponse(
    res => res.url().includes('/api/sessions') && res.request().method() === 'POST' && res.ok(),
    { timeout: 15_000 }
  )
}

/** Type into the chat box and press Enter. */
export async function sendMessage(page: Page, message: string): Promise<void> {
  await page.locator('textarea').fill(message)
  await page.locator('textarea').press('Enter')
}
