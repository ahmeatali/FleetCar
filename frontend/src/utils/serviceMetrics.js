// Only completed requests with a recorded check-in and completion time contribute.
export function serviceMetrics(requests = []) {
  const groups = { damage: [], maintenance: [], total: [] }
  for (const request of requests) {
    if (request.type !== 'servis' || request.status !== 'Tamamlandı') continue
    const start = request.details?.entry_date,
      end = request.completed_at
    if (!start || !end) continue
    const elapsed = new Date(end).getTime() - new Date(start).getTime()
    if (!Number.isFinite(elapsed) || elapsed < 0) continue
    const days = elapsed / 86400000
    groups.total.push(days)
    const category = String(request.details?.service_type || '').toLocaleLowerCase('tr-TR')
    if (/hasar|onarım|kaza/.test(category)) groups.damage.push(days)
    else if (/bakım|periyodik/.test(category)) groups.maintenance.push(days)
  }
  return Object.fromEntries(
    Object.entries(groups).map(([key, days]) => [
      key,
      {
        count: days.length,
        days: days.length ? days.reduce((sum, day) => sum + day, 0) / days.length : null,
      },
    ]),
  )
}
