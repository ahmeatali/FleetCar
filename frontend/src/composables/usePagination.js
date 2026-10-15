import { computed, ref, toValue, watch } from 'vue'

export function usePagination(items, { page = ref(1), pageSize = ref(10) } = {}) {
  const size = computed(() => Math.max(1, Math.floor(Number(toValue(pageSize)) || 10)))
  const rows = computed(() => toValue(items) || [])
  const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / size.value)))
  const pageItems = computed(() =>
    rows.value.slice((page.value - 1) * size.value, page.value * size.value),
  )
  const start = computed(() => (rows.value.length ? (page.value - 1) * size.value + 1 : 0))
  const end = computed(() => Math.min(page.value * size.value, rows.value.length))
  const reset = () => {
    page.value = 1
  }

  watch(size, reset)
  watch(
    [totalPages, page],
    () => {
      const safePage = Math.min(totalPages.value, Math.max(1, Math.floor(Number(page.value) || 1)))
      if (page.value !== safePage) page.value = safePage
    },
    { immediate: true, flush: 'sync' },
  )

  return { page, pageSize, totalPages, pageItems, start, end, reset }
}
