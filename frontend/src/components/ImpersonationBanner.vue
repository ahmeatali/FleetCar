<template>
  <div v-if="session" ref="bar" class="imp-banner" role="status">
    <span class="imp-dot" aria-hidden="true"></span>
    <span class="imp-text">
      Destek modu — <strong>{{ session.subjectName }}</strong> hesabındasınız. Bu hesabın
      kullanıcıları bunu görmez.
    </span>
    <button type="button" class="imp-exit" :disabled="busy" @click="exit">
      {{ busy ? 'Çıkılıyor…' : 'Destekten Çık' }}
    </button>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { activeImpersonation, stopImpersonation } from '../api/impersonation.js'

const session = ref(null)
const busy = ref(false)
const bar = ref(null)
const router = useRouter()
const root = document.documentElement
let observer = null

function refresh() {
  session.value = activeImpersonation()
}

// The banner is fixed; push the page (and the fixed sidebar) down by its height.
function setOffset(height) {
  root.style.setProperty('--imp-h', `${Math.ceil(height)}px`)
}
watch(session, async (active) => {
  observer?.disconnect()
  observer = null
  if (!active) {
    root.classList.remove('imp-active')
    root.style.removeProperty('--imp-h')
    return
  }
  await nextTick()
  if (!bar.value) return
  setOffset(bar.value.offsetHeight)
  root.classList.add('imp-active')
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(() => bar.value && setOffset(bar.value.offsetHeight))
    observer.observe(bar.value)
  }
})

async function exit() {
  busy.value = true
  try {
    await stopImpersonation()
  } finally {
    busy.value = false
    refresh()
    router.push('/admin-portal')
  }
}

onMounted(() => {
  refresh()
  globalThis.addEventListener('impersonation-change', refresh)
})
onUnmounted(() => {
  globalThis.removeEventListener('impersonation-change', refresh)
  observer?.disconnect()
  root.classList.remove('imp-active')
  root.style.removeProperty('--imp-h')
})
// Re-check when navigating between portal pages.
router.afterEach(() => refresh())
</script>

<style scoped>
.imp-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #7c2d12;
  color: #ffedd5;
  font-size: 0.85rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
}
.imp-text {
  flex: 1;
  min-width: 0;
}
.imp-text strong {
  color: #fff;
}
.imp-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #fb923c;
  box-shadow: 0 0 0 0 rgba(251, 146, 60, 0.7);
  animation: imp-pulse 1.8s infinite;
  flex: none;
}
@keyframes imp-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(251, 146, 60, 0.6);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(251, 146, 60, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(251, 146, 60, 0);
  }
}
@media (prefers-reduced-motion: reduce) {
  .imp-dot {
    animation: none;
  }
}
.imp-exit {
  flex: none;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font: inherit;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 6px;
  cursor: pointer;
}
.imp-exit:hover {
  background: rgba(255, 255, 255, 0.22);
}
.imp-exit:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>

<style>
/* Global offsets while support mode is on (not scoped: they target the page layout).
   Only the outer mount node is padded (App.vue's root also has id="app"). Sticky headers
   scroll inside the portal layout, which already starts below the banner, so they need no
   offset; only the viewport-fixed sidebar does. */
html.imp-active body > #app {
  padding-top: var(--imp-h, 44px);
}
html.imp-active .portal-sidebar,
html.imp-active .portal-sidebar.customer-navigation {
  top: var(--imp-h, 44px) !important;
  height: calc(100dvh - var(--imp-h, 44px)) !important;
  max-height: calc(100dvh - var(--imp-h, 44px)) !important;
}
</style>
