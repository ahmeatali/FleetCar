// Compatibility exports keep existing callers stable while transport lives in api/.
import { fetchApi } from '../api/http.js'
export { supplierClient as supplierApi } from '../api/clients.js'
export { downloadCsv as downloadSupplierCsv } from './downloads.js'

export function supplierFetch(path, options = {}) {
  return fetchApi(`/api/supplier-workspace${path}`, { account: 'supplier', ...options })
}
