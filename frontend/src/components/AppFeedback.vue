<template>
  <div class="fb-toasts" aria-live="polite">
    <div
      v-for="toast in feedback.toasts"
      :key="toast.id"
      :class="['fb-toast', toast.tone]"
      :role="toast.tone === 'error' ? 'alert' : 'status'"
    >
      <span class="fb-text">{{ toast.text }}</span>
      <button
        type="button"
        class="fb-close"
        aria-label="Bildirimi kapat"
        @click="dismiss(toast.id)"
      >
        ×
      </button>
    </div>
  </div>

  <div v-if="feedback.dialog" class="fb-backdrop" @click.self="answer(false)">
    <div
      ref="dialogEl"
      class="fb-dialog"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="fb-dialog-text"
      @keydown.esc="answer(false)"
      @keydown.tab="trapFocus"
    >
      <p id="fb-dialog-text" class="fb-message">{{ feedback.dialog.message }}</p>
      <input
        v-if="feedback.dialog.input"
        ref="inputEl"
        v-model="feedback.dialog.input.value"
        class="fb-input"
        aria-labelledby="fb-dialog-text"
        @keydown.enter.prevent="answer(true)"
      />
      <div class="fb-actions">
        <button type="button" class="fb-btn" @click="answer(false)">
          {{ feedback.dialog.cancelText }}
        </button>
        <button
          ref="confirmEl"
          type="button"
          :class="['fb-btn', feedback.dialog.danger ? 'danger' : 'primary']"
          @click="answer(true)"
        >
          {{ feedback.dialog.confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { dismiss, feedback } from '../utils/feedback.js'

const dialogEl = ref(null)
const confirmEl = ref(null)
const inputEl = ref(null)
let returnFocus = null

function answer(value) {
  feedback.dialog?.resolve(value)
}

watch(
  () => feedback.dialog,
  async (dialog, previous) => {
    if (dialog && !previous) {
      returnFocus = document.activeElement
      await nextTick()
      ;(inputEl.value || confirmEl.value)?.focus()
      inputEl.value?.select?.()
    } else if (!dialog && previous) {
      returnFocus?.focus?.()
      returnFocus = null
    }
  },
)

function trapFocus(event) {
  const buttons = [...(dialogEl.value?.querySelectorAll('button') || [])]
  if (!buttons.length) return
  const first = buttons[0]
  const last = buttons[buttons.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}
</script>

<style scoped>
.fb-toasts {
  position: fixed;
  top: calc(var(--imp-h, 0px) + 16px);
  right: 16px;
  z-index: 4000;
  display: grid;
  gap: 8px;
  width: min(380px, calc(100vw - 32px));
  pointer-events: none;
}
.fb-toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #d8e3f0;
  border-left: 4px solid #3b82f6;
  background: #ffffff;
  color: #10254c;
  font-size: 13px;
  line-height: 1.45;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}
.fb-toast.success {
  border-left-color: #16a34a;
}
.fb-toast.error {
  border-left-color: #dc2626;
}
.fb-text {
  flex: 1;
  white-space: pre-line;
}
.fb-close {
  border: 0;
  background: none;
  color: #64748b;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
}
.fb-backdrop {
  position: fixed;
  inset: 0;
  z-index: 4100;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(3, 24, 38, 0.45);
}
.fb-dialog {
  width: min(440px, 100%);
  background: #ffffff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
}
.fb-message {
  margin: 0 0 18px;
  color: #10254c;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-line;
}
.fb-input {
  width: 100%;
  box-sizing: border-box;
  margin: -6px 0 16px;
  min-height: 38px;
  padding: 0 10px;
  border: 1px solid #c9d6e6;
  border-radius: 6px;
  font: inherit;
  font-size: 14px;
  color: #10254c;
}
.fb-input:focus-visible {
  outline: 2px solid #0064ff;
  outline-offset: 1px;
}
.fb-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}
.fb-btn {
  min-height: 36px;
  padding: 0 16px;
  border-radius: 6px;
  border: 1px solid #d8e3f0;
  background: #ffffff;
  color: #1b4889;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.fb-btn.primary {
  background: #0064ff;
  border-color: #0064ff;
  color: #ffffff;
}
.fb-btn.danger {
  background: #dc2626;
  border-color: #dc2626;
  color: #ffffff;
}
.fb-btn:focus-visible,
.fb-close:focus-visible {
  outline: 2px solid #0064ff;
  outline-offset: 2px;
}
</style>
