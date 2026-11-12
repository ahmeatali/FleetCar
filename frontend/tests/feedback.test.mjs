import test from 'node:test'
import assert from 'node:assert/strict'
import {
  askText,
  confirmAction,
  dismiss,
  feedback,
  notify,
  toneFor,
} from '../src/utils/feedback.js'

test('toneFor picks error, success or info from the message', () => {
  assert.equal(toneFor('Kayıt başarıyla oluşturuldu.'), 'success')
  assert.equal(toneFor('✅ Davet gönderildi'), 'success')
  assert.equal(toneFor('İşlem başarısız oldu.'), 'error')
  assert.equal(toneFor('Lütfen bir araç seçin.'), 'error')
  assert.equal(toneFor('Rapor hazırlanıyor.'), 'info')
})

test('notify queues at most four toasts and ignores empty text', () => {
  feedback.toasts.splice(0)
  notify('')
  assert.equal(feedback.toasts.length, 0)
  for (let i = 0; i < 6; i++) notify(`mesaj ${i}`, { timeout: 5 })
  assert.equal(feedback.toasts.length, 4)
  assert.equal(feedback.toasts[0].text, 'mesaj 2')
  dismiss(feedback.toasts[0].id)
  assert.equal(feedback.toasts.length, 3)
  feedback.toasts.splice(0)
})

test('confirmAction resolves with the answer and marks destructive questions', async () => {
  const pending = confirmAction('Bu kaydı silmek istiyor musunuz?')
  assert.equal(feedback.dialog.danger, true)
  feedback.dialog.resolve(true)
  assert.equal(await pending, true)
  assert.equal(feedback.dialog, null)

  const replaced = confirmAction('Devam edilsin mi?')
  assert.equal(feedback.dialog.danger, false)
  const newer = confirmAction('Başka soru?')
  assert.equal(await replaced, false) // an unanswered question is cancelled by a newer one
  feedback.dialog.resolve(false)
  assert.equal(await newer, false)
})

test('askText returns the typed text, or null when cancelled', async () => {
  const typed = askText('Ad Soyad', 'Ali')
  feedback.dialog.input.value = 'Ayşe'
  feedback.dialog.resolve(true)
  assert.equal(await typed, 'Ayşe')

  const cancelled = askText('E-posta', 'a@b.c')
  feedback.dialog.resolve(false)
  assert.equal(await cancelled, null)
})
