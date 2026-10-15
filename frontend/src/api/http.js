import { authorizedOptions } from './session.js'

export class ApiError extends Error {
  constructor(message, { status = 0, details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function isJsonBody(body) {
  return (
    body !== null &&
    typeof body === 'object' &&
    (Array.isArray(body) || Object.getPrototypeOf(body) === Object.prototype)
  )
}

// Raw responses remain available for existing pages and binary/file workflows.
export function fetchApi(path, options = {}) {
  const { account, errorMessage: _errorMessage, ...request } = options
  const headers = new Headers(request.headers)
  if (isJsonBody(request.body)) {
    request.body = JSON.stringify(request.body)
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  }
  return fetch(path, authorizedOptions(path, { ...request, headers }, { account }))
}

export async function ensureSuccess(
  response,
  fallback = 'İşlem tamamlanamadı. Lütfen tekrar deneyin.',
) {
  if (response.ok) return response
  const body = await response.json().catch(() => null)
  const detail = body?.detail
  const message =
    typeof detail === 'string'
      ? detail
      : typeof body?.message === 'string'
        ? body.message
        : fallback
  throw new ApiError(message, { status: response.status, details: detail ?? body })
}

export async function apiRequest(path, options = {}) {
  const response = await ensureSuccess(await fetchApi(path, options), options.errorMessage)
  if (response.status === 204) return null
  try {
    return await response.json()
  } catch {
    throw new ApiError('Sunucudan geçerli bir veri yanıtı alınamadı.', { status: response.status })
  }
}

export function createApiClient({ baseUrl = '', account, errorMessage } = {}) {
  return (path, options = {}) => apiRequest(baseUrl + path, { account, errorMessage, ...options })
}
