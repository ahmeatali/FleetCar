<template>
  <div ref="element" tabindex="-1" @click.self="requestClose" @keydown="onKeydown">
    <slot />
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, onUnmounted, ref, useId } from 'vue'
import { isTopModal, registerModal, trapModalFocus } from './modalStack.js'

const props = defineProps({ busy: Boolean, label: String })
const emit = defineEmits(['close'])
const element = ref(null)
const titleId = useId()
let previousFocus,
  unregister,
  restoreFocus = false

function requestClose() {
  if (!props.busy && isTopModal(element.value)) emit('close')
}
function onKeydown(event) {
  if (!isTopModal(element.value)) return
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    requestClose()
  }
  trapModalFocus(event, element.value)
}

onMounted(async () => {
  previousFocus = document.activeElement
  unregister = registerModal(element.value)
  const dialog =
    element.value.querySelector('[role="dialog"]') ||
    element.value.firstElementChild ||
    element.value
  dialog.setAttribute('role', 'dialog')
  dialog.setAttribute('aria-modal', 'true')
  if (props.label) dialog.setAttribute('aria-label', props.label)
  else if (!dialog.hasAttribute('aria-labelledby') && !dialog.hasAttribute('aria-label')) {
    const heading = dialog.querySelector('h1,h2,h3,h4')
    if (heading) {
      heading.id ||= titleId
      dialog.setAttribute('aria-labelledby', heading.id)
    }
  }
  await nextTick()
  if (!element.value?.contains(document.activeElement)) {
    const first = element.value?.querySelector(
      '[autofocus],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled)',
    )
    ;(first || element.value)?.focus()
  }
})

onBeforeUnmount(() => {
  restoreFocus = isTopModal(element.value)
})
onUnmounted(() => {
  unregister?.()
  if (restoreFocus && previousFocus?.isConnected) previousFocus.focus()
})
</script>
