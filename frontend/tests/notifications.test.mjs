import assert from 'node:assert/strict'
import test from 'node:test'
import { notificationsPath, portalFromPath, timeAgo } from '../src/api/notifications.js'

test('pages map to the portal whose notices they show', () => {
  assert.equal(portalFromPath('/dashboard/vehicles'), 'customer')
  assert.equal(portalFromPath('/supplier-portal/offers'), 'supplier')
  assert.equal(portalFromPath('/service-portal'), 'service')
  assert.equal(notificationsPath.supplier, '/supplier-portal/notifications')
})

test('relative times read naturally', () => {
  const now = new Date('2026-11-13T15:00:00')
  assert.equal(timeAgo('2026-11-13T14:59:40', now), 'şimdi')
  assert.equal(timeAgo('2026-11-13T14:40:00', now), '20 dk önce')
  assert.equal(timeAgo('2026-11-13T11:00:00', now), '4 sa önce')
  assert.match(timeAgo('2026-11-12T09:05:00', now), /^dün /)
  assert.equal(
    timeAgo('2026-11-01T09:05:00', now),
    new Date('2026-11-01T09:05:00').toLocaleDateString('tr-TR'),
  )
  assert.equal(timeAgo('', now), '')
})
