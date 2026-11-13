import assert from 'node:assert/strict'
import test from 'node:test'
import { compactPlate, formatPlate, isTurkishPlate } from '../src/utils/plate.js'

test('plates are spaced the Turkish way whatever was typed', () => {
  assert.equal(formatPlate('34abc123'), '34 ABC 123')
  assert.equal(formatPlate('34 ABC123'), '34 ABC 123')
  assert.equal(formatPlate(' 06  a 1234 '), '06 A 1234')
  assert.equal(formatPlate('34 iz 55'), '34 IZ 55')
})

test('other plates are only tidied', () => {
  assert.equal(formatPlate('cd 123 ab'), 'CD 123 AB')
  assert.equal(formatPlate(''), '')
})

test('plate checks', () => {
  assert.equal(compactPlate('34 ABC 123'), '34ABC123')
  assert.ok(isTurkishPlate('34abc123'))
  assert.ok(!isTurkishPlate('99 ABC 123'))
  assert.ok(!isTurkishPlate('ABC 123'))
})
