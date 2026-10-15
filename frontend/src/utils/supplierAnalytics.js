// All summaries use the same source records. No seeded metrics or synthetic history.
export const num = (value) => (Number.isFinite(Number(value)) ? Number(value) : 0)
export const day = (value) => String(value || '').slice(0, 10)
export function inRange(value, start, end) {
  const stamp = day(value)
  return Boolean(stamp) && (!start || stamp >= start) && (!end || stamp <= end)
}
export function fleetStatus(v) {
  if (!v.is_active) return 'Pasif'
  if (['Servis', 'Serviste', 'Lastik Değişiminde'].includes(v.status)) return 'Serviste'
  if (['Hasar', 'Kaza'].includes(v.status)) return 'Hasar'
  if (v.vehicle_group === 'Satışta') return 'Satışta'
  if (v.rental_status === 'Teslim Bekliyor') return 'Havuzda'
  return v.customer_id ? 'Kirada' : 'Havuzda'
}
export function analyzeSupplier(data, filters = {}) {
  const cars = (data.vehicles || []).filter(
    (v) =>
      (!filters.customer || String(v.customer_id) === String(filters.customer)) &&
      (!filters.vehicle || v.id === filters.vehicle),
  )
  const ids = new Set(
    (data.vehicles || [])
      .filter((v) => !filters.vehicle || v.id === filters.vehicle)
      .map((v) => v.id),
  )
  const scoped = (r) =>
    (!filters.customer || String(r.customer_id) === String(filters.customer)) &&
    (!filters.vehicle || r.vehicle_id === filters.vehicle)
  const range = (r) => inRange(r.date, filters.start, filters.end)
  const records = (data.records || []).filter(scoped)
  const invoices = records.filter(
    (r) => r.kind === 'invoice' && !['Taslak', 'İptal'].includes(r.raw_status || r.status),
  )
  const revenue = invoices
    .filter((r) => r.details.direction === 'gelir' && range(r))
    .map((r) => ({ ...r, category: 'Gelir' }))
  const sourceInvoices = new Map(
    invoices
      .filter((r) => r.details.direction === 'gider' && r.details.source_reference)
      .map((r) => [r.details.source_reference, r]),
  )
  const sourceCategories = new Map()
  const costs = []
  const add = (r, category, key) => {
    sourceCategories.set(key, category)
    if (sourceInvoices.has(key)) return
    if (range(r) && num(r.amount) > 0)
      costs.push({ ...r, amount: num(r.amount), category, costKey: key })
  }
  for (const r of data.fuel || [])
    if (ids.has(r.vehicle_id) && scoped(r)) add(r, r.details.kind || 'Yakıt', r.id)
  for (const r of data.hgs || [])
    if (ids.has(r.vehicle_id) && scoped(r) && r.details.type === 'Geçiş') add(r, 'HGS', r.id)
  for (const r of data.service || [])
    if (
      ids.has(r.vehicle_id) &&
      scoped(r) &&
      ['Tamamlandı', 'Teslimata Hazır'].includes(r.status) &&
      r.details.invoice_amount != null
    )
      add({ ...r, date: r.details.invoice_date || r.date }, 'Servis', r.id)
  for (const r of records)
    if (
      ['policy', 'damage', 'fine'].includes(r.kind) &&
      !['Taslak', 'İptal', 'Reddedildi'].includes(r.raw_status || r.status)
    )
      add(r, { policy: 'Sigorta', damage: 'Hasar', fine: 'TPC' }[r.kind], `${r.kind}:${r.id}`)
  for (const r of invoices.filter((r) => r.details.direction === 'gider' && range(r))) {
    const category = sourceCategories.get(r.details.source_reference) || 'Gider Faturası'
    add(r, category, `invoice:${r.id}`)
  }
  const receipts = records.filter(
    (r) =>
      r.kind === 'payment' &&
      range(r) &&
      invoices.some((i) => i.id === r.parent_id && i.details.direction === 'gelir'),
  )
  const payments = records.filter(
    (r) =>
      r.kind === 'payment' &&
      range(r) &&
      invoices.some((i) => i.id === r.parent_id && i.details.direction === 'gider'),
  )
  const statusGroups = ['Kirada', 'Havuzda', 'Serviste', 'Satışta', 'Pasif', 'Hasar'].map(
    (label) => ({ label, count: cars.filter((v) => fleetStatus(v) === label).length }),
  )
  const today = new Date().toLocaleDateString('en-CA')
  const upcoming = []
  const days = (value) =>
    value
      ? Math.ceil((new Date(day(value) + 'T00:00:00') - new Date(today + 'T00:00:00')) / 86400000)
      : null
  for (const v of cars)
    for (const [field, label, module] of [
      ['contract_end_date', 'Sözleşme bitişi', 'contracts'],
      ['inspection_date', 'Muayene', 'vehicles'],
      ['casco_insurance_expiry_date', 'Kasko bitişi', 'policies'],
      ['traffic_insurance_expiry_date', 'Trafik sigortası', 'policies'],
      ['next_service_due_date', 'Bakım zamanı', 'service'],
    ]) {
      const delta = days(v[field])
      if (delta != null && delta >= 0 && delta <= 90)
        upcoming.push({
          key: `${v.id}-${field}`,
          title: label,
          plate: v.plate,
          date: v[field],
          days: delta,
          vehicle_id: v.id,
          module,
        })
    }
  const monthlyMap = {}
  for (const r of [...revenue.map((r) => ({ ...r, revenue: true })), ...costs]) {
    const key = day(r.date).slice(0, 7)
    if (!key) continue
    monthlyMap[key] ??= { key, revenue: 0, cost: 0 }
    monthlyMap[key][r.revenue ? 'revenue' : 'cost'] += num(r.amount)
  }
  const costCategories = Object.entries(
    costs.reduce((acc, r) => ((acc[r.category] = (acc[r.category] || 0) + r.amount), acc), {}),
  ).map(([label, amount]) => ({ label, amount }))
  const customerDistribution = Object.entries(
    cars
      .filter((v) => v.customer_id)
      .reduce(
        (acc, v) => (
          (acc[v.customer_name || 'Müşteri'] = (acc[v.customer_name || 'Müşteri'] || 0) + 1),
          acc
        ),
        {},
      ),
  )
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
  const models = Object.entries(
    cars.reduce((acc, v) => {
      const key = `${v.brand || ''} ${v.model || ''}`
      acc[key] = (acc[key] || 0) + 1
      return acc
    }, {}),
  )
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count)
  return {
    cars,
    records,
    invoices,
    revenue,
    costs,
    receipts,
    payments,
    statusGroups,
    upcoming: upcoming.sort((a, b) => a.days - b.days),
    monthly: Object.values(monthlyMap)
      .sort((a, b) => a.key.localeCompare(b.key))
      .slice(-12),
    costCategories,
    customerDistribution,
    models,
    totals: {
      revenue: revenue.reduce((s, r) => s + num(r.amount), 0),
      cost: costs.reduce((s, r) => s + num(r.amount), 0),
      receipts: receipts.reduce((s, r) => s + num(r.amount), 0),
      payments: payments.reduce((s, r) => s + num(r.amount), 0),
      balance: invoices
        .filter((i) => i.details.direction === 'gelir')
        .reduce((s, r) => s + num(r.balance), 0),
    },
  }
}
export function detectSupplierFindings(data, analysis) {
  const result = [],
    cfg = data.settings || {},
    add = (key, category, title, evidence, vehicle_id, amount = 0) =>
      result.push({ id: key, category, title, evidence, vehicle_id, amount })
  for (const v of analysis.cars) {
    if (
      v.current_month_km != null &&
      v.monthly_km_limit &&
      num(v.current_month_km) > num(v.monthly_km_limit)
    )
      add(
        `km-${v.id}`,
        'KM',
        'Aylık kilometre limiti aşıldı',
        `${v.plate}: ${v.current_month_km} / ${v.monthly_km_limit} km`,
        v.id,
      )
    if (
      v.customer_id &&
      v.current_month_km != null &&
      num(v.current_month_km) < num(cfg.low_usage_km ?? 500)
    )
      add(
        `usage-${v.id}`,
        'Kullanım',
        'Düşük aylık kullanım',
        `${v.plate}: ${v.current_month_km} km; aylık kira ${num(v.monthly_rent)} TL`,
        v.id,
        num(v.monthly_rent),
      )
    if (v.next_service_due_km != null && num(v.mileage) >= num(v.next_service_due_km))
      add(
        `service-${v.id}`,
        'Servis',
        'Bakım kilometresi geldi',
        `${v.plate}: ${v.mileage} / ${v.next_service_due_km} km`,
        v.id,
      )
    if (v.hgs_no && num(v.hgs_balance) < num(cfg.low_balance ?? 200))
      add(`hgs-${v.id}`, 'HGS', 'HGS bakiyesi düşük', `${v.plate}: ${num(v.hgs_balance)} TL`, v.id)
  }
  const seen = new Map()
  for (const r of analysis.costs.filter((r) => r.details?.receipt_no)) {
    const key = r.details.receipt_no
    if (seen.has(key))
      add(
        `duplicate-${r.id}`,
        'Fatura',
        'Tekrarlanan fiş numarası',
        `${key}: ${seen.get(key).plate} ve ${r.plate}`,
        r.vehicle_id,
        r.amount,
      )
    else seen.set(key, r)
  }
  for (const v of analysis.cars) {
    const fuels = (data.fuel || [])
      .filter((r) => r.vehicle_id === v.id && r.details.kind === 'Yakıt')
      .sort((a, b) => num(a.details.mileage) - num(b.details.mileage))
    if (fuels.length < 2) continue
    const first = fuels[0],
      last = fuels.at(-1),
      distance = num(last.details.mileage) - num(first.details.mileage)
    if (distance <= 0) continue
    const liters = fuels.slice(1).reduce((s, r) => s + num(r.details.liters), 0)
    const consumption = (liters / distance) * 100
    if (consumption > num(cfg.fuel_l100_threshold || 12))
      add(
        `fuel-${v.id}`,
        'Yakıt',
        'Yakıt tüketimini inceleyin',
        `${v.plate}: kayıtlar arası yaklaşık ${consumption.toFixed(1)} L/100 km (${distance} km). Dolum kapsamını doğrulayın.`,
        v.id,
      )
  }
  return result
}
