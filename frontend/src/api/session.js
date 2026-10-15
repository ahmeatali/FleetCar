const TOKEN_KEYS = Object.freeze({
  admin: 'fleetcar_admin_token',
  supplier: 'fleetcar_supplier_token',
  customer: 'fleetcar_token',
})

export function portalAccount(apiPath, pagePath = '') {
  if (apiPath.startsWith('/api/admin/') || pagePath.startsWith('/admin')) return 'admin'
  if (
    apiPath.startsWith('/api/supplier-workspace') ||
    pagePath.startsWith('/supplier-portal') ||
    pagePath.startsWith('/service-portal')
  )
    return 'supplier'
  return 'customer'
}

export function authorizedOptions(input, options = {}, environment = {}) {
  const origin = environment.origin || globalThis.location?.origin || 'http://localhost'
  const pagePath = environment.pagePath ?? globalThis.location?.pathname ?? ''
  const storage = environment.storage || globalThis.localStorage
  const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url, origin)
  const headers = new Headers(input instanceof Request ? input.headers : undefined)
  new Headers(options.headers).forEach((value, key) => headers.set(key, value))
  if (url.origin === origin && url.pathname.startsWith('/api/') && !headers.has('Authorization')) {
    const account = environment.account || portalAccount(url.pathname, pagePath)
    const key = TOKEN_KEYS[account]
    if (!key) throw new TypeError(`Unknown portal account: ${account}`)
    const token = storage?.getItem(key)
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }
  return { ...options, headers }
}
