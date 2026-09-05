# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: accessibility.spec.ts >> Accessibility >> no obvious keyboard trap: tabbing reaches chat and viewer controls
- Location: tests\e2e\accessibility.spec.ts:118:7

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
  25  |     await expect(viewer).toBeVisible()
  26  |     await expect(viewer.getByRole('button', { name: 'Close artifact viewer' })).toBeVisible()
  27  |     await expect(viewer.getByRole('button', { name: 'Copy content' })).toBeVisible()
  28  |     await expect(viewer.getByRole('button', { name: 'Download artifact' })).toBeVisible()
  29  |     await expect(viewer.getByRole('button', { name: 'Show raw code' })).toBeVisible()
  30  |   })
  31  | 
  32  |   test('HTML artifact iframe has a title', async ({ page }) => {
  33  |     await startNewChat(page)
  34  |     await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))
  35  | 
  36  |     await sendMessage(page, 'Create an HTML calculator')
  37  | 
  38  |     const iframe = page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')
  39  |     await expect(iframe).toBeVisible()
  40  |     const title = await iframe.getAttribute('title')
  41  |     expect(title, 'iframe must have a non-empty title').toBeTruthy()
  42  |     expect(title!.length).toBeGreaterThan(0)
  43  |     await expect(iframe).toHaveAccessibleName(title!)
  44  |   })
  45  | 
  46  |   test('close button is keyboard operable and Escape closes the viewer', async ({ page }) => {
  47  |     await startNewChat(page)
  48  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  49  | 
  50  |     await sendMessage(page, 'Create a markdown checklist')
  51  | 
  52  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  53  |     await expect(viewer).toBeVisible()
  54  | 
  55  |     // Keyboard-activate the close button
  56  |     await viewer.getByRole('button', { name: 'Close artifact viewer' }).focus()
  57  |     await page.keyboard.press('Enter')
  58  |     await expect(viewer).toHaveCount(0)
  59  | 
  60  |     // Reopen and close with Escape
  61  |     await page.getByRole('button', { name: 'View Artifact' }).click()
  62  |     await expect(viewer).toBeVisible()
  63  |     await page.keyboard.press('Escape')
  64  |     await expect(viewer).toHaveCount(0)
  65  |   })
  66  | 
  67  |   test('version switcher is labelled for assistive tech', async ({ page }) => {
  68  |     await startNewChat(page)
  69  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_V2_ID))
  70  |     await mockArtifactVersions(page, 'Checklist', [
  71  |       artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT, 1),
  72  |       artifactPayload(MOCK_ARTIFACT_V2_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT_V2, 2),
  73  |     ])
  74  | 
  75  |     await sendMessage(page, 'Update the checklist with owners')
  76  | 
  77  |     // Version switcher is now a button group with proper ARIA labels
  78  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  79  |     const versionGroup = viewer.getByRole('group', { name: 'Artifact version' })
  80  |     await expect(versionGroup).toBeVisible()
  81  |     
  82  |     // Verify individual version buttons are accessible
  83  |     const v1Button = versionGroup.getByRole('button', { name: 'Version 1' })
  84  |     const v2Button = versionGroup.getByRole('button', { name: 'Version 2' })
  85  |     await expect(v1Button).toBeVisible()
  86  |     await expect(v2Button).toBeVisible()
  87  |     
  88  |     // v2 should be active (pressed state)
  89  |     await expect(v2Button).toHaveAttribute('aria-pressed', 'true')
  90  |   })
  91  | 
  92  |   test('visible focus rings on artifact controls when tabbing', async ({ page }) => {
  93  |     await startNewChat(page)
  94  |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  95  | 
  96  |     await sendMessage(page, 'Create a markdown checklist')
  97  | 
  98  |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
  99  |     await expect(viewer).toBeVisible()
  100 | 
  101 |     // Keyboard-focus the raw toggle and confirm a visible focus indicator
  102 |     const rawToggle = viewer.getByRole('button', { name: 'Show raw code' })
  103 |     await rawToggle.focus()
  104 |     await page.keyboard.press('Shift+Tab') // move backwards then forwards to force focus-visible
  105 |     await page.keyboard.press('Tab')
  106 | 
  107 |     const focusStyle = await page.evaluate(() => {
  108 |       const el = document.activeElement
  109 |       if (!el) return { outline: 'none', shadow: 'none' }
  110 |       const cs = getComputedStyle(el)
  111 |       return { outline: cs.outlineStyle, shadow: cs.boxShadow }
  112 |     })
  113 |     const hasVisibleFocus =
  114 |       focusStyle.shadow !== 'none' || focusStyle.outline !== 'none'
  115 |     expect(hasVisibleFocus, 'keyboard focus must be visible (ring or outline)').toBe(true)
  116 |   })
  117 | 
  118 |   test('no obvious keyboard trap: tabbing reaches chat and viewer controls', async ({ page }) => {
  119 |     await startNewChat(page)
  120 |     await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))
  121 | 
  122 |     await sendMessage(page, 'Create a markdown checklist')
  123 | 
  124 |     const viewer = page.getByRole('region', { name: 'Artifact viewer' })
> 125 |     await expect(viewer).toBeVisible()
      |                          ^ Error: expect(locator).toBeVisible() failed
  126 | 
  127 |     // Walk focus with Tab and collect the focused elements
  128 |     const visited: string[] = []
  129 |     for (let i = 0; i < 12; i++) {
  130 |       await page.keyboard.press('Tab')
  131 |       const tag = await page.evaluate(() => {
  132 |         const el = document.activeElement
  133 |         if (!el) return 'none'
  134 |         const label = el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 20) || ''
  135 |         return `${el.tagName.toLowerCase()}:${label}`
  136 |       })
  137 |       visited.push(tag)
  138 |     }
  139 | 
  140 |     const distinct = new Set(visited)
  141 |     expect(
  142 |       distinct.size,
  143 |       `focus should move freely, visited: ${visited.join(' -> ')}`
  144 |     ).toBeGreaterThanOrEqual(5)
  145 | 
  146 |     // Focus must be able to reach and type into the chat textarea (no trap)
  147 |     await page.locator('textarea').focus()
  148 |     await page.keyboard.type('a')
  149 |     await expect(page.locator('textarea')).toBeFocused()
  150 |     await page.keyboard.press('Backspace')
  151 |   })
  152 | })
  153 | 
```