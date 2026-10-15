import { ensureSuccess, fetchApi } from '../api/http.js'

export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  // Keep the URL alive long enough for browsers to begin consuming the download.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export async function downloadApi(path, { filename, errorMessage, ...options }) {
  const response = await ensureSuccess(await fetchApi(path, options), errorMessage)
  saveBlob(await response.blob(), filename)
}

export function createCsv(rows, { delimiter = ';' } = {}) {
  return rows
    .map((row) =>
      row
        .map((value) => {
          let text = String(value ?? '')
          if (typeof value !== 'number' && /^[=+\-@\t\r]/.test(text)) text = "'" + text
          return '"' + text.replaceAll('"', '""') + '"'
        })
        .join(delimiter),
    )
    .join('\r\n')
}

export function downloadCsv(rows, filename, options) {
  saveBlob(
    new Blob(['\ufeff', createCsv(rows, options)], { type: 'text/csv;charset=utf-8' }),
    filename,
  )
}
