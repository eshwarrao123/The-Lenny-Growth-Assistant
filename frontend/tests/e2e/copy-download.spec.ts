import { test, expect } from '@playwright/test'
import * as fs from 'fs'
import {
  HTML_ARTIFACT,
  MARKDOWN_ARTIFACT,
  MOCK_ARTIFACT_ID,
  htmlArtifactEvents,
  markdownArtifactEvents,
  mockChatStream,
  sendMessage,
  startNewChat,
} from './helpers'

async function openArtifact(
  page: import('@playwright/test').Page,
  kind: 'markdown' | 'html'
): Promise<import('@playwright/test').Locator> {
  await startNewChat(page)
  await mockChatStream(
    page,
    kind === 'markdown'
      ? markdownArtifactEvents(MOCK_ARTIFACT_ID)
      : htmlArtifactEvents(MOCK_ARTIFACT_ID)
  )
  await sendMessage(page, kind === 'markdown' ? 'Create a markdown checklist' : 'Create an HTML calculator')
  const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  await expect(viewer).toBeVisible()
  return viewer
}

test.describe('Copy and download controls', () => {
  test.use({ permissions: ['clipboard-read', 'clipboard-write'] })

  test('copy copies exact markdown content', async ({ page }) => {
    const viewer = await openArtifact(page, 'markdown')

    await viewer.getByRole('button', { name: 'Copy content' }).click()

    const clipboard = await page.evaluate(() => navigator.clipboard.readText())
    // Chromium normalizes clipboard text to CRLF on Windows
    expect(clipboard.replace(/\r\n/g, '\n')).toBe(MARKDOWN_ARTIFACT)
  })

  test('copy copies exact HTML content', async ({ page }) => {
    const viewer = await openArtifact(page, 'html')

    await viewer.getByRole('button', { name: 'Copy content' }).click()

    const clipboard = await page.evaluate(() => navigator.clipboard.readText())
    // Chromium normalizes clipboard text to CRLF on Windows
    expect(clipboard.replace(/\r\n/g, '\n')).toBe(HTML_ARTIFACT)
  })

  test('markdown artifact downloads as .md with correct content', async ({ page }) => {
    const viewer = await openArtifact(page, 'markdown')

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      viewer.getByRole('button', { name: 'Download artifact' }).click(),
    ])

    expect(download.suggestedFilename()).toBe('Checklist-v1.md')
    const content = fs.readFileSync(await download.path(), 'utf-8')
    expect(content).toBe(MARKDOWN_ARTIFACT)
  })

  test('HTML artifact downloads as .html with correct content', async ({ page }) => {
    const viewer = await openArtifact(page, 'html')

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      viewer.getByRole('button', { name: 'Download artifact' }).click(),
    ])

    expect(download.suggestedFilename()).toBe('Calculator-v1.html')
    const content = fs.readFileSync(await download.path(), 'utf-8')
    expect(content).toBe(HTML_ARTIFACT)
  })
})
