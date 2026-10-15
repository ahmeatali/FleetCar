const LOCALE = 'tr-TR'

export function formatNumber(value, { empty = '—', ...options } = {}) {
  if (value == null || value === '' || !Number.isFinite(Number(value))) return empty
  return Number(value).toLocaleString(LOCALE, options)
}

export function formatMoney(value, { empty = '—', currency = 'TRY', ...options } = {}) {
  return formatNumber(value, {
    empty,
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
    ...options,
  })
}

export function formatDate(value, { empty = '—', ...options } = {}) {
  if (!value) return empty
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? empty : parsed.toLocaleDateString(LOCALE, options)
}

export function formatDateTime(value, { empty = '—', ...options } = {}) {
  if (!value) return empty
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime())
    ? empty
    : parsed.toLocaleString(LOCALE, { dateStyle: 'short', timeStyle: 'short', ...options })
}

export function formatBytes(bytes) {
  if (!Number.isFinite(Number(bytes)) || Number(bytes) <= 0) return '0 B'
  return bytes < 1048576 ? Math.ceil(bytes / 1024) + ' KB' : (bytes / 1048576).toFixed(1) + ' MB'
}
