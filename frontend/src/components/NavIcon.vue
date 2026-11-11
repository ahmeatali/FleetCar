<template>
  <svg
    class="nav-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.9"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import { iconPaths, iconForLabel } from '../utils/navIcons.js'

const props = defineProps({
  name: { type: String, default: '' },
  label: { type: String, default: '' },
  size: { type: [Number, String], default: 22 },
})
const paths = computed(() => iconPaths[props.name] || iconPaths[iconForLabel(props.label)])
</script>

<style scoped>
.nav-icon {
  display: block;
  flex-shrink: 0;
}
</style>
