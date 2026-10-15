import test from 'node:test'
import assert from 'node:assert/strict'
import { createCsv } from '../src/utils/downloads.js'
import { formatMoney, formatNumber, formatDate, formatBytes } from '../src/utils/formatters.js'

test('CSV quotes delimiters/newlines and neutralizes spreadsheet formulas while preserving numeric values', () => {
  assert.equal(
    createCsv([
      ['A;B', 'a"b', 'line\nbreak', null, -12, '=1+1', '+cmd', '@value', '-formula', '\t=1'],
    ]),
    '"A;B";"a""b";"line\nbreak";"";"-12";"\'=1+1";"\'+cmd";"\'@value";"\'-formula";"\'\t=1"',
  )
})
test('localized formatters distinguish missing/invalid data from real zero', () => {
  assert.equal(formatNumber(null), '—')
  assert.equal(formatNumber('invalid'), '—')
  assert.equal(formatNumber(0), '0')
  assert.equal(formatMoney(null, { empty: 'Veri yok' }), 'Veri yok')
  assert.ok(formatMoney(1234.5).includes('1.234,50'))
  assert.equal(formatDate('invalid'), '—')
  assert.equal(formatDate(null), '—')
  assert.equal(formatBytes(2048), '2 KB')
  assert.equal(formatBytes(null), '0 B')
})
