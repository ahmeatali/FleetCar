import assert from 'node:assert/strict'
import { mkdirSync } from 'node:fs'
import {
  launchBrowser,
  readFixture,
  routeFixtureApi,
  webOrigin,
} from './helpers/browserFixture.mjs'
const browser = await launchBrowser(),
  fixture = readFixture(),
  out = '/tmp/team-management-previews',
  run = Date.now(),
  errors = [],
  failures = []
mkdirSync(out, { recursive: true })
try {
  const owner = await browser.newContext({ viewport: { width: 1600, height: 1050 } })
  await owner.addInitScript((f) => {
    localStorage.setItem('fleetcar_supplier_token', f.token)
    localStorage.setItem('fleetcar_supplier_id', '1')
    localStorage.setItem('fleetcar_supplier_type', 'ikame_arac')
    localStorage.setItem('fleetcar_token', f.customer_token)
    localStorage.setItem('fleetcar_customer_id', '1')
  }, fixture)
  const page = await owner.newPage()
  page.on('pageerror', (e) => errors.push(e.message))
  await routeFixtureApi(page, failures)
  for (const portal of ['supplier', 'customer']) {
    const root = portal === 'supplier' ? '/supplier-portal/users' : '/dashboard/users'
    await page.goto(webOrigin + root)
    await page.getByRole('heading', { name: 'Kullanıcı seçin' }).waitFor()
    await page.getByRole('button', { name: '＋ Yeni Kullanıcı', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByLabel('Ad Soyad', { exact: true }).fill('Ekip Test ' + portal)
    await dialog.getByLabel('E-posta', { exact: true }).fill(`${portal}.${run}@example.test`)
    await dialog.getByLabel('Departman', { exact: true }).fill('Operasyon')
    await dialog.getByRole('button', { name: 'Kullanıcıyı Ekle', exact: true }).click()
    await page.getByRole('heading', { name: 'Kullanıcı Daveti', exact: true }).waitFor()
    const url = await page.getByLabel('Davet Bağlantısı', { exact: true }).inputValue()
    assert.match(url, /#token=/)
    await page.getByRole('dialog').getByRole('button', { name: 'Kapat', exact: true }).click()
    const details = page.locator('.user-details')
    await details.getByRole('heading', { name: 'Ekip Test ' + portal, exact: true }).waitFor()
    if (portal === 'supplier') {
      await page.getByRole('button', { name: '＋ Yeni Rol', exact: true }).click()
      const roleDialog = page.getByRole('dialog')
      await roleDialog.getByLabel('Rol Adı', { exact: true }).fill('Operasyon Özel ' + run)
      await roleDialog.getByLabel('Temel Rol', { exact: true }).selectOption('fleet_manager')
      await roleDialog
        .getByRole('checkbox', { name: 'Yakıt & Giderler: Görüntüle', exact: true })
        .uncheck()
      assert.equal(
        await roleDialog
          .getByRole('checkbox', { name: 'Yakıt & Giderler: Ekle', exact: true })
          .isChecked(),
        false,
      )
      await roleDialog.getByRole('button', { name: 'Rolü Kaydet', exact: true }).click()
      await page.getByText('Rol şablonu kaydedildi.', { exact: true }).waitFor()
      await page.getByRole('button', { name: 'Kullanıcılar', exact: true }).click()
      await details
        .getByLabel('Rol', { exact: true })
        .selectOption({ label: 'Operasyon Özel ' + run })
      await details.getByRole('button', { name: 'Değişiklikleri Kaydet', exact: true }).click()
      await page
        .getByText('Kullanıcı ve izinleri kaydedildi. Kullanıcının açık oturumları kapatıldı.', {
          exact: true,
        })
        .waitFor()
      await page.evaluate(() => window.scrollTo(0, 0))
      await page.screenshot({
        path: out + '/supplier-team-desktop.png',
        fullPage: true,
        animations: 'disabled',
      })
    }
    await page.getByLabel('Kullanıcı ara', { exact: true }).fill('bulunmayan')
    await page.getByText('Aramanıza uygun kullanıcı bulunamadı.', { exact: true }).waitFor()
    await page.getByLabel('Kullanıcı ara', { exact: true }).fill('')
    await page.setViewportSize({ width: 390, height: 844 })
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
    await page.screenshot({
      path: out + '/' + portal + '-team-mobile.png',
      fullPage: true,
      animations: 'disabled',
    })
    await page.setViewportSize({ width: 1600, height: 1050 })
    const join = await browser.newContext(),
      joinPage = await join.newPage()
    joinPage.on('pageerror', (e) => errors.push(e.message))
    await routeFixtureApi(joinPage, failures)
    await joinPage.goto(webOrigin + '/accept-invitation' + new URL(url).hash)
    await joinPage.getByLabel('Şifre', { exact: true }).fill('TeamPassword10')
    await joinPage.getByLabel('Şifre Tekrar', { exact: true }).fill('WrongPassword10')
    await joinPage.getByRole('button', { name: 'Şifremi Oluştur ve Katıl' }).click()
    await joinPage.getByText('Şifreler eşleşmiyor.', { exact: true }).waitFor()
    await joinPage.getByLabel('Şifre Tekrar', { exact: true }).fill('TeamPassword10')
    await joinPage.getByRole('button', { name: 'Şifremi Oluştur ve Katıl' }).click()
    await joinPage.getByRole('link', { name: 'Giriş Yap', exact: true }).waitFor()
    assert.equal(new URL(joinPage.url()).hash, '')
    const login = await joinPage.request.post('http://127.0.0.1:8088/api/' + portal + '/login', {
      data: { email: `${portal}.${run}@example.test`, password: 'TeamPassword10' },
    })
    assert.equal(login.status(), 200, await login.text())
    const token = (await login.json()).token
    if (portal === 'supplier')
      assert.equal(
        (
          await joinPage.request.get('http://127.0.0.1:8088/api/supplier-workspace/expenses', {
            headers: { Authorization: 'Bearer ' + token },
          })
        ).status(),
        403,
      )
    await joinPage.evaluate(
      ({ portal, token }) =>
        localStorage.setItem(
          portal === 'supplier' ? 'fleetcar_supplier_token' : 'fleetcar_token',
          token,
        ),
      { portal, token },
    )
    await joinPage.goto(webOrigin + root)
    await joinPage
      .getByRole('alert')
      .filter({ hasText: 'Kullanıcı ve rol yönetimi şirket hesabı sahibine aittir.' })
      .waitFor()
    await join.close()
    await page.goto(webOrigin + root)
    await page.getByRole('button', { name: 'Aktivite', exact: true }).click()
    await page.getByRole('heading', { name: 'Ekip Yönetimi Aktivitesi', exact: true }).waitFor()
    assert.ok((await page.locator('.team-table tbody tr').count()) > 0)
  }
  await owner.close()
  assert.deepEqual(errors, [])
  assert.deepEqual(failures, [])
  console.log(
    'TEAM_BROWSER_OK supplier/customer: create, invite, accept, role matrix, backend denial, owner-only access, filters, activity, mobile',
  )
} finally {
  await browser.close()
}
