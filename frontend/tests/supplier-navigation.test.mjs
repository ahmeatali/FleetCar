import test from 'node:test'
import assert from 'node:assert/strict'
import { supplierNavigation } from '../src/utils/supplierModules.js'
import { supplierNavigationGroups } from '../src/utils/supplierNavigation.js'

test('grouped supplier menu retains every existing destination exactly once', () => {
  const links = supplierNavigationGroups.flatMap((item) => item.children || [item])
  assert.equal(links.length, supplierNavigation.length)
  assert.equal(new Set(links.map((item) => item.to)).size, links.length)
  assert.deepEqual(
    links.map((item) => item.to).sort(),
    supplierNavigation.map((item) => item.to).sort(),
  )
  for (const link of links) assert.ok(supplierNavigation.includes(link))
})

test('supplier groups have unique identities and only contain existing links', () => {
  const groups = supplierNavigationGroups.filter((item) => item.children)
  assert.equal(new Set(groups.map((item) => item.id)).size, groups.length)
  assert.deepEqual(
    groups.map((item) => item.label),
    ['Araçlar', 'Kiralamalar', 'Muhasebe', 'Raporlar', 'Ayarlar'],
  )
  for (const group of groups) {
    assert.ok(group.children.length > 0)
    assert.ok(group.children.every((item) => item?.to))
  }
})
