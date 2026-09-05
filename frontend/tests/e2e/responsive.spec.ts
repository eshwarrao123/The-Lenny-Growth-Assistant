import { test, expect } from '@playwright/test'
import {
  MOCK_ARTIFACT_ID,
  createSession,
  groundedQaEvents,
  htmlArtifactEvents,
  mockChatStream,
  sendMessage,
  startNewChat,
} from './helpers'

async function openHtmlArtifact(page: import('@playwright/test').Page): Promise<void> {
  await startNewChat(page)
  await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))
  await sendMessage(page, 'Create an HTML calculator')
  await expect(page.getByRole('region', { name: 'Artifact viewer' })).toBeVisible()
}

async function assertNoHorizontalOverflow(page: import('@playwright/test').Page): Promise<void> {
  const overflow = await page.evaluate(() => ({
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  expect(
    overflow.documentScrollWidth,
    `document overflows horizontally (${overflow.documentScrollWidth} > ${overflow.innerWidth})`
  ).toBeLessThanOrEqual(overflow.innerWidth + 1)
  expect(
    overflow.bodyScrollWidth,
    `body overflows horizontally (${overflow.bodyScrollWidth} > ${overflow.innerWidth})`
  ).toBeLessThanOrEqual(overflow.innerWidth + 1)
}

test.describe('Responsive layouts', () => {
  test('desktop 1440x900: split pane, chat and artifact viewer usable', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await openHtmlArtifact(page)

    // Split-pane: chat pane and artifact pane side by side
    const chatBox = await page.locator('.chat-pane-host').boundingBox()
    const viewerBox = await page.getByRole('region', { name: 'Artifact viewer' }).boundingBox()
    expect(chatBox).not.toBeNull()
    expect(viewerBox).not.toBeNull()
    expect(chatBox!.width).toBeGreaterThan(400)
    expect(viewerBox!.width).toBeGreaterThan(300)
    expect(chatBox!.x + chatBox!.width).toBeLessThanOrEqual(viewerBox!.x + 5)

    // Iframe visible inside the viewer
    await expect(
      page.getByRole('region', { name: 'Artifact viewer' }).locator('iframe')
    ).toBeVisible()

    await assertNoHorizontalOverflow(page)
    await expect(page.locator('textarea')).toBeInViewport()
    await expect(page.getByRole('button', { name: 'Send message' })).toBeInViewport()
  })

  test('tablet 768x1024: split pane works with collapsible sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await openHtmlArtifact(page)

    // Split-pane still applies at md+
    const viewerBox = await page.getByRole('region', { name: 'Artifact viewer' }).boundingBox()
    expect(viewerBox!.width).toBeGreaterThan(250)

    // Sidebar collapse/expand still usable
    const aside = page.locator('aside')
    await page.getByRole('button', { name: 'Collapse sidebar' }).click()
    await expect(aside).toHaveClass(/md:w-16/)
    await page.getByRole('button', { name: 'Expand sidebar' }).click()
    await expect(aside).toHaveClass(/md:w-72/)

    await assertNoHorizontalOverflow(page)
    await expect(page.locator('textarea')).toBeInViewport()
  })

  test('mobile 375x667: drawer nav + full-screen artifact panel, no overflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Sidebar is an off-canvas drawer; hamburger opens it
    const aside = page.locator('aside')
    let box = await aside.boundingBox()
    expect(box!.x, 'drawer should start off-screen').toBeLessThan(0)

    await page.getByRole('button', { name: 'Open navigation menu' }).click()
    box = await aside.boundingBox()
    expect(box!.x, 'drawer should slide in').toBe(0)
    await expect(aside.locator('button.btn-primary')).toBeInViewport()

    // New chat from the drawer works on mobile
    await createSession(page)

    // Backdrop click closes the drawer (click the strip right of the 288px drawer)
    await page.locator('div.fixed.inset-0.z-30').click({ position: { x: 340, y: 300 } })
    box = await aside.boundingBox()
    expect(box!.x, 'drawer should slide out').toBeLessThan(0)

    // Chat remains usable
    await mockChatStream(page, groundedQaEvents())
    await sendMessage(page, 'What improves retention?')
    await expect(page.getByText(/Elena Verna recommends/)).toBeVisible()
    await expect(page.locator('textarea')).toBeInViewport()

    // Artifact opens as a full-width panel
    await mockChatStream(page, htmlArtifactEvents(MOCK_ARTIFACT_ID))
    await sendMessage(page, 'Create an HTML calculator')
    const viewer = page.getByRole('region', { name: 'Artifact viewer' })
    await expect(viewer).toBeVisible()
    const viewerBox = await viewer.boundingBox()
    expect(viewerBox!.width, 'artifact panel should span the full mobile width').toBe(375)
    await expect(viewer.locator('iframe')).toBeVisible()

    // Close button returns to chat
    await viewer.getByRole('button', { name: 'Close artifact viewer' }).click()
    await expect(viewer).toHaveCount(0)

    await assertNoHorizontalOverflow(page)

    // Buttons remain accessible and text remains readable
    await expect(page.getByRole('button', { name: 'Send message' })).toBeInViewport()
    const bodyFontSize = await page.evaluate(
      () => parseFloat(getComputedStyle(document.body).fontSize)
    )
    expect(bodyFontSize).toBeGreaterThanOrEqual(12)
  })
})

