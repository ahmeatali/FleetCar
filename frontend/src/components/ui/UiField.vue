<template>
  <label :for="inputId">
    <span v-if="label">{{ label }}<span v-if="required" aria-hidden="true"> *</span></span>
    <slot :id="fieldId" :invalid="Boolean(error)" :described-by="descriptionId" />
    <small v-if="error" :id="descriptionId" class="ui-field__error" role="alert">{{ error }}</small>
    <small v-else-if="hint" :id="descriptionId" class="ui-field__hint">{{ hint }}</small>
  </label>
</template>

<script setup>
import { computed, useId } from 'vue'

const props = defineProps({
  inputId: String,
  label: String,
  hint: String,
  error: String,
  required: Boolean,
})
const uid = useId()
const fieldId = computed(() => props.inputId || uid)
const descriptionId = computed(() =>
  props.error || props.hint ? `${fieldId.value}-description` : undefined,
)
</script>

<style scoped>
.ui-field__error {
  color: var(--danger, #c92c3e);
}
.ui-field__hint {
  color: var(--text-muted, #687b92);
}
</style>
