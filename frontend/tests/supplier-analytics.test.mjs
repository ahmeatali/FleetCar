import test from 'node:test'
import assert from 'node:assert/strict'
import {
  analyzeSupplier,
  detectSupplierFindings,
  fleetStatus,
} from '../src/utils/supplierAnalytics.js'
const vehicle = {
  id: 'car',
  is_active: true,
  status: 'Aktif',
  customer_id: 1,
  customer_name: 'Customer A',
  mileage: 10000,
}
const invoice = (id, amount, direction, extras = {}) => ({
  id,
  kind: 'invoice',
  source: 'operation',
  number: `F-${id}`,
  vehicle_id: 'car',
  customer_id: 1,
  date: '2026-10-14',
  amount,
  balance: amount,
  status: 'Kesildi',
  raw_status: 'Kesildi',
  details: { direction, ...extras },
})
const fuel = {
  id: 'fuel:1',
  vehicle_id: 'car',
  customer_id: 1,
  date: '2026-09-01',
  amount: 2000,
  details: { kind: 'Yakıt', liters: 40, mileage: 10000, receipt_no: 'R1' },
}
test('empty fleet has no invented figures or history', () => {
  const a = analyzeSupplier({})
  assert.deepEqual(a.totals, { revenue: 0, cost: 0, receipts: 0, payments: 0, balance: 0 })
  assert.equal(a.monthly.length, 0)
  assert.equal(detectSupplierFindings({}, a).length, 0)
})
test('HGS reload and invoice receipt do not inflate cost or revenue', () => {
  const data = {
    vehicles: [vehicle],
    records: [
      invoice(1, 30000, 'gelir'),
      {
        id: 2,
        kind: 'payment',
        parent_id: 1,
        vehicle_id: 'car',
        customer_id: 1,
        date: '2026-10-14',
        amount: 10000,
        details: {},
      },
    ],
    hgs: [
      {
        id: 'hgs:1',
        vehicle_id: 'car',
        customer_id: 1,
        date: '2026-10-14',
        amount: 500,
        details: { type: 'Yükleme' },
      },
      {
        id: 'hgs:2',
        vehicle_id: 'car',
        customer_id: 1,
        date: '2026-10-14',
        amount: 125,
        details: { type: 'Geçiş' },
      },
    ],
  }
  const a = analyzeSupplier(data)
  assert.equal(a.totals.revenue, 30000)
  assert.equal(a.totals.receipts, 10000)
  assert.equal(a.totals.cost, 125)
})
test('linked expense invoice replaces its source without counting either month twice', () => {
  const data = {
    vehicles: [vehicle],
    fuel: [fuel],
    records: [invoice(2, 2200, 'gider', { source_reference: 'fuel:1' })],
  }
  assert.equal(analyzeSupplier(data).totals.cost, 2200)
  assert.equal(analyzeSupplier(data, { start: '2026-09-01', end: '2026-09-30' }).totals.cost, 0)
  assert.equal(analyzeSupplier(data, { start: '2026-10-01', end: '2026-10-31' }).totals.cost, 2200)
})
test('draft/cancelled invoices never become realized revenue', () => {
  const data = {
    vehicles: [vehicle],
    records: [
      { ...invoice(1, 30000, 'gelir'), status: 'Taslak', raw_status: 'Taslak' },
      { ...invoice(2, 30000, 'gelir'), status: 'İptal', raw_status: 'İptal' },
    ],
  }
  assert.equal(analyzeSupplier(data).totals.revenue, 0)
})
test('customer and vehicle filters apply to ledger as well as current stock', () => {
  const data = {
    vehicles: [vehicle, { ...vehicle, id: 'other', customer_id: 2 }],
    records: [
      invoice(1, 30000, 'gelir'),
      { ...invoice(2, 40000, 'gelir'), vehicle_id: 'other', customer_id: 2 },
    ],
  }
  assert.equal(analyzeSupplier(data, { customer: '1' }).totals.revenue, 30000)
  assert.equal(analyzeSupplier(data, { vehicle: 'other' }).totals.revenue, 40000)
})
test('operational status takes precedence over customer assignment', () => {
  assert.equal(fleetStatus({ ...vehicle, status: 'Serviste' }), 'Serviste')
  assert.equal(fleetStatus({ ...vehicle, customer_id: null }), 'Havuzda')
  assert.equal(fleetStatus({ ...vehicle, is_active: false }), 'Pasif')
})
test('findings require evidence; absent mileage is not treated as low usage', () => {
  const data = { vehicles: [vehicle], settings: { low_usage_km: 500 } }
  assert.equal(detectSupplierFindings(data, analyzeSupplier(data)).length, 0)
  data.vehicles[0] = { ...vehicle, current_month_km: 250, monthly_rent: 30000 }
  const findings = detectSupplierFindings(data, analyzeSupplier(data))
  assert.equal(findings.length, 1)
  assert.equal(findings[0].category, 'Kullanım')
  assert.equal(findings[0].amount, 30000)
})

test('historical costs remain filterable after the vehicle returns to pool', () => {
  const data = { vehicles: [{ ...vehicle, customer_id: null }], fuel: [fuel] }
  assert.equal(analyzeSupplier(data, { customer: '1' }).totals.cost, 2000)
  assert.equal(analyzeSupplier(data, { customer: '1' }).cars.length, 0)
})
