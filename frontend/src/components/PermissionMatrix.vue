<template>
  <UiTable label="Modül bazında erişim izinleri">
    <table class="permission-matrix">
      <thead>
        <tr>
          <th>Modül</th>
          <th v-for="(label, action) in actions" :key="action">{{ label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(label, module) in modules" :key="module">
          <th scope="row">{{ label }}</th>
          <td v-for="(title, action) in actions" :key="action">
            <input
              type="checkbox"
              :aria-label="`${label}: ${title}`"
              :checked="modelValue[module]?.[action] || false"
              :disabled="readonly || !ceiling[module]?.[action]"
              @change="change(module, action, $event.target.checked)"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </UiTable>
</template>
<script setup>
import { UiTable } from './ui/index.js'
const props = defineProps({
  modelValue: { type: Object, required: true },
  modules: Object,
  actions: Object,
  ceiling: { type: Object, required: true },
  readonly: Boolean,
})
const emit = defineEmits(['update:modelValue'])
function change(module, action, checked) {
  const next = JSON.parse(JSON.stringify(props.modelValue))
  next[module] ||= {}
  next[module][action] = checked
  if (action === 'view' && !checked)
    for (const key of Object.keys(next[module])) next[module][key] = false
  if (action !== 'view' && checked) next[module].view = true
  emit('update:modelValue', next)
}
</script>
<style scoped>
.permission-matrix {
  border-collapse: collapse;
  width: 100%;
  min-width: 600px;
  font-size: 12px;
}
th,
td {
  padding: 12px 8px;
  border-bottom: 1px solid #e8eef6;
  text-align: center;
}
th:first-child {
  text-align: left;
  min-width: 170px;
}
thead {
  color: #64748b;
  background: #f8faff;
}
input {
  width: 17px;
  height: 17px;
  accent-color: #0064ff;
  cursor: pointer;
}
input:disabled {
  cursor: default;
  opacity: 0.7;
}
</style>
