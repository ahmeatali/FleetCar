// Support impersonation: an admin opens a company's own portal to help them.
// The minted portal token is stored under that portal's normal key so the portal
// works exactly as the company sees it; a flag records the active support session.
import { apiRequest } from './http.js'

const FLAG = 'fleetcar_impersonation'

function notify() {
  globalThis.dispatchEvent?.(new CustomEvent('impersonation-change'))
}

export function activeImpersonation(storage = localStorage) {
  try {
    return JSON.parse(storage.getItem(FLAG) || 'null')
  } catch {
    return null
  }
}

export async function startImpersonation(portal, subjectId, userId = null, storage = localStorage) {
  const data = await apiRequest('/api/admin/impersonate', {
    account: 'admin',
    method: 'POST',
    body: { portal, subject_id: subjectId, user_id: userId },
  })
  storage.setItem(data.storage_key, data.token)
  storage.setItem(
    FLAG,
    JSON.stringify({
      portal: data.portal,
      subjectName: data.subject_name,
      eventId: data.event_id,
      storageKey: data.storage_key,
      openPath: data.open_path,
    }),
  )
  notify()
  return data.open_path
}

export async function stopImpersonation(storage = localStorage) {
  const flag = activeImpersonation(storage)
  if (!flag) return
  try {
    await apiRequest('/api/admin/impersonate/stop', {
      account: 'admin',
      method: 'POST',
      body: { event_id: flag.eventId },
    })
  } catch {
    // The portal session may already be gone; clearing locally is enough.
  }
  storage.removeItem(flag.storageKey)
  storage.removeItem(FLAG)
  notify()
}
