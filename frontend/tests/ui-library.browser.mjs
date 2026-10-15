import assert from 'node:assert/strict'
import {
  launchBrowser,
  readFixture,
  routeFixtureApi,
  webOrigin,
  closeFixtureContext,
} from './helpers/browserFixture.mjs'

const fixture = readFixture(),
  browser = await launchBrowser(),
  errors = [],
  failures = []
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  const page = await context.newPage()
  page.on('pageerror', (error) => errors.push(error.message))
  await routeFixtureApi(page, failures)
  await page.goto(webOrigin + '/supplier-login')
  await page.getByLabel('Tedarikçi E-posta Adresi', { exact: true }).fill('owner@example.test')
  await page.getByLabel('Şifre', { exact: true }).fill('InvalidPassword10')
  await page.getByRole('button', { name: /Tedarikçi Portalına Giriş/ }).click()
  await page.getByRole('alert').waitFor()
  assert.equal(await page.evaluate(() => localStorage.getItem('fleetcar_supplier_token')), null)
  await page.getByLabel('Şifre', { exact: true }).fill('OwnerPassword10')
  await page.getByRole('button', { name: /Tedarikçi Portalına Giriş/ }).click()
  await page.waitForURL('**/supplier-portal')
  await page.goto(webOrigin + '/supplier-portal/offers')
  const create = page.getByRole('button', { name: '＋ Yeni Teklif', exact: true })
  await create.waitFor()
  const overflow = await page.evaluate(() => document.body.style.overflow)
  await create.click()
  const dialog = page.getByRole('dialog')
  await dialog.waitFor()
  assert.equal(await page.evaluate(() => document.body.style.overflow), 'hidden')
  assert.equal(await dialog.evaluate((node) => node.contains(document.activeElement)), true)
  await dialog.evaluate((node) => {
    const buttons = [...node.querySelectorAll('button,input,select,textarea')].filter(
      (el) => !el.disabled && el.getClientRects().length,
    )
    buttons.at(-1).focus()
  })
  await page.keyboard.press('Tab')
  assert.equal(
    await dialog.evaluate((node) => document.activeElement === node.querySelector('button')),
    true,
  )
  await page.keyboard.press('Escape')
  await dialog.waitFor({ state: 'hidden' })
  assert.equal(await create.evaluate((node) => node === document.activeElement), true)
  assert.equal(await page.evaluate(() => document.body.style.overflow), overflow)

  // Isolated component harness in the browser; no production route or fixture data is added.
  await page.evaluate(async () => {
    const compiled = await (await fetch('/src/components/ui/UiModal.vue')).text()
    const vuePath = compiled.match(/from\s*["']([^"']*\/vue[^"']*)["']/)?.[1]
    if (!vuePath) throw Error('Vue runtime path was not found in the development module.')
    const { createApp, h, ref } = await import(vuePath)
    const { UiButton, UiModal } = await import('/src/components/ui/index.js')
    const host = document.createElement('div')
    Object.assign(host.style, {
      position: 'fixed',
      right: '20px',
      top: '80px',
      zIndex: '20000',
      background: 'white',
      padding: '16px',
    })
    document.body.append(host)
    const app = createApp({
      setup() {
        const outer = ref(false),
          inner = ref(false),
          busy = ref(false)
        return () =>
          h('div', [
            h(
              UiButton,
              {
                type: 'button',
                onClick: () => {
                  outer.value = true
                },
              },
              () => 'Open outer',
            ),
            outer.value
              ? h(
                  UiModal,
                  {
                    'data-testid': 'outer-modal',
                    style: { position: 'fixed', inset: '0', background: 'white', zIndex: 10000 },
                    onClose: () => {
                      outer.value = false
                    },
                  },
                  () =>
                    h('section', [
                      h('h2', 'Outer dialog'),
                      h(
                        UiButton,
                        {
                          type: 'button',
                          onClick: () => {
                            inner.value = true
                          },
                        },
                        () => 'Open inner',
                      ),
                      inner.value
                        ? h(
                            UiModal,
                            {
                              'data-testid': 'inner-modal',
                              busy: busy.value,
                              style: {
                                position: 'fixed',
                                inset: '0',
                                background: 'white',
                                zIndex: 10001,
                              },
                              onClose: () => {
                                inner.value = false
                              },
                            },
                            () =>
                              h('section', [
                                h('h2', 'Inner dialog'),
                                h(
                                  UiButton,
                                  {
                                    type: 'button',
                                    onClick: () => {
                                      busy.value = !busy.value
                                    },
                                  },
                                  () => 'Toggle busy',
                                ),
                              ]),
                          )
                        : null,
                    ]),
                )
              : null,
          ])
      },
    })
    app.mount(host)
    window.__fleetUiCleanup = () => {
      app.unmount()
      host.remove()
    }
  })
  const outer = page.getByTestId('outer-modal'),
    inner = page.getByTestId('inner-modal')
  await page.getByRole('button', { name: 'Open outer', exact: true }).click()
  await page.getByRole('button', { name: 'Open inner', exact: true }).click()
  await page.getByRole('button', { name: 'Toggle busy', exact: true }).click()
  await page.keyboard.press('Escape')
  assert.equal(await inner.isVisible(), true)
  await page.getByRole('button', { name: 'Toggle busy', exact: true }).click()
  await page.keyboard.press('Escape')
  await inner.waitFor({ state: 'hidden' })
  assert.equal(await outer.isVisible(), true)
  assert.equal(await page.evaluate(() => document.body.style.overflow), 'hidden')
  assert.equal(
    await page
      .getByRole('button', { name: 'Open inner', exact: true })
      .evaluate((node) => node === document.activeElement),
    true,
  )
  await page.keyboard.press('Escape')
  await outer.waitFor({ state: 'hidden' })
  assert.equal(await page.evaluate(() => document.body.style.overflow), overflow)
  await page.evaluate(() => window.__fleetUiCleanup())

  const service = await browser.newContext(),
    servicePage = await service.newPage()
  servicePage.on('pageerror', (error) => errors.push(error.message))
  await routeFixtureApi(servicePage, failures)
  await servicePage.goto(webOrigin + '/service-login')
  await servicePage.getByRole('button', { name: 'Şifremi Unuttum?', exact: true }).click()
  await servicePage.getByLabel('E-posta Adresi', { exact: true }).waitFor()
  await servicePage.getByRole('button', { name: '← Girişe Dön', exact: true }).click()
  await servicePage
    .getByLabel('Servis E-posta Adresi', { exact: true })
    .fill('service-browser@example.test')
  await servicePage.getByLabel('Şifre', { exact: true }).fill('ServicePassword10')
  await servicePage.getByRole('button', { name: /Servis Portalına Giriş/ }).click()
  await servicePage.waitForURL('**/service-portal')
  assert.equal(await servicePage.evaluate(() => localStorage.getItem('fleetcar_supplier_id')), '3')
  assert.equal(
    await servicePage.evaluate(() => localStorage.getItem('fleetcar_supplier_role')),
    'owner',
  )
  await closeFixtureContext(service)

  const customer = await browser.newContext(),
    customerPage = await customer.newPage()
  await customer.addInitScript((token) => {
    localStorage.setItem('fleetcar_token', token)
    localStorage.setItem('fleetcar_customer_id', '1')
  }, fixture.customer_token)
  customerPage.on('pageerror', (error) => errors.push(error.message))
  await routeFixtureApi(customerPage, failures)
  await customerPage.goto(webOrigin + '/dashboard/quotes')
  const bell = customerPage.getByRole('button', { name: 'Bildirimler', exact: true })
  await bell.click()
  await customerPage.locator('.notification-panel').waitFor()
  await customerPage.keyboard.press('Escape')
  await customerPage.locator('.notification-panel').waitFor({ state: 'hidden' })
  assert.equal(await bell.evaluate((node) => node === document.activeElement), true)
  await closeFixtureContext(customer)
  assert.deepEqual(errors, [])
  assert.deepEqual(failures, [])
  console.log(
    'PASS: supplier/service login, failed authentication, shared form labels, dialog Tab/Escape/focus restoration, nested busy dialogs and scroll locks, notification button DOM bridge',
  )
} finally {
  await browser.close()
}
