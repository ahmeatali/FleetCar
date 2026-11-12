// Support impersonation: an admin opens a company's own portal to help them.
// The minted portal token is stored under that portal's normal key so the portal
// works exactly as the company sees it; a flag records the active support session.
import { apiRequest } from './http.js'

const FLAG = 'fleetcar_impersonation'

// Portal pages read the company id/name from localStorage to scope their requests
// (e.g. /api/vehicles?customer_id=...), so impersonation must set them like a real login.
const IDENTITY_KEYS = {
  customer: {
    id: 'fleetcar_customer_id',
    name: 'fleetcar_customer_name',
    role: 'fleetcar_user_role',
  },
  supplier: { id: 'fleetcar_supplier_id', name: 'fleetcar_supplier_name' },
}

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
  const idKeys = IDENTITY_KEYS[data.portal]
  const setKeys = [data.storage_key]
  if (idKeys) {
    storage.setItem(idKeys.id, String(data.subject_id))
    storage.setItem(idKeys.name, data.subject_name || '')
    setKeys.push(idKeys.id, idKeys.name)
    if (idKeys.role) {
      // the support session is the company's owner session
      storage.setItem(idKeys.role, 'owner')
      setKeys.push(idKeys.role)
    }
  }
  storage.setItem(
    FLAG,
    JSON.stringify({
      portal: data.portal,
      subjectName: data.subject_name,
      eventId: data.event_id,
      storageKey: data.storage_key,
      openPath: data.open_path,
      keys: setKeys,
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
  for (const key of flag.keys || [flag.storageKey]) storage.removeItem(key)
  storage.removeItem(FLAG)
  notify()
}
