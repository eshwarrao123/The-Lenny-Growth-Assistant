import { defineConfig } from '@playwright/test'

/**
 * Playwright configuration for the Lenny Growth Assistant E2E suite.
 *
 * The suite targets the REAL running stack:
 *   - PostgreSQL 16 (docker compose, port 5432)
 *   - FastAPI backend (uvicorn, port 8000)
 *   - Next.js frontend (next dev, port 3000)
 *   - Ollama (port 11434)
 *
 * Start these before running: `npx playwright test` from ./frontend.
 * Only the `real-ollama` spec exercises real LLM generation; the other specs
 * stub the /api/chat SSE stream for determinism while still using the real
 * backend for sessions and the real frontend rendering pipeline.
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    viewport: { width: 1440, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
})
