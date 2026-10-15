<template>
  <component
    :is="as"
    :role="tone === 'error' ? 'alert' : 'status'"
    :aria-live="tone === 'error' ? 'assertive' : 'polite'"
  >
    <slot />
  </component>
</template>

<script setup>
defineProps({
  as: { type: String, default: 'p' },
  tone: {
    type: String,
    default: 'error',
    validator: (value) => ['error', 'success', 'info'].includes(value),
  },
})
</script>
