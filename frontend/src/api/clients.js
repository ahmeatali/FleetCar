import { createApiClient } from './http.js'

export const supplierClient = createApiClient({
  baseUrl: '/api/supplier-workspace',
  account: 'supplier',
  errorMessage: 'Alanları kontrol edip tekrar deneyin.',
})
export const customerClient = createApiClient({
  baseUrl: '/api/customer-workspace',
  account: 'customer',
})
export const portalClient = createApiClient()
