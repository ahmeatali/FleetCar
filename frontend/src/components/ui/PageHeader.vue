<template>
  <header class="fr-page-header">
    <div class="fr-page-heading">
      <span v-if="icon" class="fr-page-icon" aria-hidden="true"
        ><NavIcon :name="icon" size="20"
      /></span>
      <div>
        <p v-if="eyebrow" class="fr-page-eyebrow">{{ eyebrow }}</p>
        <h1 class="fr-page-title">{{ title }}</h1>
        <p v-if="description" class="fr-page-description">{{ description }}</p>
      </div>
    </div>
    <div v-if="$slots.actions" class="fr-page-actions"><slot name="actions" /></div>
  </header>
</template>

<script setup>
import NavIcon from '../NavIcon.vue'

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
  icon: { type: String, default: '' },
})
</script>

<style scoped>
.fr-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--fr-space-4);
  flex-wrap: wrap;
  margin-bottom: var(--fr-space-5);
}
.fr-page-heading {
  display: flex;
  gap: var(--fr-space-3);
  align-items: flex-start;
  min-width: 0;
}
.fr-page-icon {
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: var(--fr-radius);
  background: var(--fr-primary-soft);
  color: var(--fr-primary);
}
.fr-page-eyebrow {
  margin: 0 0 2px;
  font-size: var(--fr-text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--fr-muted);
}
.fr-page-title {
  margin: 0;
  font-size: var(--fr-text-2xl);
  line-height: 1.2;
  color: var(--fr-ink);
}
.fr-page-description {
  margin: 4px 0 0;
  font-size: var(--fr-text-md);
  color: var(--fr-muted);
  max-width: 70ch;
}
.fr-page-actions {
  display: flex;
  gap: var(--fr-space-2);
  flex-wrap: wrap;
  align-items: center;
}
</style>
