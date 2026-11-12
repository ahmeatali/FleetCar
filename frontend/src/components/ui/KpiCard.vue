<template>
  <component
    :is="to ? 'router-link' : clickable ? 'button' : 'div'"
    :to="to || undefined"
    :type="!to && clickable ? 'button' : undefined"
    :class="['fr-kpi', `tone-${tone}`, { 'is-link': to || clickable }]"
  >
    <span v-if="icon" class="fr-kpi-icon" aria-hidden="true"
      ><NavIcon :name="icon" size="20"
    /></span>
    <span class="fr-kpi-body">
      <span class="fr-kpi-label">{{ label }}</span>
      <strong class="fr-kpi-value">{{ value }}</strong>
      <span v-if="note" class="fr-kpi-note">{{ note }}</span>
    </span>
  </component>
</template>

<script setup>
import NavIcon from '../NavIcon.vue'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  note: { type: String, default: '' },
  icon: { type: String, default: '' },
  // blue | teal | green | amber | red | violet | gray
  tone: { type: String, default: 'blue' },
  to: { type: [String, Object], default: '' },
  // render as a button (listen with @click) instead of a static card
  clickable: { type: Boolean, default: false },
})
</script>

<style scoped>
.fr-kpi {
  display: flex;
  gap: var(--fr-space-3);
  align-items: flex-start;
  min-width: 0;
  padding: var(--fr-space-4);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius);
  background: var(--fr-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  text-decoration: none;
  box-shadow: var(--fr-shadow-sm);
}
.fr-kpi.is-link {
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.fr-kpi.is-link:hover {
  border-color: var(--fr-border-strong);
  box-shadow: var(--fr-shadow);
}
.fr-kpi-icon {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--fr-radius);
  background: var(--fr-info-soft);
  color: var(--fr-info);
}
.tone-teal .fr-kpi-icon {
  background: var(--fr-teal-soft);
  color: var(--fr-teal);
}
.tone-green .fr-kpi-icon {
  background: var(--fr-success-soft);
  color: var(--fr-success);
}
.tone-amber .fr-kpi-icon {
  background: var(--fr-warning-soft);
  color: var(--fr-warning);
}
.tone-red .fr-kpi-icon {
  background: var(--fr-danger-soft);
  color: var(--fr-danger);
}
.tone-violet .fr-kpi-icon,
.tone-purple .fr-kpi-icon {
  background: var(--fr-violet-soft);
  color: var(--fr-violet);
}
.tone-gray .fr-kpi-icon {
  background: #eef2f7;
  color: var(--fr-muted);
}
.fr-kpi-body {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.fr-kpi-label {
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.fr-kpi-value {
  font-size: var(--fr-text-xl);
  line-height: 1.2;
  color: var(--fr-ink);
}
.fr-kpi-note {
  font-size: var(--fr-text-xs);
  color: var(--fr-muted);
}
</style>
