import test from 'node:test'
import assert from 'node:assert/strict'
import { serviceMetrics } from '../src/utils/serviceMetrics.js'

test('service metrics have no synthetic defaults', () => {
  for (const value of Object.values(serviceMetrics()))
    assert.deepEqual(value, { count: 0, days: null })
})
test('service duration uses recorded check-in and completion, with explicit categories', () => {
  const row = (service_type, end) => ({
    type: 'servis',
    status: 'Tamamlandı',
    details: { entry_date: '2026-10-01T09:00:00', service_type },
    completed_at: end,
  })
  const result = serviceMetrics([
    row('Hasar Onarım', '2026-10-03T09:00:00'),
    row('Periyodik Bakım', '2026-10-01T21:00:00'),
    row('', '2026-10-02T09:00:00'),
  ])
  assert.deepEqual(result.damage, { count: 1, days: 2 })
  assert.deepEqual(result.maintenance, { count: 1, days: 0.5 })
  assert.equal(result.total.count, 3)
  assert.equal(result.total.days, 3.5 / 3)
})
test('unfinished, missing, invalid and reversed times are excluded', () => {
  const base = {
    type: 'servis',
    status: 'Tamamlandı',
    details: { entry_date: '2026-10-01' },
    completed_at: '2026-10-02',
  }
  const rows = [
    { ...base, status: 'Serviste' },
    { ...base, type: 'lastik' },
    { ...base, completed_at: null },
    { ...base, completed_at: 'invalid' },
    { ...base, completed_at: '2026-09-30' },
    { ...base, details: {} },
  ]
  assert.equal(serviceMetrics(rows).total.count, 0)
})
