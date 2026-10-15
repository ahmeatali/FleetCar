import test, { afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { authorizedOptions, portalAccount } from '../src/api/session.js'
import { ApiError, apiRequest, fetchApi } from '../src/api/http.js'

const originalFetch = globalThis.fetch
afterEach(() => {
  globalThis.fetch = originalFetch
})
const storage = {
  getItem: (key) =>
    ({
      fleetcar_admin_token: 'admin-fixture',
      fleetcar_supplier_token: 'supplier-fixture',
      fleetcar_token: 'customer-fixture',
    })[key],
}
const environment = { origin: 'https://fleet.test', pagePath: '/supplier-portal', storage }

test('portal account resolution preserves the customer, supplier and admin boundaries', () => {
  assert.equal(portalAccount('/api/vehicles', '/supplier-portal'), 'supplier')
  assert.equal(portalAccount('/api/admin/customers', '/dashboard'), 'admin')
  assert.equal(portalAccount('/api/vehicles', '/dashboard'), 'customer')
  assert.equal(portalAccount('/api/requests', '/service-portal'), 'supplier')
  assert.equal(
    authorizedOptions('/api/vehicles', {}, environment).headers.get('Authorization'),
    'Bearer supplier-fixture',
  )
})
test('tokens never attach to external URLs or non-API resources', () => {
  for (const path of [
    'https://outside.test/api/vehicles',
    '//outside.test/api/vehicles',
    '/uploads/file.pdf',
  ]) {
    assert.equal(authorizedOptions(path, {}, environment).headers.has('Authorization'), false)
  }
})
test('explicit account and caller headers are preserved without mutating options', () => {
  const options = { headers: { 'X-Request-ID': '123' } }
  assert.equal(
    authorizedOptions('/api/signatures', options, {
      ...environment,
      account: 'customer',
    }).headers.get('Authorization'),
    'Bearer customer-fixture',
  )
  assert.deepEqual(options, { headers: { 'X-Request-ID': '123' } })
  const request = new Request('https://fleet.test/api/vehicles', {
    headers: { Authorization: 'Bearer explicit', 'X-Base': 'value' },
  })
  const result = authorizedOptions(request, { headers: { 'X-Request-ID': '123' } }, environment)
  assert.equal(result.headers.get('Authorization'), 'Bearer explicit')
  assert.equal(result.headers.get('X-Base'), 'value')
})
test('JSON objects are encoded once and supplied strings remain unchanged', async () => {
  const seen = []
  globalThis.fetch = async (path, options) => {
    seen.push(options)
    return Response.json({ ok: true })
  }
  await apiRequest('/api/demo', { method: 'POST', body: { amount: 100 } })
  await apiRequest('/api/demo', {
    method: 'POST',
    body: '{"amount":100}',
    headers: { 'Content-Type': 'application/json' },
  })
  assert.equal(seen[0].body, '{"amount":100}')
  assert.equal(seen[1].body, seen[0].body)
  assert.equal(seen[0].headers.get('Content-Type'), 'application/json')
})
test('PDF, FormData, abort signals and raw responses keep their native contracts', async () => {
  const blob = new Blob(['pdf'], { type: 'application/pdf' }),
    form = new FormData(),
    signal = new AbortController().signal
  const seen = []
  globalThis.fetch = async (path, options) => {
    seen.push(options)
    return Response.json({ ok: true })
  }
  const response = await fetchApi('/api/upload', { method: 'POST', body: blob, signal })
  await fetchApi('/api/upload', { method: 'POST', body: form })
  assert.equal(seen[0].body, blob)
  assert.equal(seen[0].signal, signal)
  assert.equal(seen[1].body, form)
  assert.equal(seen[1].headers.has('Content-Type'), false)
  assert.equal(response.status, 200)
})
test('HTTP errors expose status and details without displaying server HTML', async () => {
  globalThis.fetch = async () =>
    Response.json({ detail: 'Güncel sürümü kullanın.' }, { status: 409 })
  await assert.rejects(
    () => apiRequest('/api/demo'),
    (e) => e instanceof ApiError && e.status === 409 && e.message === 'Güncel sürümü kullanın.',
  )
  globalThis.fetch = async () => new Response('<html>private server error</html>', { status: 500 })
  await assert.rejects(
    () => apiRequest('/api/demo', { errorMessage: 'Kaydedilemedi.' }),
    (e) => e.status === 500 && e.message === 'Kaydedilemedi.',
  )
})
test('empty and malformed successful responses are handled explicitly; mutations are not retried', async () => {
  globalThis.fetch = async () => new Response(null, { status: 204 })
  assert.equal(await apiRequest('/api/demo'), null)
  globalThis.fetch = async () => new Response('invalid')
  await assert.rejects(() => apiRequest('/api/demo'), ApiError)
  let calls = 0
  globalThis.fetch = async () => {
    calls++
    throw new TypeError('offline')
  }
  await assert.rejects(
    () => apiRequest('/api/demo', { method: 'POST', body: { value: 1 } }),
    TypeError,
  )
  assert.equal(calls, 1)
})
