// App-wide feedback in place of the browser's alert() and confirm() boxes, rendered once by
// AppFeedback.vue. notify() shows a toast; confirmAction() opens a dialog and resolves to a
// boolean, so `if (!confirm(msg)) return` becomes `if (!(await confirmAction(msg))) return`.
// askText() replaces prompt(): it resolves to the entered text, or null when cancelled.
import { reactive } from 'vue'

export const feedback = reactive({ toasts: [], dialog: null })

const ERROR =
  /hata|yapılamadı|başarısız|geçersiz|bulunamadı|alınamadı|yüklenemedi|lütfen|seçin|gerekli|zorunlu|olmalı|eksik|izin|yetki|❌|⚠/i
const SUCCESS =
  /başarı|✅|✓|oluşturuldu|kaydedildi|gönderildi|silindi|güncellendi|eklendi|tamamlandı|onaylandı/i

export function toneFor(message) {
  const text = String(message ?? '')
  if (SUCCESS.test(text) && !/başarısız/i.test(text)) return 'success'
  if (ERROR.test(text)) return 'error'
  return 'info'
}

let nextId = 1
export function notify(message, { tone, timeout } = {}) {
  const text = String(message ?? '').trim()
  if (!text) return
  const toast = { id: nextId++, text, tone: tone || toneFor(text) }
  feedback.toasts.push(toast)
  if (feedback.toasts.length > 4) feedback.toasts.shift()
  const ms = timeout ?? (toast.tone === 'error' ? 8000 : 5000)
  setTimeout(() => dismiss(toast.id), ms)
}

export function dismiss(id) {
  const i = feedback.toasts.findIndex((t) => t.id === id)
  if (i >= 0) feedback.toasts.splice(i, 1)
}

export function confirmAction(message, { confirmText, cancelText = 'Vazgeç', danger } = {}) {
  feedback.dialog?.resolve(false) // a newer question replaces an unanswered one
  return new Promise((resolve) => {
    const isDanger = danger ?? /sil|iptal|reddet|çıkar|kaldır/i.test(String(message))
    feedback.dialog = {
      message: String(message ?? ''),
      confirmText: confirmText || (isDanger ? 'Evet, devam et' : 'Onayla'),
      cancelText,
      danger: isDanger,
      resolve: (value) => {
        feedback.dialog = null
        resolve(value)
      },
    }
  })
}

export function askText(
  message,
  defaultValue = '',
  { confirmText = 'Tamam', cancelText = 'Vazgeç' } = {},
) {
  feedback.dialog?.resolve(null)
  return new Promise((resolve) => {
    feedback.dialog = {
      message: String(message ?? ''),
      confirmText,
      cancelText,
      danger: false,
      input: { value: defaultValue ?? '' },
      resolve: (value) => {
        const input = feedback.dialog?.input
        feedback.dialog = null
        resolve(value ? (input?.value ?? '') : null)
      },
    }
  })
}
