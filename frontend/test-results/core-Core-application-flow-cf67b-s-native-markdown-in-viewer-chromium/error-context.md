# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: core.spec.ts >> Core application flows >> markdown artifact request renders native markdown in viewer
- Location: tests\e2e\core.spec.ts:47:7

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
  1   | import { test, expect } from '@playwright/test'
  2   | import {
  3   |   MARKDOWN_ARTIFACT,
  4   |   MARKDOWN_ARTIFACT_V2,
  5   |   MOCK_ARTIFACT_ID,
  6   |   MOCK_ARTIFACT_V2_ID,
  7   |   artifactPayload,
  8   |   groundedQaEvents,
  9   |   htmlArtifactEvents,
  10  |   markdownArtifactEvents,
  11  |   mockArtifactGet,
  12  |   mockArtifactVersions,
  13  |   mockChatStream,
  14  |   sendMessage,
  15  |   startNewChat,
  16  |   HTML_ARTIFACT,
  17  | } from './helpers'
  18  | 
  19  | test.describe('Core application flows', () => {
  20  |   test('application loads with chat UI', async ({ page }) => {
  21  |     await page.goto('/')
  22  |     await expect(page).toHaveTitle('Lenny Growth Assistant')
  23  |     await expect(page.getByRole('heading', { name: 'Lenny Growth' })).toBeVisible()
  24  |     await expect(page.getByText('Welcome to Lenny Growth Assistant')).toBeVisible()
  25  |     await expect(page.locator('textarea')).toBeVisible()
  26  |   })
  27  | 
  28  |   test('creates a new session via the real backend', async ({ page }) => {
  29  |     await startNewChat(page)
  30  |     // Header switches to the new session title
  31  |     await expect(page.getByRole('heading', { name: 'New Chat', exact: true })).toBeVisible()
  32  |     // Session appears in the sidebar list
  33  |     await expect(page.locator('aside').getByRole('button', { name: 'New Chat' }).first()).toBeVisible()
  34  |   })
  35  | 
  36  |   test('grounded question streams an answer with sources', async ({ page }) => {
  37  |     await startNewChat(page)
  38  |     await mockChatStream(page, groundedQaEvents())
  39  | 
  40  |     await sendMessage(page, 'What does Elena Verna say about product-led sales?')
  41  | 
  42  |     await expect(page.getByText('Elena Verna recommends starting with self-serve onboarding before sales.')).toBeVisible()
  43  |     await expect(page.getByText('Sources:', { exact: false })).toBeVisible()
  44  |     await expect(page.getByText('Elena Verna on PLG').first()).toBeVisible()
  45  |   })
  46  | 
  47  |   test('markdown artifact request renders native markdown in viewer', async ({ page }) => {
  48  |     await startNewChat(page)
  49  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  50  | 
  51  |     await sendMessage(page, 'Create a markdown checklist for activation work')
  52  | 
  53  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
> 54  |     await expect(viewer).toBeVisible()
      |                          ^ Error: expect(locator).toBeVisible() failed
  55  |     await expect(viewer.getByText(/^markdown$/i)).toBeVisible()
  56  |     await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
  57  |     await expect(viewer.getByText('Define the activation metric')).toBeVisible()
  58  |   })
  59  | 
  60  |   test('HTML artifact request renders sandboxed iframe in viewer', async ({ page }) => {
  61  |     await startNewChat(page)
  62  |     await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))
  63  | 
  64  |     await sendMessage(page, 'Create an HTML calculator')
  65  | 
  66  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  67  |     await expect(viewer).toBeVisible()
  68  |     await expect(viewer.getByText(/^html$/i)).toBeVisible()
  69  |     const iframe = viewer.locator('iframe')
  70  |     await expect(iframe).toBeVisible()
  71  |     // Content actually rendered inside the sandboxed frame
  72  |     await expect(iframe.contentFrame().locator('h1')).toHaveText('Tiny Calculator')
  73  |   })
  74  | 
  75  |   test('artifact viewer closes and reopens from the message button', async ({ page }) => {
  76  |     await startNewChat(page)
  77  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  78  |     await mockArtifactGet(page, MOCK_ARTIFACT_ID, artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT))
  79  | 
  80  |     await sendMessage(page, 'Create a markdown checklist')
  81  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  82  |     await expect(viewer).toBeVisible()
  83  | 
  84  |     // Close
  85  |     await viewer.getByRole('button', { name: 'Close artifact viewer' }).click()
  86  |     await expect(viewer).toHaveCount(0)
  87  | 
  88  |     // Reopen via the persisted-artifact button (real GET /api/artifacts/{id})
  89  |     await page.getByRole('button', { name: 'View Artifact' }).click()
  90  |     await expect(viewer).toBeVisible()
  91  |     await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
  92  |   })
  93  | 
  94  |   test('version switching shows previous version content', async ({ page }) => {
  95  |     await startNewChat(page)
  96  |     const v1 = artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT, 1)
  97  |     const v2 = artifactPayload(MOCK_ARTIFACT_V2_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT_V2, 2)
  98  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_V2_ID))
  99  |     await mockArtifactVersions(page, 'Checklist', [v1, v2])
  100 | 
  101 |     await sendMessage(page, 'Update the checklist with owners')
  102 |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  103 |     await expect(viewer).toBeVisible()
  104 | 
  105 |     // Current artifact is v2
  106 |     const versionSelect = viewer.getByLabel('Artifact version')
  107 |     await expect(versionSelect).toBeVisible()
  108 |     await expect(versionSelect).toHaveValue(MOCK_ARTIFACT_V2_ID)
  109 | 
  110 |     // Switch to v1 and verify content swaps
  111 |     await versionSelect.selectOption({ label: 'v1' })
  112 |     await expect(viewer.getByRole('heading', { name: 'Growth Checklist', exact: true })).toBeVisible()
  113 |     await expect(viewer.getByText('Instrument the funnel', { exact: true })).toBeVisible()
  114 | 
  115 |     // Switch back to v2
  116 |     await versionSelect.selectOption({ label: 'v2' })
  117 |     await expect(viewer.getByText('Instrument the funnel (Data)')).toBeVisible()
  118 |   })
  119 | 
  120 |   test('raw/preview toggle shows source and rendered views', async ({ page }) => {
  121 |     await startNewChat(page)
  122 |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  123 | 
  124 |     await sendMessage(page, 'Create a markdown checklist')
  125 |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  126 |     await expect(viewer).toBeVisible()
  127 | 
  128 |     // Raw mode shows the markdown source as text
  129 |     await viewer.getByRole('button', { name: 'Show raw code' }).click()
  130 |     await expect(viewer.locator('pre')).toContainText('# Growth Checklist')
  131 | 
  132 |     // Back to preview
  133 |     await viewer.getByRole('button', { name: 'Show preview' }).click()
  134 |     await expect(viewer.getByRole('heading', { name: 'Growth Checklist' })).toBeVisible()
  135 |   })
  136 | 
  137 |   test('loading state disables input while streaming', async ({ page }) => {
  138 |     await startNewChat(page)
  139 |     await page.route('**/api/chat', async route => {
  140 |       await new Promise(resolve => setTimeout(resolve, 2500))
  141 |       await route.fulfill({
  142 |         status: 200,
  143 |         headers: { 'Content-Type': 'text/event-stream' },
  144 |         body: '',
  145 |       })
  146 |     })
  147 | 
  148 |     await sendMessage(page, 'Hello')
  149 | 
  150 |     const textarea = page.locator('textarea')
  151 |     await expect(textarea).toBeDisabled()
  152 |     await expect(page.getByPlaceholder('Streaming...')).toBeVisible()
  153 |     await expect(textarea).toBeEnabled({ timeout: 15_000 })
  154 |   })
```