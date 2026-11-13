import { apiRequest } from './http.js'

// Which portal a page belongs to decides whose notices it shows; service accounts sign in
// through the supplier session.
export function portalFromPath(path = '') {
  if (path.startsWith('/service-portal')) return 'service'
  if (path.startsWith('/supplier-portal')) return 'supplier'
  return 'customer'
}

export const notificationsPath = {
  customer: '/dashboard/notifications',
  supplier: '/supplier-portal/notifications',
  service: '/service-portal/notifications',
}

export function notificationsApi(portal) {
  const account = portal === 'customer' ? 'customer' : 'supplier'
  return (path = '', options = {}) =>
    apiRequest('/api/notifications' + path, {
      account,
      errorMessage: 'Bildirimler yüklenemedi.',
      ...options,
    })
}

// "2 dk önce", "dün 14:05", "12.11.2026"
export function timeAgo(value, now = new Date()) {
  if (!value) return ''
  const then = new Date(value)
  if (Number.isNaN(then.getTime())) return ''
  const minutes = Math.round((now - then) / 60000)
  if (minutes < 1) return 'şimdi'
  if (minutes < 60) return `${minutes} dk önce`
  const hours = Math.round(minutes / 60)
  if (hours < 24 && then.getDate() === now.getDate()) return `${hours} sa önce`
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const clock = then.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
  if (then.toDateString() === yesterday.toDateString()) return `dün ${clock}`
  return then.toLocaleDateString('tr-TR')
}
