import { createRequire } from 'node:module'
import { readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const require = createRequire(import.meta.url)
export const webOrigin = process.env.FLEETRENT_E2E_WEB || 'http://127.0.0.1:5188'

export function readFixture() {
  return JSON.parse(
    readFileSync(
      process.env.FLEETRENT_E2E_FIXTURE || join(tmpdir(), 'supplier-workspace-fixture.json'),
      'utf8',
    ),
  )
}

export function launchBrowser() {
  const { chromium } = require(process.env.FLEETRENT_PLAYWRIGHT_PACKAGE || 'playwright')
  return chromium.launch({
    executablePath: process.env.FLEETRENT_CHROME || undefined,
    headless: true,
  })
}

export function routeFixtureApi(page, failures = []) {
  return page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const url = new URL(route.request().url())
      try {
        const response = await route.fetch({
          url: 'http://127.0.0.1:8088' + url.pathname + url.search,
          timeout: 10000,
        })
        if (response.status() >= 500) failures.push(`${url.pathname}: ${response.status()}`)
        await route.fulfill({ response })
      } catch {
        if (!page.isClosed()) throw new Error(`Fixture API isteği tamamlanamadı: ${url.pathname}`)
      }
    },
  )
}

export async function closeFixtureContext(context) {
  for (const page of context.pages()) await page.unrouteAll({ behavior: 'wait' })
  await context.close()
}
