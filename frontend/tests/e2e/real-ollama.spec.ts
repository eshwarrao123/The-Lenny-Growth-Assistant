import { test, expect } from '@playwright/test'
import { sendMessage, startNewChat } from './helpers'

/**
 * REAL end-to-end generation tests against the live stack:
 * PostgreSQL + FastAPI + Ollama (qwen2.5:7b) + Next.js.
 *
 * A pass-through route spy forwards /api/chat to the real backend unchanged,
 * records the raw SSE stream, and lets the page consume it. This verifies:
 * routing -> retrieval -> generation -> SSE artifact events -> persistence ->
 * retrieval via API -> frontend rendering.
 */

interface RecordedSse {
  body: string
  status: number
}

function spyChatStream(page: import('@playwright/test').Page, recorded: RecordedSse[]): void {
  page.route('**/api/chat', async route => {
    const response = await route.fetch()
    const body = await response.text()
    recorded.push({ body, status: response.status() })
    await route.fulfill({ response })
  })
}

function extractEvent(body: string, name: string): unknown[] {
  const payloads: unknown[] = []
  const lines = body.split('\n')
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === `event: ${name}` && i + 1 < lines.length) {
      const dataLine = lines[i + 1]
      if (dataLine.startsWith('data:')) {
        try {
          payloads.push(JSON.parse(dataLine.slice(5).trim()))
        } catch {
          // ignore malformed
        }
      }
    }
  }
  return payloads
}

test.describe('Real Ollama artifact generation', () => {
  test.setTimeout(240_000)

  test('real Markdown artifact: routing, SSE events, persistence, rendering', async ({ page, request }) => {
    await startNewChat(page)

    const recorded: RecordedSse[] = []
    spyChatStream(page, recorded)

    await sendMessage(page, 'Create a short markdown checklist with exactly 3 items for improving user onboarding.')

    // 1. Frontend renders the artifact natively
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible({ timeout: 220_000 })
    await expect(viewer.getByText(/^markdown$/i)).toBeVisible()

    // 2. Real SSE stream: routing + artifact event sequence
    expect(recorded.length).toBe(1)
    expect(recorded[0].status).toBe(200)
    const body = recorded[0].body
    expect(body).toContain('event: start')
    const startEvents = extractEvent(body, 'start') as Array<{ skill?: string }>
    expect(startEvents.length).toBeGreaterThanOrEqual(1)
    expect(startEvents[0].skill, 'request must route to the artifact skill').toBe('artifact')

    expect(body).toContain('event: artifact_start')
    expect(body).toContain('event: artifact_chunk')
    expect(body).toContain('event: artifact_done')

    const starts = extractEvent(body, 'artifact_start') as Array<{ type?: string; title?: string }>
    expect(starts[0].type).toBe('markdown')
    const title = starts[0].title!

    const chunks = extractEvent(body, 'artifact_chunk') as Array<{ content?: string }>
    const streamedContent = chunks.map(c => c.content ?? '').join('')
    expect(streamedContent.length, 'artifact content must be non-empty').toBeGreaterThan(0)

    const dones = extractEvent(body, 'artifact_done') as Array<{ artifact_id?: string }>
    const artifactId = dones[0].artifact_id
    expect(artifactId, 'artifact_done must carry the persisted artifact id').toBeTruthy()

    // 3. Persistence + retrieval through the real API
    const res = await request.get(`http://localhost:8000/api/artifacts/${artifactId}`)
    expect(res.status()).toBe(200)
    const persisted = (await res.json()) as {
      id: string
      type: string
      title: string
      content: string
      version: number
    }
    expect(persisted.type).toBe('markdown')
    expect(persisted.title).toBe(title)
    expect(persisted.version).toBe(1)
    expect(persisted.content).toBe(streamedContent)

    // 4. Viewer shows the streamed markdown
    const rendered = await viewer.innerText()
    expect(rendered.length).toBeGreaterThan(0)
  })

  test('real HTML artifact: routing, SSE events, persistence, sandboxed rendering', async ({ page, request }) => {
    await startNewChat(page)

    const recorded: RecordedSse[] = []
    spyChatStream(page, recorded)

    await sendMessage(
      page,
      'Create a tiny HTML calculator with two number inputs and an add button. Use a <script> tag with addEventListener, no inline onclick. Keep it under 60 lines.'
    )

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible({ timeout: 220_000 })
    await expect(viewer.getByText(/^html$/i)).toBeVisible()

    // Real SSE stream: routing + artifact event sequence
    expect(recorded.length).toBe(1)
    const body = recorded[0].body
    const startEvents = extractEvent(body, 'start') as Array<{ skill?: string }>
    expect(startEvents[0].skill).toBe('artifact')

    expect(body).toContain('event: artifact_start')
    expect(body).toContain('event: artifact_chunk')
    expect(body).toContain('event: artifact_done')

    const starts = extractEvent(body, 'artifact_start') as Array<{ type?: string; title?: string }>
    expect(starts[0].type).toBe('html')

    const chunks = extractEvent(body, 'artifact_chunk') as Array<{ content?: string }>
    const streamedContent = chunks.map(c => c.content ?? '').join('')
    expect(streamedContent, 'HTML artifact must contain markup').toContain('<')

    const dones = extractEvent(body, 'artifact_done') as Array<{ artifact_id?: string }>
    const artifactId = dones[0].artifact_id
    expect(artifactId).toBeTruthy()

    // Persistence + retrieval through the real API
    const res = await request.get(`http://localhost:8000/api/artifacts/${artifactId}`)
    expect(res.status()).toBe(200)
    const persisted = (await res.json()) as { type: string; content: string; version: number }
    expect(persisted.type).toBe('html')
    expect(persisted.content).toBe(streamedContent)

    // Sandboxed rendering
    const iframe = viewer.locator('iframe')
    await expect(iframe).toBeVisible()
    const sandboxAttr = await iframe.getAttribute('sandbox')
    expect(sandboxAttr).toContain('allow-scripts')
    expect(sandboxAttr).not.toContain('allow-same-origin')

    // Reopen from the persisted artifact (real GET /api/artifacts/{id} via UI)
    await viewer.getByRole('button', { name: 'Close artifact viewer' }).click()
    await expect(viewer).toHaveCount(0)
    await page.getByRole('button', { name: 'View Artifact' }).click()
    await expect(viewer).toBeVisible()
    await expect(viewer.locator('iframe')).toBeVisible()
  })
})

