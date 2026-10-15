import test, { before, after } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp, h } from 'vue'
import { renderToString } from '@vue/server-renderer'

let server, ui, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'fleetrent-ui-ssr-'))
  server = await createServer({
    root: fileURLToPath(new URL('../', import.meta.url)),
    configFile: false,
    cacheDir,
    optimizeDeps: { noDiscovery: true, include: [] },
    plugins: [vue()],
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  })
  ui = await server.ssrLoadModule('/src/components/ui/index.js')
})
after(async () => {
  await server?.close()
  if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
})
const render = (component, props, slots) =>
  renderToString(createSSRApp({ render: () => h(component, props, slots) }))

test('shared buttons preserve native submit/reset types and forward accessible attributes', async () => {
  const html = await render(
    ui.UiButton,
    { type: 'submit', class: 'feature-button', 'aria-label': 'Kaydet' },
    () => 'Kaydet',
  )
  assert.match(html, /<button/)
  assert.match(html, /type="submit"/)
  assert.match(html, /class="feature-button"/)
  assert.match(html, /aria-label="Kaydet"/)
  const native = await render(ui.UiButton, {}, () => 'Default submit')
  assert.doesNotMatch(native, /type="button"/)
  const reset = await render(ui.UiButton, { type: 'reset' }, () => 'Reset')
  assert.match(reset, /type="reset"/)
})
test('loading buttons block interaction and expose their busy state', async () => {
  const html = await render(ui.UiButton, { loading: true }, () => 'Saving')
  assert.match(html, /disabled/)
  assert.match(html, /aria-busy="true"/)
  assert.match(html, /ui-button__spinner/)
})
test('form fields connect hints and validation errors to their controls', async () => {
  const html = await render(
    ui.UiField,
    { inputId: 'plate', label: 'Plaka', error: 'Plaka gerekli.' },
    {
      default: ({ id, invalid, describedBy }) =>
        h('input', { id, 'aria-invalid': invalid, 'aria-describedby': describedBy }),
    },
  )
  assert.match(html, /for="plate"/)
  assert.match(html, /id="plate"/)
  assert.match(html, /aria-describedby="plate-description"/)
  assert.match(html, /id="plate-description"/)
  assert.match(html, /role="alert"/)
})
test('alerts and table wrappers retain native semantics', async () => {
  assert.match(await render(ui.UiAlert, { tone: 'error' }, () => 'Failed'), /role="alert"/)
  assert.match(await render(ui.UiAlert, { tone: 'success' }, () => 'Saved'), /role="status"/)
  const html = await render(ui.UiTable, { label: 'Araçlar' }, () =>
    h('table', {}, h('tbody', {}, h('tr', {}, h('td', '34 ABC')))),
  )
  assert.match(html, /role="region"/)
  assert.match(html, /<table/)
  assert.match(html, /34 ABC/)
})
