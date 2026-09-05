import { test, expect } from '@playwright/test'
import {
  MARKDOWN_ARTIFACT,
  MARKDOWN_ARTIFACT_V2,
  MOCK_ARTIFACT_ID,
  MOCK_ARTIFACT_V2_ID,
  artifactPayload,
  groundedQaEvents,
  htmlArtifactEvents,
  markdownArtifactEvents,
  mockArtifactGet,
  mockArtifactVersions,
  mockChatStream,
  sendMessage,
  startNewChat,
  HTML_ARTIFACT,
} from './helpers'

test.describe('Core application flows', () => {
  test('application loads with chat UI', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle('Lenny Growth Assistant')
    await expect(page.getByRole('heading', { name: 'Lenny Growth', exact: true })).toBeVisible()
    await expect(page.getByText('Welcome to Lenny Growth Assistant')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()
  })

  test('creates a new session via the real backend', async ({ page }) => {
    await startNewChat(page)
    // Header switches to the new session title
    await expect(page.getByRole('heading', { name: 'New Chat', exact: true })).toBeVisible()
    // Session appears in the sidebar list
    await expect(page.locator('aside').getByRole('button', { name: 'New Chat' }).first()).toBeVisible()
  })

  test('grounded question streams an answer with sources', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, groundedQaEvents())

    await sendMessage(page, 'What does Elena Verna say about product-led sales?')

    await expect(page.getByText('Elena Verna recommends starting with self-serve onboarding before sales.')).toBeVisible()
    await expect(page.getByText('Sources:', { exact: false })).toBeVisible()
    await expect(page.getByText('Elena Verna on PLG').first()).toBeVisible()
  })

  test('markdown artifact request renders native markdown in viewer', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist for activation work')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()
    await expect(viewer.getByText(/^markdown$/i)).toBeVisible()
    await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
    await expect(viewer.getByText('Define the activation metric')).toBeVisible()
  })

  test('HTML artifact request renders sandboxed iframe in viewer', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create an HTML calculator')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()
    await expect(viewer.getByText(/^html$/i)).toBeVisible()
    const iframe = viewer.locator('iframe')
    await expect(iframe).toBeVisible()
    // Content actually rendered inside the sandboxed frame
    await expect(iframe.contentFrame().locator('h1')).toHaveText('Tiny Calculator')
  })

  test('artifact viewer closes and reopens from the message button', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
    await mockArtifactGet(page, MOCK_ARTIFACT_ID, artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT))

    await sendMessage(page, 'Create a markdown checklist')
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Close
    await viewer.getByRole('button', { name: 'Close artifact viewer' }).click()
    await expect(viewer).toHaveCount(0)

    // Reopen via the persisted-artifact button (real GET /api/artifacts/{id})
    await page.getByRole('button', { name: 'View Artifact' }).click()
    await expect(viewer).toBeVisible()
    await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
  })

  test('version switching shows previous version content', async ({ page }) => {
    await startNewChat(page)
    const v1 = artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT, 1)
    const v2 = artifactPayload(MOCK_ARTIFACT_V2_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT_V2, 2)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_V2_ID))
    await mockArtifactVersions(page, 'Checklist', [v1, v2])

    await sendMessage(page, 'Update the checklist with owners')
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Current artifact is v2
    const versionGroup = viewer.getByRole('group', { name: 'Artifact version' })
    await expect(versionGroup).toBeVisible()
    const v2Button = versionGroup.getByRole('button', { name: 'Version 2' })
    await expect(v2Button).toHaveAttribute('aria-pressed', 'true')

    // Switch to v1 and verify content swaps
    const v1Button = versionGroup.getByRole('button', { name: 'Version 1' })
    await v1Button.click()
    await expect(viewer.getByRole('heading', { name: 'Growth Checklist', exact: true })).toBeVisible()
    await expect(viewer.getByText('Instrument the funnel', { exact: true })).toBeVisible()

    // Switch back to v2
    await v2Button.click()
    await expect(viewer.getByText('Instrument the funnel (Data)')).toBeVisible()
  })

  test('raw/preview toggle shows source and rendered views', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist')
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Raw mode shows the markdown source as text
    await viewer.getByRole('button', { name: 'Show raw code' }).click()
    await expect(viewer.locator('pre')).toContainText('# Growth Checklist')

    // Back to preview
    await viewer.getByRole('button', { name: 'Show preview' }).click()
    await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
  })

  test('loading state disables input while streaming', async ({ page }) => {
    await startNewChat(page)
    await page.route('**/api/chat', async route => {
      await new Promise(resolve => setTimeout(resolve, 2500))
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: '',
      })
    })

    await sendMessage(page, 'Hello')

    const textarea = page.locator('textarea')
    await expect(textarea).toBeDisabled()
    await expect(page.getByPlaceholder('Streaming...')).toBeVisible()
    await expect(textarea).toBeEnabled({ timeout: 15_000 })
  })

  test('error state surfaces backend error events inline', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, [
      { event: 'start', data: { session_id: 'x', skill: 'artifact' } },
      {
        event: 'error',
        data: { code: 'artifact_size_exceeded', message: 'Artifact size exceeded maximum allowed size of 5MB' },
      },
      { event: 'done', data: {} },
    ])

    await sendMessage(page, 'Create a huge artifact')

    await expect(page.getByText(/Artifact size exceeded maximum allowed size/)).toBeVisible()
  })

  test('error state surfaces connection failures inline', async ({ page, context }) => {
    await startNewChat(page)
    await context.route('**/api/chat', route => route.abort('connectionrefused'))

    await sendMessage(page, 'Hello')

    await expect(page.getByText(/Unable to reach the server/)).toBeVisible()
    // The user's message stays visible for retry
    await expect(page.getByText('Hello', { exact: true })).toBeVisible()
  })

  test('artifact generation links the artifact id carried by SSE done event', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID, HTML_ARTIFACT))

    await sendMessage(page, 'Create an HTML calculator')

    // artifact_done carried the backend artifact id -> "View Artifact" appears
    await page.getByRole('button', { name: 'View Artifact' }).waitFor({ timeout: 10_000 })
    await expect(page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')).toBeVisible()
  })

  test('enter key sends message from the textarea', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, groundedQaEvents())

    await page.locator('textarea').fill('What improves retention?')
    await page.locator('textarea').press('Enter')

    await expect(page.getByText('What improves retention?', { exact: true })).toBeVisible()
    await expect(page.getByText(/Elena Verna recommends/)).toBeVisible()
  })
})
