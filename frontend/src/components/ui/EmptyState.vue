<template>
  <div :class="['fr-empty', { compact }]" role="status">
    <span v-if="icon" class="fr-empty-icon" aria-hidden="true"
      ><NavIcon :name="icon" size="22"
    /></span>
    <p class="fr-empty-title">{{ title }}</p>
    <p v-if="text" class="fr-empty-text">{{ text }}</p>
    <div v-if="$slots.default" class="fr-empty-actions"><slot /></div>
  </div>
</template>

<script setup>
import NavIcon from '../NavIcon.vue'

defineProps({
  title: { type: String, required: true },
  text: { type: String, default: '' },
  icon: { type: String, default: '' },
  // compact: for small panels, no tall padding
  compact: { type: Boolean, default: false },
})
</script>

<style scoped>
.fr-empty {
  display: grid;
  justify-items: center;
  gap: var(--fr-space-2);
  padding: var(--fr-space-6) var(--fr-space-4);
  text-align: center;
}
.fr-empty.compact {
  padding: var(--fr-space-4) var(--fr-space-3);
}
.fr-empty-icon {
  display: inline-grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--fr-primary-soft);
  color: var(--fr-primary);
}
.fr-empty-title {
  margin: 0;
  font-size: var(--fr-text-md);
  font-weight: 600;
  color: var(--fr-ink);
}
.fr-empty-text {
  margin: 0;
  max-width: 46ch;
  font-size: var(--fr-text-sm);
  line-height: 1.5;
  color: var(--fr-muted);
}
.fr-empty-actions {
  display: flex;
  gap: var(--fr-space-2);
  flex-wrap: wrap;
  justify-content: center;
  margin-top: var(--fr-space-1);
}
</style>
