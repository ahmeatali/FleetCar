// Run with the isolated supplier fixture server, never a production account.
import assert from 'node:assert/strict'
import { mkdirSync } from 'node:fs'
import { launchBrowser, readFixture } from './helpers/browserFixture.mjs'
const tokens = readFixture()
const browser = await launchBrowser()
const web = process.env.FLEETRENT_E2E_WEB || 'http://127.0.0.1:5188'
const backend = process.env.FLEETRENT_E2E_API || 'http://127.0.0.1:8088'
const output = process.env.FLEETRENT_E2E_OUTPUT || '/tmp/fleet-planning-previews'
mkdirSync(output, { recursive: true })
const run = Date.now()
const errors = []
const serverFailures = []
const day = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(new Date())
const offset = (n) => {
  const d = new Date(day + 'T12:00:00Z')
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}
async function session(token, width = 1440) {
  const ctx = await browser.newContext({ viewport: { width, height: 1000 } })
  await ctx.addInitScript((token) => {
    localStorage.setItem('fleetcar_supplier_token', token)
    localStorage.setItem('fleetcar_supplier_id', '1')
    localStorage.setItem('fleetcar_supplier_type', 'ikame_arac')
  }, token)
  const page = await ctx.newPage()
  page.on('pageerror', (e) => errors.push(e.message))
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const url = new URL(route.request().url())
      const response = await route.fetch({ url: backend + url.pathname + url.search })
      if (response.status() >= 500) serverFailures.push(url.pathname + ': ' + response.status())
      await route.fulfill({ response })
    },
  )
  return { ctx, page }
}
try {
  const { ctx, page } = await session(tokens.token)
  await page.goto(web + '/supplier-portal/branches')
  await page.getByRole('heading', { name: 'Şubeler ve Lokasyonlar', exact: true }).waitFor()
  const branches = []
  for (const suffix of ['Merkez', 'Havalimanı']) {
    const name = `E2E ${run} ${suffix}`
    await page.getByLabel('Şube Adı', { exact: true }).fill(name)
    await page.getByLabel('Şehir', { exact: true }).fill('İstanbul')
    await page.getByRole('button', { name: 'Şube Ekle', exact: true }).click()
    await page.getByRole('cell').filter({ hasText: name }).first().waitFor()
    branches.push(name)
  }
  const overview = await (
    await page.request.get(backend + '/api/supplier-workspace/fleet/overview', {
      headers: { Authorization: `Bearer ${tokens.token}` },
    })
  ).json()
  const branch = overview.branches.find((b) => b.name === branches[0])
  const second = overview.branches.find((b) => b.name === branches[1])
  const car = overview.vehicles.find((v) => v.id === 'car2')
  await page
    .getByRole('row')
    .filter({ hasText: car.plate })
    .getByRole('button', { name: 'Lokasyonu Düzenle', exact: true })
    .click()
  await page.getByLabel('Bağlı Şube', { exact: true }).selectOption(String(branch.id))
  await page.getByLabel('Bulunduğu Şube', { exact: true }).selectOption(String(branch.id))
  await page.getByLabel('Konum Notu', { exact: true }).fill('Otopark A')
  await page.getByRole('button', { name: 'Lokasyonu Kaydet', exact: true }).click()
  await page.getByText('Araç lokasyonu kaydedildi.', { exact: true }).waitFor()
  await page.screenshot({ path: output + '/branches-desktop.png', fullPage: true })
  await page.goto(web + '/supplier-portal/reservations')
  await page.getByRole('heading', { name: 'Yeni Rezervasyon', exact: true }).waitFor()
  await page.getByLabel('Müşteri', { exact: true }).selectOption('1')
  await page.getByLabel('Rezervasyon Aracı', { exact: true }).selectOption('car2')
  await page.getByLabel('Teslim Şubesi', { exact: true }).selectOption(String(branch.id))
  await page.getByLabel('Dönüş Şubesi', { exact: true }).selectOption(String(second.id))
  await page.getByLabel('Rezervasyon Başlangıcı', { exact: true }).fill(offset(3))
  await page.getByLabel('Rezervasyon Bitişi', { exact: true }).fill(offset(8))
  await page.getByLabel('Aylık Kira (TL)', { exact: true }).fill('25000')
  await page.getByRole('button', { name: 'Rezervasyon Oluştur', exact: true }).click()
  await page.getByText('Rezervasyon oluşturuldu.', { exact: true }).waitFor()
  const reserved = page
    .getByRole('row')
    .filter({ has: page.getByRole('button', { name: 'Sözleşme Taslağı Oluştur', exact: true }) })
    .first()
  await reserved.waitFor()
  await page.locator('.fp-booked').first().waitFor()
  // Same dates must be rejected, including when the UI's calendar was loaded earlier.
  await page.getByRole('button', { name: 'Rezervasyon Oluştur', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'çakışıyor' }).waitFor()
  await reserved.getByRole('button', { name: 'Sözleşme Taslağı Oluştur', exact: true }).click()
  await page
    .getByText(
      'Sözleşme taslağı oluşturuldu. Mevcut imza ve onay adımları sözleşme ekranından devam eder.',
      { exact: true },
    )
    .waitFor()
  await page.getByRole('link', { name: 'Sözleşmeyi Aç', exact: true }).waitFor()
  await page.locator('.fp-contracted').first().waitFor()
  await page.screenshot({ path: output + '/reservations-desktop.png', fullPage: true })
  await page.goto(web + '/supplier-portal/operations')
  await page.getByRole('heading', { name: 'Yeni Operasyon Görevi', exact: true }).waitFor()
  await page.getByLabel('Görev Başlığı', { exact: true }).fill('E2E araç hazırlığı ' + run)
  await page.getByLabel('Son Tarih', { exact: true }).fill(day)
  await page.getByLabel('Görev Aracı', { exact: true }).selectOption('car2')
  await page.getByLabel('Görev Şubesi', { exact: true }).selectOption(String(branch.id))
  await page.getByLabel('Sorumlu Kullanıcı', { exact: true }).selectOption('1')
  const createdTask = page.waitForResponse(
    (r) => r.url().includes('/fleet/tasks') && r.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Görev Ekle', exact: true }).click()
  const createdResponse = await createdTask
  assert.equal(createdResponse.status(), 200, await createdResponse.text())
  await page.getByText('Görev kaydedildi.', { exact: true }).waitFor()
  const task = page.getByRole('row').filter({ hasText: 'E2E araç hazırlığı ' + run })
  await task.waitFor()
  await task.getByRole('button', { name: 'Görevi Düzenle', exact: true }).click()
  await page.getByLabel('Görev Durumu', { exact: true }).selectOption('Tamamlandı')
  await page.getByRole('button', { name: 'Görevi Kaydet', exact: true }).click()
  await page.getByText('Görev kaydedildi.', { exact: true }).waitFor()
  await page.getByLabel('Görünüm', { exact: true }).selectOption('done')
  await task.waitFor()
  await page.screenshot({ path: output + '/tasks-desktop.png', fullPage: true })
  for (const section of ['branches', 'reservations', 'operations']) {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto(web + '/supplier-portal/' + section)
    await page.locator('.fp-workspace .sw-card').first().waitFor()
    await page.waitForTimeout(350)
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth),
      false,
      section + ' mobile overflow',
    )
    await page.screenshot({ path: output + '/' + section + '-mobile.png', fullPage: true })
  }
  const viewer = await session(tokens.viewer_token)
  for (const section of ['branches', 'reservations', 'operations']) {
    await viewer.page.goto(web + '/supplier-portal/' + section)
    await viewer.page.locator('.fp-workspace .sw-card').first().waitFor()
    assert.equal(
      await viewer.page
        .getByRole('button', {
          name: /Şube Ekle|Rezervasyon Oluştur|Görev Ekle|Lokasyonu Düzenle|Sözleşme Taslağı Oluştur/,
        })
        .count(),
      0,
    )
  }
  await page.goto(web + '/supplier-portal')
  await page.getByRole('heading', { name: 'Günlük Operasyon İş Listesi', exact: true }).waitFor()
  assert.deepEqual(errors, [])
  assert.deepEqual(serverFailures, [])
  await viewer.ctx.close()
  await ctx.close()
  console.log(
    'PASS: branches, location assignment, reservation/collision/conversion, calendar, assigned tasks/completion, home summary, mobile layouts and viewer permissions',
  )
} finally {
  await browser.close()
}
