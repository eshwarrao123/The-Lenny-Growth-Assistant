import { test, expect } from '@playwright/test'
import {
  HTML_ARTIFACT,
  MARKDOWN_ARTIFACT,
  MARKDOWN_ARTIFACT_V2,
  MOCK_ARTIFACT_ID,
  MOCK_ARTIFACT_V2_ID,
  artifactPayload,
  htmlArtifactEvents,
  markdownArtifactEvents,
  mockArtifactVersions,
  mockChatStream,
  sendMessage,
  startNewChat,
} from './helpers'

test.describe('Accessibility', () => {
  test('artifact controls expose useful accessible names', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()
    await expect(viewer.getByRole('button', { name: 'Close artifact viewer' })).toBeVisible()
    await expect(viewer.getByRole('button', { name: 'Copy content' })).toBeVisible()
    await expect(viewer.getByRole('button', { name: 'Download artifact' })).toBeVisible()
    await expect(viewer.getByRole('button', { name: 'Show raw code' })).toBeVisible()
  })

  test('HTML artifact iframe has a title', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create an HTML calculator')

    const iframe = page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')
    await expect(iframe).toBeVisible()
    const title = await iframe.getAttribute('title')
    expect(title, 'iframe must have a non-empty title').toBeTruthy()
    expect(title!.length).toBeGreaterThan(0)
    await expect(iframe).toHaveAccessibleName(title!)
  })

  test('close button is keyboard operable and Escape closes the viewer', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Keyboard-activate the close button
    await viewer.getByRole('button', { name: 'Close artifact viewer' }).focus()
    await page.keyboard.press('Enter')
    await expect(viewer).toHaveCount(0)

    // Reopen and close with Escape
    await page.getByRole('button', { name: 'View Artifact' }).click()
    await expect(viewer).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(viewer).toHaveCount(0)
  })

  test('version switcher is labelled for assistive tech', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_V2_ID))
    await mockArtifactVersions(page, 'Checklist', [
      artifactPayload(MOCK_ARTIFACT_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT, 1),
      artifactPayload(MOCK_ARTIFACT_V2_ID, 'markdown', 'Checklist', MARKDOWN_ARTIFACT_V2, 2),
    ])

    await sendMessage(page, 'Update the checklist with owners')

    // Version switcher is now a button group with proper ARIA labels
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    const versionGroup = viewer.getByRole('group', { name: 'Artifact version' })
    await expect(versionGroup).toBeVisible()
    
    // Verify individual version buttons are accessible
    const v1Button = versionGroup.getByRole('button', { name: 'Version 1' })
    const v2Button = versionGroup.getByRole('button', { name: 'Version 2' })
    await expect(v1Button).toBeVisible()
    await expect(v2Button).toBeVisible()
    
    // v2 should be active (pressed state)
    await expect(v2Button).toHaveAttribute('aria-pressed', 'true')
  })

  test('visible focus rings on artifact controls when tabbing', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Keyboard-focus the raw toggle and confirm a visible focus indicator
    const rawToggle = viewer.getByRole('button', { name: 'Show raw code' })
    await rawToggle.focus()
    await page.keyboard.press('Shift+Tab') // move backwards then forwards to force focus-visible
    await page.keyboard.press('Tab')

    const focusStyle = await page.evaluate(() => {
      const el = document.activeElement
      if (!el) return { outline: 'none', shadow: 'none' }
      const cs = getComputedStyle(el)
      return { outline: cs.outlineStyle, shadow: cs.boxShadow }
    })
    const hasVisibleFocus =
      focusStyle.shadow !== 'none' || focusStyle.outline !== 'none'
    expect(hasVisibleFocus, 'keyboard focus must be visible (ring or outline)').toBe(true)
  })

  test('no obvious keyboard trap: tabbing reaches chat and viewer controls', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create a markdown checklist')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()

    // Walk focus with Tab and collect the focused elements
    const visited: string[] = []
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press('Tab')
      const tag = await page.evaluate(() => {
        const el = document.activeElement
        if (!el) return 'none'
        const label = el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 20) || ''
        return `${el.tagName.toLowerCase()}:${label}`
      })
      visited.push(tag)
    }

    const distinct = new Set(visited)
    expect(
      distinct.size,
      `focus should move freely, visited: ${visited.join(' -> ')}`
    ).toBeGreaterThanOrEqual(5)

    // Focus must be able to reach and type into the chat textarea (no trap)
    await page.locator('textarea').focus()
    await page.keyboard.type('a')
    await expect(page.locator('textarea')).toBeFocused()
    await page.keyboard.press('Backspace')
  })
})
