import test from 'node:test'
import assert from 'node:assert/strict'
import { savePartnerSession } from '../src/api/partnerSession.js'

test('incomplete login responses never invent an account id or overwrite the current session', () => {
  const values = new Map([['fleetcar_supplier_token', 'existing']]),
    storage = { setItem: (key, value) => values.set(key, value) }
  assert.throws(() =>
    savePartnerSession({ token: 'new', supplier: {} }, 'user@example.test', storage),
  )
  assert.throws(() => savePartnerSession({ supplier: { id: 1 } }, 'user@example.test', storage))
  assert.equal(values.get('fleetcar_supplier_token'), 'existing')
  assert.equal(values.size, 1)
})
test('a new partner login replaces stale member metadata with server-confirmed identity', () => {
  const values = new Map([['fleetcar_supplier_role', 'operations']]),
    storage = { setItem: (key, value) => values.set(key, value) }
  savePartnerSession(
    {
      token: 'fixture',
      supplier: { id: 9, name: 'Service', type: 'servis', is_email_verified: true },
    },
    'service@example.test',
    storage,
  )
  assert.equal(values.get('fleetcar_supplier_id'), '9')
  assert.equal(values.get('fleetcar_supplier_role'), 'owner')
  assert.equal(values.get('fleetcar_supplier_user_name'), 'Service')
  assert.equal(values.get('fleetcar_user_email'), 'service@example.test')
})
