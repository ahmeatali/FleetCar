export function hasPreferredDates(details) {
  return Boolean(details?.preferred_date_start || details?.date1)
}

export function preferredDateRange(details) {
  const start = details?.preferred_date_start || details?.date1
  const end = details?.preferred_date_end || details?.date2
  const format = value => value ? new Date(`${value}T00:00:00`).toLocaleDateString('tr-TR') : '—'
  return start ? `${format(start)} – ${format(end || start)}` : '—'
}
