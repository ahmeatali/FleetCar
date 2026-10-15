import test from 'node:test'
import assert from 'node:assert/strict'
import { detectCustomerFindings } from '../src/utils/customerFindings.js'

const vehicle = {
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
test('customer findings use only the selected active vehicles and their expenses', () => {
  const expenses = [
    {
      id: 1,
      vehicle_id: vehicle.id,
      kind: 'Yakıt',
      mileage: 1000,
      liters: 40,
      receipt_no: 'A',
      amount: 1000,
    },
    {
      id: 2,
      vehicle_id: vehicle.id,
      kind: 'Yakıt',
      mileage: 1100,
      liters: 40,
      receipt_no: 'A',
      amount: 1000,
    },
    {
      id: 3,
      vehicle_id: 'another-car',
      kind: 'Yakıt',
      mileage: 1200,
      liters: 999,
      receipt_no: 'A',
      amount: 99999,
    },
  ]
  const findings = detectCustomerFindings([vehicle], expenses)
  assert.deepEqual(
    new Set(findings.map((finding) => finding.category)),
    new Set(['KM', 'Kullanım', 'HGS', 'Fatura', 'Yakıt']),
  )
  assert.ok(findings.every((finding) => finding.vehicle_id === vehicle.id))
  assert.equal(findings.find((finding) => finding.category === 'Fatura').amount, 1000)
  assert.match(findings.find((finding) => finding.category === 'Yakıt').evidence, /40.0 L\/100 km/)
  assert.deepEqual(detectCustomerFindings([], expenses), [])
  assert.deepEqual(detectCustomerFindings([{ ...vehicle, is_active: false }], []), [])
})
test('customer thresholds can change findings without modifying source data', () => {
  const before = structuredClone(vehicle)
  const findings = detectCustomerFindings([vehicle], [], { low_usage_km: 50, low_balance: 10 })
  assert.deepEqual(
    findings.map((finding) => finding.category),
    ['KM'],
  )
  assert.deepEqual(vehicle, before)
  assert.deepEqual(detectCustomerFindings([{ id: 'no-data', is_active: true }], []), [])
})
