import { apiRequest } from '../api/http.js'
import { downloadApi } from './downloads.js'

export function signatureApi(path, options = {}, account = 'supplier') {
  const headers = new Headers(options.headers)
  if (options.body instanceof Blob && !headers.has('Content-Type'))
    headers.set('Content-Type', 'application/pdf')
  return apiRequest(path, {
    account,
    errorMessage: 'Belge işlemi tamamlanamadı.',
    ...options,
    headers,
  })
}

export function downloadSignedDocument(document, account = 'supplier') {
  return downloadApi(`/api/signed-documents/${document.document_id}`, {
    account,
    filename: document.original_name || 'imzali-belge.pdf',
    errorMessage: 'Belge indirilemedi.',
  })
}

export const signaturePartyLabels = Object.freeze({
  supplier: 'Kiralayan Firma',
  customer: 'Müşteri Firma',
  platform: 'FleetRent',
})
