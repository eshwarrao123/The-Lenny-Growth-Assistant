import { test, expect } from '@playwright/test'
import {
  MALICIOUS_HTML_ARTIFACT,
  MOCK_ARTIFACT_ID,
  XSS_MARKDOWN_ARTIFACT,
  htmlArtifactEvents,
  markdownArtifactEvents,
  mockChatStream,
  sendMessage,
  startNewChat,
} from './helpers'

test.describe('Artifact sandbox security', () => {
  test('HTML artifact iframe uses sandbox="allow-scripts" without allow-same-origin', async ({ page }) => {
    await startNewChat(page)
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))

    await sendMessage(page, 'Create an HTML calculator')

    const iframe = page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')
    await expect(iframe).toBeVisible()

    const sandboxAttr = await iframe.getAttribute('sandbox')
    expect(sandboxAttr, 'sandbox attribute must be present').toBeTruthy()
    expect(sandboxAttr).toContain('allow-scripts')
    expect(sandboxAttr, 'allow-same-origin is strictly prohibited').not.toContain('allow-same-origin')

    // No extra permissions granted to untrusted content
    const allowAttr = await iframe.getAttribute('allow')
    expect(allowAttr).toBeNull()
  })

  test('malicious artifact cannot access parent document, storage, cookies or top window', async ({ page }) => {
    await startNewChat(page)

    // Plant parent-side canaries that the artifact must not be able to touch
    await page.evaluate(() => {
      ;(window as unknown as { __sandboxCanary: number }).__sandboxCanary = 42
      document.cookie = 'lenny_canary=safe; path=/'
      localStorage.setItem('lenny_canary', 'safe')
    })
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID, MALICIOUS_HTML_ARTIFACT, 'Sneaky'))

    // Collect console output produced by the artifact's script
    const consoleTexts: string[] = []
    page.on('console', msg => consoleTexts.push(msg.text()))

    await sendMessage(page, 'Create an HTML calculator')

    const iframe = page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')
    await expect(iframe).toBeVisible()
    // The artifact itself renders (its own DOM is intact)
    await expect(iframe.contentFrame().locator('#proof')).toHaveText('Sneaky artifact')

    // Give the artifact script time to run its escape attempts
    await page.waitForTimeout(1500)

    const breaches = consoleTexts.filter(t => t.includes('BREACH:'))
    expect(breaches, `sandbox breaches reported: ${breaches.join(' | ')}`).toEqual([])

    const isolated = consoleTexts.filter(t => t.includes('ISOLATED:'))
    expect(isolated.length, 'expected the artifact script to run and report isolation').toBeGreaterThanOrEqual(5)

    // Parent-side state is untouched
    const parentState = await page.evaluate(() => ({
      canary: (window as unknown as { __sandboxCanary: number }).__sandboxCanary,
      cookie: document.cookie,
      localStorageHacked: localStorage.getItem('hacked'),
      localStorageCanary: localStorage.getItem('lenny_canary'),
      url: window.location.href,
      bodyMarker: document.body.textContent?.includes('HACKED') ?? false,
    }))
    expect(parentState.canary).toBe(42)
    expect(parentState.cookie).not.toContain('hacked')
    expect(parentState.cookie).toContain('lenny_canary=safe')
    expect(parentState.localStorageHacked).toBeNull()
    expect(parentState.localStorageCanary).toBe('safe')
    expect(parentState.url).not.toContain('attacker.invalid')
    expect(parentState.bodyMarker).toBe(false)

    // Sandbox attribute still correct
    const sandboxAttr = await iframe.getAttribute('sandbox')
    expect(sandboxAttr).toContain('allow-scripts')
    expect(sandboxAttr).not.toContain('allow-same-origin')
  })

  test('markdown artifact does not execute scripts or inject handlers (XSS-safe)', async ({ page }) => {
    await startNewChat(page)

    const dialogs: string[] = []
    page.on('dialog', dialog => {
      dialogs.push(dialog.message())
      void dialog.dismiss()
    })

    await mockChatStream(page, markdownArtifactEvents(MOCK_ARTIFACT_ID, XSS_MARKDOWN_ARTIFACT, 'XSS Test'))

    await sendMessage(page, 'Create a markdown doc')

    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()
    // Legit markdown still renders through the safe pipeline
    await expect(viewer.getByRole('heading', { name: 'Safe Heading' })).toBeVisible()
    await expect(viewer.getByText('Regular markdown content should render.')).toBeVisible()

    await page.waitForTimeout(1000)

    // No script iframes, no script tags, no inline event handlers, no js: URLs
    const audit = await page.evaluate(() => {
      const region = document.querySelector('[aria-label="Artifact viewer"]')
      if (!region) return { ok: false as const }
      const scripts = region.querySelectorAll('script')
      const iframes = region.querySelectorAll('iframe')
      const eventAttrEls = Array.from(region.querySelectorAll('*')).filter(el =>
        Array.from(el.attributes).some(a => a.name.toLowerCase().startsWith('on'))
      )
      const jsUrls = Array.from(region.querySelectorAll('a[href], img[src]')).filter(el => {
        const v = el.getAttribute('href') || el.getAttribute('src') || ''
        return v.trim().toLowerCase().startsWith('javascript:')
      })
      return {
        ok: true as const,
        scripts: scripts.length,
        iframes: iframes.length,
        eventAttrEls: eventAttrEls.length,
        jsUrls: jsUrls.length,
      }
    })
    expect(audit).toEqual({ ok: true, scripts: 0, iframes: 0, eventAttrEls: 0, jsUrls: 0 })

    // No alert/confirm/prompt fired anywhere
    expect(dialogs, `dialogs were opened: ${dialogs.join(', ')}`).toEqual([])
  })
})
