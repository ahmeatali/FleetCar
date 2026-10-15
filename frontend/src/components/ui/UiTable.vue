<template>
  <div
    class="ui-table-scroll"
    :role="label ? 'region' : undefined"
    :aria-label="label"
    :tabindex="label ? 0 : undefined"
    :aria-busy="loading || undefined"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({ label: String, loading: Boolean })
</script>

<style scoped>
.ui-table-scroll {
  max-width: 100%;
  overflow-x: auto;
}
</style>
