import test from 'node:test'
import assert from 'node:assert/strict'
import { effectScope, ref } from 'vue'
import { usePagination } from '../src/composables/usePagination.js'

test('shared pagination clamps pages as records change and handles an empty collection', () => {
  const scope = effectScope()
  scope.run(() => {
    const items = ref(Array.from({ length: 23 }, (_, i) => i + 1)),
      page = ref(3)
    const result = usePagination(items, { page })
    assert.equal(result.totalPages.value, 3)
    assert.deepEqual(result.pageItems.value, [21, 22, 23])
    assert.equal(result.start.value, 21)
    assert.equal(result.end.value, 23)
    items.value = [1, 2]
    assert.equal(page.value, 1)
    assert.deepEqual(result.pageItems.value, [1, 2])
    page.value = -2
    assert.equal(page.value, 1)
    items.value = []
    assert.equal(result.totalPages.value, 1)
    assert.equal(result.start.value, 0)
    assert.equal(result.end.value, 0)
  })
  scope.stop()
})
