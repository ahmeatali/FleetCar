import { launchBrowser, readFixture, routeFixtureApi } from './helpers/browserFixture.mjs'
// Run against supplier_workspace_preview.py only; creates isolated test records.

import { mkdirSync } from 'node:fs'
import assert from 'node:assert/strict'

const runId = Date.now(),
  e2eVehicleId = `E2E${runId}`
const tokens = readFixture()
const browser = await launchBrowser()
const context = await browser.newContext({ viewport: { width: 1536, height: 1024 } })
await context.addInitScript((token) => {
  localStorage.setItem('fleetcar_supplier_token', token)
  localStorage.setItem('fleetcar_supplier_id', '1')
  localStorage.setItem('fleetcar_supplier_type', 'ikame_arac')
  localStorage.setItem('fleetcar_supplier_name', 'ABC Filo Kiralama')
}, tokens.token)
const page = await context.newPage(),
  errors = [],
  failures = []
page.on('pageerror', (e) => errors.push(e.message))
await routeFixtureApi(page, failures)
const root = (process.env.FLEETRENT_E2E_WEB || 'http://127.0.0.1:5188') + '/supplier-portal',
  out = process.env.FLEETRENT_E2E_OUTPUT || '/private/tmp/supplier-workspace-previews'
mkdirSync(out, { recursive: true })
async function visit(section) {
  const loaded = page.waitForResponse((r) => r.url().includes('/supplier-workspace/snapshot'))
  await page.goto(root + (section ? '/' + section : ''))
  await loaded
  await page.locator('h1').waitFor()
  await page.waitForTimeout(150)
  assert.equal(
    await page.locator('.sw-alert.error').count(),
    0,
    section + ': ' + (await page.locator('main').innerText()),
  )
}
async function screen(name) {
  await page.waitForTimeout(250)
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true })
}
async function signCurrent(kind) {
  const rid = new URL(page.url()).searchParams.get('record')
  const box = page.locator('.signed-document-box')
  await box.getByLabel('Islak İmzalı PDF', { exact: true }).setInputFiles(tokens.pdf_path)
  await box.getByRole('button', { name: "İmzalı PDF'yi Kaydet", exact: true }).click()
  await box.getByRole('button', { name: 'Belgeyi ve Şartları Teyit Et', exact: true }).click()
  await box.getByText('Kiralayan Firma: Teyit edildi', { exact: true }).waitFor()
  const envelope = await (
    await page.request.get(
      `http://127.0.0.1:8088/api/supplier-workspace/records/${rid}/signature`,
      { headers: { Authorization: `Bearer ${tokens.token}` } },
    )
  ).json()
  for (const account of kind === 'contract' ? ['customer', 'admin'] : ['customer']) {
    const c = await browser.newContext({ viewport: { width: 1280, height: 900 } })
    await c.addInitScript(
      ({ account, token }) => {
        localStorage.setItem(account === 'admin' ? 'fleetcar_admin_token' : 'fleetcar_token', token)
        localStorage.setItem('fleetcar_customer_id', '1')
        localStorage.setItem('fleetcar_admin_id', '9000')
      },
      { account, token: tokens[account + '_token'] },
    )
    const p = await c.newPage()
    p.on('pageerror', (e) => errors.push(e.message))
    await routeFixtureApi(p, failures)
    await p.goto(
      root.replace('/supplier-portal', '/') +
        (account === 'admin' ? 'admin-portal' : 'dashboard/quotes'),
    )
    const article = p
      .locator('.manual-signature-inbox article')
      .filter({ hasText: envelope.number })
    await article.getByRole('button', { name: 'Belgeyi ve Şartları Teyit Et', exact: true }).click()
    await article
      .getByText((account === 'admin' ? 'FleetRent' : 'Müşteri Firma') + ': Teyit edildi', {
        exact: true,
      })
      .waitFor()
    await c.close()
  }
  await box.getByRole('button', { name: 'Belge Durumunu Yenile', exact: true }).click()
  await box.getByText(/Teyit Edildi|TeyitEdildi/).waitFor()
}
try {
  await page.request.post('http://127.0.0.1:8088/api/supplier-workspace/vehicles', {
    headers: { Authorization: `Bearer ${tokens.token}` },
    data: {
      plate: '35 TEST 003',
      brand: 'Ford',
      model: 'Focus',
      year: 2025,
      fuel: 'Benzin',
      mileage: 12000,
      chassis_no: e2eVehicleId,
      license_serial_no: 'AB123',
      inspection_date: '2027-10-01',
      vehicle_segment: 'C',
      vehicle_type: 'Sedan',
      tire_change_date: '2026-01-01',
      last_service_date: '2026-01-01',
      last_service_mileage: 10000,
    },
  })
  await visit('')
  assert.equal(await page.locator('.sw-dashboard-grid .sw-card').count(), 9)
  await screen('home')
  for (const section of [
    'customers',
    'offers',
    'contracts',
    'rentals',
    'deliveries',
    'returns',
    'sales',
    'maintenance',
    'service',
    'damage',
    'policies',
    'tire',
    'hgs',
    'fines',
    'fuel',
    'invoices',
    'accounting',
    'reports',
    'approvals',
    'planning',
    'users',
    'settings',
  ]) {
    await visit(section)
    assert.ok(await page.locator('h1').innerText())
    assert.ok(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      `${section}: desktop overflow`,
    )
    if (
      [
        'customers',
        'offers',
        'contracts',
        'policies',
        'service',
        'hgs',
        'reports',
        'approvals',
        'planning',
      ].includes(section)
    )
      await screen(section)
  }
  await visit('settings')
  await page.getByRole('tab', { name: 'Entegrasyonlar', exact: true }).click()
  await page.getByRole('heading', { name: 'Entegrasyon Kütüphanesi' }).waitFor()
  assert.equal(await page.getByText('Erişim ve İşlem Sonuçlarını Gör', { exact: true }).count(), 0)
  await page
    .locator('article')
    .filter({ has: page.getByRole('heading', { name: 'Arvento', exact: true }) })
    .getByRole('button')
    .click()
  await page.getByLabel('Cihaz Kimliği Alanı', { exact: true }).fill('Node')
  await page.getByLabel('Konum Zamanı Alanı', { exact: true }).fill('At')
  await page.getByLabel('Enlem Alanı', { exact: true }).fill('Lat')
  await page.getByLabel('Boylam Alanı', { exact: true }).fill('Lon')
  await page.getByRole('button', { name: 'Alan Eşlemesini Kaydet', exact: true }).click()
  await page.getByText('Arvento alan eşlemesi kaydedildi.', { exact: true }).waitFor()
  await page.getByLabel('Arvento Cihaz Kimliği', { exact: true }).fill('browser-device')
  const gpsPanel = page
    .locator('section.sw-settings')
    .filter({ has: page.getByRole('heading', { name: 'Arvento GPS Bağlantısı' }) })
  await gpsPanel.getByLabel('Arvento Aracı', { exact: true }).selectOption('car2')
  await page.getByRole('button', { name: 'Cihazı Eşle', exact: true }).click()
  await gpsPanel.getByRole('cell', { name: 'browser-device', exact: true }).waitFor()
  assert.equal(
    await page.getByRole('button', { name: 'Arvento Verilerini Al', exact: true }).isDisabled(),
    true,
  )
  await screen('arvento-settings')
  await page
    .locator('article')
    .filter({ has: page.getByRole('heading', { name: 'Shell Taşıt Tanıma', exact: true }) })
    .getByRole('button')
    .click()
  await page.getByRole('heading', { name: 'Shell Taşıt Tanıma Bağlantısı', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Bağlantı Ayarlarını Kaydet', exact: true }).click()
  await page.getByText('Shell bağlantı ayarları kaydedildi.', { exact: true }).waitFor()
  await page.getByLabel('Shell Plakası', { exact: true }).fill('34 ABC 123')
  const shellPanel = page
    .locator('section.sw-settings')
    .filter({ has: page.getByRole('heading', { name: 'Shell Taşıt Tanıma Bağlantısı' }) })
  await shellPanel.getByLabel('Shell Aracı', { exact: true }).selectOption('car')
  await page.getByRole('button', { name: 'Plakayı Eşle', exact: true }).click()
  await shellPanel.getByRole('cell', { name: '34ABC123', exact: true }).waitFor()
  assert.equal(
    await page
      .getByRole('button', { name: 'Shell Yakıt Alımlarını Getir', exact: true })
      .isDisabled(),
    true,
  )
  await screen('shell-settings')
  await visit('offers')
  await page.getByRole('button', { name: '＋ Yeni Teklif', exact: true }).click()
  let modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Başlık / Açıklama', { exact: true }).fill('E2E Corolla Teklifi')
  await modal.getByLabel('Müşteri', { exact: true }).selectOption('1')
  await modal.getByLabel('Araç', { exact: true }).selectOption(e2eVehicleId)
  await modal.getByLabel('Araç Başına Aylık Kira (TL)', { exact: true }).fill('32000')
  await modal.getByRole('button', { name: 'Kaydet', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Kayıt kaydedildi.' }).waitFor()
  assert.equal(await page.locator('.sw-form-modal').count(), 0)
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Beklemede', exact: true })
    .click()
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Onayla', exact: true })
    .click()
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Sözleşme Oluştur', exact: true })
    .click()
  modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Araç', { exact: true }).selectOption(e2eVehicleId)
  await modal.getByRole('button', { name: 'Sözleşme Oluştur', exact: true }).click()
  await page.waitForURL(/contracts\?record/)
  const signedContractId = new URL(page.url()).searchParams.get('record')
  await signCurrent('contract')
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Sözleşmeyi Aktifleştir', exact: true })
    .click()
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Teslimat Planla', exact: true })
    .click()
  await page.waitForURL(/deliveries\?record/)
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: '✎ Düzenle', exact: true })
    .click()
  modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Teslim Alan', { exact: true }).fill('E2E Teslim Alan')
  await modal.getByLabel('Teslim Yeri', { exact: true }).fill('İstanbul')
  for (const label of [
    'Araç dış kontrolü',
    'Araç iç kontrolü',
    'Belgeler teslim edildi',
    'Aksesuar ve ekipman kontrolü',
  ])
    await modal.getByLabel(label, { exact: true }).check()
  await modal.getByRole('button', { name: 'Kaydet', exact: true }).click()
  await page.locator('.sw-form-modal').waitFor({ state: 'hidden' })
  await signCurrent('delivery')
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Tamamla', exact: true })
    .click()
  await page.waitForFunction(() =>
    document.querySelector('.sw-detail-panel .sw-detail-title')?.textContent.includes('Tamamlandı'),
  )
  await screen('delivery-completed')
  const customerForms = await (
    await page.request.get('http://127.0.0.1:8088/api/customer/delivery-forms?customer_id=1', {
      headers: { Authorization: `Bearer ${tokens.token}` },
    })
  ).json()
  assert.ok(customerForms.some((f) => f.receiver === 'E2E Teslim Alan'))
  await visit('returns')
  await page.getByRole('button', { name: '＋ İade Kaydı Aç', exact: true }).click()
  modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Başlık / Açıklama', { exact: true }).fill('E2E İade ve Mutabakat')
  await modal.getByLabel('Bağlı Sözleşme', { exact: true }).selectOption(signedContractId)
  await modal.getByLabel('İade Kilometresi', { exact: true }).fill('12500')
  await modal.getByLabel('Yakıt Seviyesi (%)', { exact: true }).fill('40')
  await modal.getByLabel('Hasar Ek Ücreti (TL)', { exact: true }).fill('100')
  await modal.getByLabel('Yakıt Ek Ücreti (TL)', { exact: true }).fill('50')
  await modal.getByLabel('İade Alan', { exact: true }).fill('E2E Depo Görevlisi')
  await modal.getByLabel('İade Konumu', { exact: true }).fill('İstanbul Depo')
  await modal
    .getByLabel('Son Mutabakat Açıklaması', { exact: true })
    .fill('İade incelendi, ücretler kontrol edilerek mutabakat tamamlandı.')
  for (const label of [
    'Araç dış kontrolü',
    'Araç iç kontrolü',
    'Belgeler teslim edildi',
    'Aksesuar ve ekipman kontrolü',
  ])
    await modal.getByLabel(label, { exact: true }).check()
  await modal.getByRole('button', { name: 'Kaydet', exact: true }).click()
  await modal.waitFor({ state: 'hidden' })
  for (const label of ['İnceleniyor', 'Mutabakat Bekliyor', 'Tamamla'])
    await page.locator('.sw-detail-panel').getByRole('button', { name: label, exact: true }).click()
  await page.waitForFunction(() =>
    document.querySelector('.sw-detail-panel .sw-detail-title')?.textContent.includes('Tamamlandı'),
  )
  await screen('return-settlement-completed')
  const returnedCar = await (
    await page.request.get(
      `http://127.0.0.1:8088/api/supplier-workspace/vehicles/${e2eVehicleId}`,
      { headers: { Authorization: `Bearer ${tokens.token}` } },
    )
  ).json()
  assert.equal(returnedCar.customer_id, null)
  assert.equal(returnedCar.mileage, 12500)
  await visit('invoices')
  await page.locator('.sw-table tbody tr').first().click()
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Kesildi Olarak Kaydet', exact: true })
    .click()
  await page
    .locator('.sw-detail-panel')
    .getByRole('button', { name: 'Tahsilat Kaydet', exact: true })
    .click()
  modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Ödeme Tutarı (TL)', { exact: true }).fill('10000')
  await modal.getByRole('button', { name: 'Kaydet', exact: true }).click()
  await visit('accounting')
  assert.ok(
    (await page.locator('.sw-table tbody').innerText()).includes('10000') ||
      (await page.locator('.sw-table tbody').innerText()).includes('10.000'),
  )
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: '⇩ Dışa Aktar', exact: true }).click()
  assert.ok((await download).suggestedFilename().endsWith('.csv'))
  await visit('reports')
  for (const [label, ext] of [
    ['Excel İndir', '.xlsx'],
    ['PDF İndir', '.pdf'],
  ]) {
    const downloaded = page.waitForEvent('download')
    await page.getByRole('button', { name: label, exact: true }).click()
    const file = await downloaded
    assert.ok(file.suggestedFilename().endsWith(ext))
    assert.equal(await file.failure(), null)
  }
  await visit('customers')
  await page.getByRole('button', { name: '＋ Yeni Müşteri', exact: true }).click()
  modal = page.locator('.sw-form-modal')
  await modal.getByLabel('Firma Adı', { exact: true }).fill('E2E Yeni Müşteri')
  await modal.getByLabel('E-posta', { exact: true }).fill(`new-${runId}@example.test`)
  await modal.getByRole('button', { name: 'Kaydet', exact: true }).click()
  await page.getByRole('status').waitFor()
  await page.locator('.sw-detail-panel h3').filter({ hasText: 'E2E Yeni Müşteri' }).waitFor()
  await visit('vehicles')
  await page.locator('.fleet-table tbody tr').first().waitFor()
  assert.ok((await page.locator('.fleet-table tbody tr').count()) >= 2)
  await page.locator('.fleet-plate').first().click()
  await page.getByRole('heading', { name: /BMW 520i/ }).waitFor()
  assert.equal(await page.locator('.detail-error').count(), 0)
  await page.getByRole('button', { name: 'Ticari Geçmiş', exact: true }).click()
  await page.getByRole('heading', { name: 'Ticari İşlem Geçmişi', exact: true }).waitFor()
  // Quick-action links consume their new flag; saving must not reopen the form.
  await visit('fuel?new=1')
  modal = page.locator('.sw-form-modal')
  await modal.getByRole('button', { name: 'Vazgeç', exact: true }).click()
  assert.equal(await page.locator('.sw-form-modal').count(), 0)
  await page.setViewportSize({ width: 390, height: 844 })
  for (const section of ['', 'offers', 'reports', 'contracts', 'planning']) {
    await visit(section)
    assert.ok(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      `${section}: mobile overflow`,
    )
    await screen('mobile-' + (section || 'home'))
  }
  await page.getByRole('button', { name: 'Tedarikçi menüsünü aç' }).click()
  await page
    .locator('aside.portal-sidebar')
    .getByRole('link', { name: 'Müşteriler', exact: true })
    .click()
  await page.getByRole('heading', { name: /Müşteriler/ }).waitFor()
  await page.evaluate(
    (token) => localStorage.setItem('fleetcar_supplier_token', token),
    tokens.viewer_token,
  )
  const viewerLoaded = page.waitForResponse((r) => r.url().includes('/supplier-workspace/snapshot'))
  await page.getByRole('button', { name: 'Tedarikçi menüsünü aç' }).click()
  await page
    .locator('aside.portal-sidebar')
    .getByRole('button', { name: 'Kiralamalar', exact: true })
    .click()
  await page
    .locator('aside.portal-sidebar')
    .getByRole('link', { name: 'Teklifler', exact: true })
    .click()
  await viewerLoaded
  await page.waitForFunction(() =>
    document.querySelector('.sw-profile')?.textContent.includes('Görüntüleyici'),
  )
  assert.equal(await page.getByRole('button', { name: '＋ Yeni Teklif', exact: true }).count(), 0)
  const denied = await page.request.post(
    'http://127.0.0.1:8088/api/supplier-workspace/records/offer',
    {
      headers: { Authorization: `Bearer ${tokens.viewer_token}` },
      data: { title: 'Illegal', date: '2026-10-14', details: {} },
    },
  )
  assert.equal(denied.status(), 403)
  // Customer decisions use a separately authenticated customer browser session.
  const ownerHeaders = { Authorization: `Bearer ${tokens.token}` }
  let customerOffer = await (
    await page.request.post('http://127.0.0.1:8088/api/supplier-workspace/records/offer', {
      headers: ownerHeaders,
      data: {
        title: 'Müşteri Revizyon Testi',
        customer_id: 1,
        vehicle_id: 'car2',
        date: new Date().toLocaleDateString('en-CA'),
        end_date: '2027-12-31',
        amount: 32000,
        details: { months: 24, quantity: 1, annual_km: 30000 },
      },
    })
  ).json()
  customerOffer = await (
    await page.request.post(
      `http://127.0.0.1:8088/api/supplier-workspace/records/${customerOffer.id}/status`,
      { headers: ownerHeaders, data: { version: customerOffer.version, status: 'Beklemede' } },
    )
  ).json()
  const customerContext = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  await customerContext.addInitScript((token) => {
    localStorage.setItem('fleetcar_token', token)
    localStorage.setItem('fleetcar_customer_id', '1')
    localStorage.setItem('fleetcar_customer_name', 'ABC Lojistik')
  }, tokens.customer_token)
  const customerPage = await customerContext.newPage()
  customerPage.on('pageerror', (e) => errors.push(e.message))
  await routeFixtureApi(customerPage, failures)
  await customerPage.goto(root.replace('/supplier-portal', '/dashboard/quotes'))
  let article = customerPage
    .locator('.incoming-offers article')
    .filter({ hasText: 'Müşteri Revizyon Testi' })
  await article.locator('textarea').fill('Aylık kira için revize fiyat istiyoruz.')
  await article.getByRole('button', { name: 'Revizyon İste', exact: true }).click()
  await article.getByText(/Revizyon Bekliyor/).waitFor()
  customerOffer = (
    await (
      await page.request.get('http://127.0.0.1:8088/api/supplier-workspace/records/offer', {
        headers: ownerHeaders,
      })
    ).json()
  ).find((r) => r.id === customerOffer.id)
  assert.equal(customerOffer.raw_status, 'Revizyon Bekliyor')
  customerOffer = await (
    await page.request.put(
      `http://127.0.0.1:8088/api/supplier-workspace/records/${customerOffer.id}`,
      {
        headers: ownerHeaders,
        data: {
          title: customerOffer.title,
          customer_id: 1,
          vehicle_id: 'car2',
          date: customerOffer.date,
          end_date: customerOffer.end_date,
          amount: 30000,
          version: customerOffer.version,
          details: { months: 24, quantity: 1, annual_km: 30000 },
        },
      },
    )
  ).json()
  customerOffer = await (
    await page.request.post(
      `http://127.0.0.1:8088/api/supplier-workspace/records/${customerOffer.id}/status`,
      { headers: ownerHeaders, data: { version: customerOffer.version, status: 'Beklemede' } },
    )
  ).json()
  await customerPage.reload()
  article = customerPage
    .locator('.incoming-offers article')
    .filter({ hasText: 'Müşteri Revizyon Testi' })
  await article.getByRole('button', { name: 'Teklifi Kabul Et', exact: true }).click()
  await article.getByText(/Onaylandı/).waitFor()
  await article.getByRole('button', { name: 'Gönderilen Sürümleri Gör', exact: true }).click()
  await article.getByText(/Sürüm 2 · Beklemede/).waitFor()
  await customerPage.screenshot({ path: out + '/customer-offer-decision.png', fullPage: true })
  await customerContext.close()
  assert.equal(errors.length, 0, errors.join('\n'))
  assert.equal(failures.length, 0, failures.join('\n'))
  console.log(
    'PASS: return inspection→settlement→pool, real XLSX/PDF downloads, 23 workspace modules, three-party contract confirmation and two-party delivery confirmation, offer→contract→delivery→customer, invoice receipt, customers, CSV, shared fleet/details, mobile menu/overflow, viewer permissions, no runtime/server errors',
  )
} catch (error) {
  console.error({ runtimeErrors: errors, serverFailures: failures, currentUrl: page.url() })
  await page.screenshot({ path: `${out}/failure.png`, fullPage: true }).catch(() => {})
  throw error
} finally {
  await browser.close()
}
