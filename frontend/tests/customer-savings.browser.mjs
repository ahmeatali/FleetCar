import assert from 'node:assert/strict'
import { launchBrowser, webOrigin } from './helpers/browserFixture.mjs'
import { mkdirSync } from 'node:fs'

const browser = await launchBrowser()
const out = process.env.FLEETRENT_E2E_OUTPUT || '/tmp/customer-savings-previews'
mkdirSync(out, { recursive: true })
const car = {
  id: 'customer-car',
  plate: '34 TEST 01',
  is_active: true,
  customer_id: 1,
  current_month_km: 100,
  monthly_km_limit: 50,
  monthly_rent: 2000,
  hgs_no: '123',
  hgs_balance: 20,
}
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    acceptDownloads: true,
  })
  await context.addInitScript(() => {
    localStorage.setItem('fleetcar_token', 'customer-test-token')
    localStorage.setItem('fleetcar_supplier_token', 'supplier-test-token')
  })
  const page = await context.newPage(),
    errors = [],
    calls = []
  page.on('pageerror', (error) => errors.push(error.message))
  let fail = false,
    empty = false
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const path = new URL(route.request().url()).pathname
      calls.push(path)
      assert.equal(route.request().headers().authorization, 'Bearer customer-test-token')
      if (fail)
        return route.fulfill({ status: 503, json: { detail: 'Test: geçici bağlantı hatası' } })
      await route.fulfill({ json: path === '/api/vehicles' && !empty ? [car] : [] })
    },
  )
  await page.goto(webOrigin + '/dashboard/savings')
  await page.getByRole('heading', { name: 'Tespitler ve Öneriler' }).waitFor()
  assert.deepEqual(calls.sort(), ['/api/vehicle-expenses', '/api/vehicles'])
  assert.equal(await page.locator('tbody tr').count(), 3)
  assert.equal(
    await page.getByRole('link', { name: 'Araç Detayı' }).first().getAttribute('href'),
    '/dashboard/vehicles/customer-car',
  )
  await page.getByLabel('Düşük kullanım (km/ay)', { exact: true }).fill('50')
  await page.getByLabel('Düşük HGS bakiyesi (TL)', { exact: true }).fill('10')
  assert.equal(await page.locator('tbody tr').count(), 1)
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'CSV İndir' }).click()
  assert.match((await download).suggestedFilename(), /filo-tespitleri/)
  await page.screenshot({ path: out + '/customer-savings-desktop.png', fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  await page.getByRole('button', { name: 'Müşteri menüsünü aç' }).click()
  await page.getByRole('link', { name: 'Filo Kontrol & Tasarruf', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Menüyü kapat' }).click()
  await page.screenshot({ path: out + '/customer-savings-mobile.png', fullPage: true })
  fail = true
  await page.reload()
  await page.getByText('Test: geçici bağlantı hatası').waitFor()
  assert.equal(await page.locator('tbody').count(), 0)
  fail = false
  empty = true
  await page.getByRole('button', { name: 'Tekrar Dene' }).click()
  await page.getByText('Henüz filonuza atanmış araç bulunmuyor.').waitFor()
  assert.equal(await page.getByRole('button', { name: 'CSV İndir' }).isDisabled(), true)
  await page.goto(webOrigin + '/supplier-portal/savings')
  await page.waitForURL('**/dashboard/savings')
  assert.deepEqual(errors, [])
  const loggedOut = await browser.newContext()
  const signedOutPage = await loggedOut.newPage()
  await signedOutPage.goto(webOrigin + '/supplier-portal/savings')
  await signedOutPage.waitForURL('**/login')
  await loggedOut.close()
  await context.close()
  console.log(
    'CUSTOMER_SAVINGS_BROWSER_OK desktop, mobile, customer token, CSV, thresholds, empty, retry, legacy redirect, login guard',
  )
} finally {
  await browser.close()
}
