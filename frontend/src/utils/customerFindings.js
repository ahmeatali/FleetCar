import { detectSupplierFindings } from './supplierAnalytics.js'

// Inputs come from the customer-authenticated APIs, including event-period visibility.
export function detectCustomerFindings(vehicles, expenses, settings = {}) {
  const active = vehicles.filter((vehicle) => vehicle.is_active)
  const ids = new Set(active.map((vehicle) => vehicle.id))
  const fuel = expenses
    .filter((record) => ids.has(record.vehicle_id))
    .map((record) => ({
      ...record,
      plate: vehicles.find((vehicle) => vehicle.id === record.vehicle_id)?.plate,
      details: record,
    }))
  return detectSupplierFindings({ settings, fuel }, { cars: active, costs: fuel })
}
