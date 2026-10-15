<template>
  <button
    ref="element"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :class="[variant && `ui-button ui-button--${variant}`, size && `ui-button--${size}`]"
  >
    <span v-if="loading" class="ui-button__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  // Unspecified type preserves native submit behavior in existing forms.
  type: { type: String, validator: (value) => ['button', 'submit', 'reset'].includes(value) },
  disabled: Boolean,
  loading: Boolean,
  variant: {
    type: String,
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost'].includes(value),
  },
  size: { type: String, validator: (value) => ['sm', 'md', 'lg'].includes(value) },
})

const element = ref(null)
defineExpose({
  element,
  focus: (options) => element.value?.focus(options),
  blur: () => element.value?.blur(),
  getBoundingClientRect: () => element.value?.getBoundingClientRect(),
})
</script>

<style scoped>
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.ui-button--primary {
  background: var(--primary, #0064ff);
  color: white;
}
.ui-button--secondary {
  background: var(--bg-card, #fff);
  border-color: var(--border-color, #dce5f0);
  color: var(--text-main, #183959);
}
.ui-button--danger {
  background: #dc3545;
  color: white;
}
.ui-button--ghost {
  background: transparent;
  color: var(--primary, #0064ff);
}
.ui-button--sm {
  padding: 6px 10px;
  font-size: 12px;
}
.ui-button--lg {
  padding: 13px 20px;
}
button:disabled {
  cursor: not-allowed;
}
button:focus-visible {
  outline: 2px solid var(--primary, #0064ff);
  outline-offset: 3px;
}
.ui-button__spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-spin 0.7s linear infinite;
}
@keyframes ui-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .ui-button__spinner {
    animation: none;
  }
}
</style>
