# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: copy-download.spec.ts >> Copy and download controls >> copy copies exact markdown content
- Location: tests\e2e\copy-download.spec.ts:34:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: 'Artifact viewer' })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: 'Artifact viewer' }) with timeout 10000ms
  - waiting for getByRole('region', { name: 'Artifact viewer' })

```

```yaml
- dialog "Unhandled Runtime Error":
  - navigation:
    - button "previous" [disabled]:
      - img "previous"
    - button "next" [disabled]:
      - img "next"
    - text: 1 of 1 error Next.js (14.2.35) is outdated
    - link "(learn more)":
      - /url: https://nextjs.org/docs/messages/version-staleness
  - button "Close"
  - heading "Unhandled Runtime Error" [level=1]
  - paragraph: "ReferenceError: cn is not defined"
  - heading "Source" [level=2]
  - link "src\\components\\ArtifactViewer.tsx (150:26) @ cn":
    - text: src\components\ArtifactViewer.tsx (150:26) @ cn
    - img
  - text: "148 | <button 149 | onClick={() => setShowRaw(!showRaw)} > 150 | className={cn( | ^ 151 | \"btn-ghost p-2 h-9 transition-colors\", 152 | showRaw && \"bg-surface-elevated\" 153 | )}"
  - heading "Call Stack" [level=2]
  - button "Show collapsed frames"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | import * as fs from 'fs'
  3  | import {
  4  |   HTML_ARTIFACT,
  5  |   MARKDOWN_ARTIFACT,
  6  |   MOCK_ARTIFACT_ID,
  7  |   htmlArtifactEvents,
  8  |   markdownArtifactEvents,
  9  |   mockChatStream,
  10 |   sendMessage,
  11 |   startNewChat,
  12 | } from './helpers'
  13 | 
  14 | async function openArtifact(
  15 |   page: import('@playwright/test').Page,
  16 |   kind: 'markdown' | 'html'
  17 | ): Promise<import('@playwright/test').Locator> {
  18 |   await startNewChat(page)
  19 |   await mockChatStream(
  20 |     page,
  21 |     kind === 'markdown'
  22 |       ? markdownArtifactEvents(MOCK_ARTIFACT_ID)
  23 |       : htmlArtifactEvents(MOCK_ARTIFACT_ID)
  24 |   )
  25 |   await sendMessage(page, kind === 'markdown' ? 'Create a markdown checklist' : 'Create an HTML calculator')
  26 |   const viewer = page.getByRole('region', { name: 'Artifact viewer' })
> 27 |   await expect(viewer).toBeVisible()
     |                        ^ Error: expect(locator).toBeVisible() failed
  28 |   return viewer
  29 | }
  30 | 
  31 | test.describe('Copy and download controls', () => {
  32 |   test.use({ permissions: ['clipboard-read', 'clipboard-write'] })
  33 | 
  34 |   test('copy copies exact markdown content', async ({ page }) => {
  35 |     const viewer = await openArtifact(page, 'markdown')
  36 | 
  37 |     await viewer.getByRole('button', { name: 'Copy content' }).click()
  38 | 
  39 |     const clipboard = await page.evaluate(() => navigator.clipboard.readText())
  40 |     // Chromium normalizes clipboard text to CRLF on Windows
  41 |     expect(clipboard.replace(/\r\n/g, '\n')).toBe(MARKDOWN_ARTIFACT)
  42 |   })
  43 | 
  44 |   test('copy copies exact HTML content', async ({ page }) => {
  45 |     const viewer = await openArtifact(page, 'html')
  46 | 
  47 |     await viewer.getByRole('button', { name: 'Copy content' }).click()
  48 | 
  49 |     const clipboard = await page.evaluate(() => navigator.clipboard.readText())
  50 |     // Chromium normalizes clipboard text to CRLF on Windows
  51 |     expect(clipboard.replace(/\r\n/g, '\n')).toBe(HTML_ARTIFACT)
  52 |   })
  53 | 
  54 |   test('markdown artifact downloads as .md with correct content', async ({ page }) => {
  55 |     const viewer = await openArtifact(page, 'markdown')
  56 | 
  57 |     const [download] = await Promise.all([
  58 |       page.waitForEvent('download'),
  59 |       viewer.getByRole('button', { name: 'Download artifact' }).click(),
  60 |     ])
  61 | 
  62 |     expect(download.suggestedFilename()).toBe('Checklist-v1.md')
  63 |     const content = fs.readFileSync(await download.path(), 'utf-8')
  64 |     expect(content).toBe(MARKDOWN_ARTIFACT)
  65 |   })
  66 | 
  67 |   test('HTML artifact downloads as .html with correct content', async ({ page }) => {
  68 |     const viewer = await openArtifact(page, 'html')
  69 | 
  70 |     const [download] = await Promise.all([
  71 |       page.waitForEvent('download'),
  72 |       viewer.getByRole('button', { name: 'Download artifact' }).click(),
  73 |     ])
  74 | 
  75 |     expect(download.suggestedFilename()).toBe('Calculator-v1.html')
  76 |     const content = fs.readFileSync(await download.path(), 'utf-8')
  77 |     expect(content).toBe(HTML_ARTIFACT)
  78 |   })
  79 | })
  80 | 
```