<template>
  <div ref="container" class="notification-bell" @keydown.esc.stop="close">
    <UiButton
      ref="trigger"
      type="button"
      class="notification-trigger"
      :aria-label="unread ? `Bildirimler, ${unread} okunmamış` : 'Bildirimler'"
      :aria-expanded="open"
      @click="toggle"
    >
      <NavIcon name="bell" size="22" />
      <b v-if="unread" class="notification-count" aria-hidden="true">{{
        unread > 99 ? '99+' : unread
      }}</b>
    </UiButton>
    <Teleport to="body">
      <section
        v-if="open"
        ref="panel"
        class="notification-panel"
        :style="panelPosition"
        aria-label="Bildirimler"
        :aria-busy="loading"
        @keydown.esc.stop="close"
      >
        <header>
          <strong>Bildirimler</strong>
          <span class="notification-head-actions">
            <button v-if="unread" type="button" class="notification-mark" @click="markAll">
              Tümünü okundu say
            </button>
            <button
              type="button"
              class="notification-close"
              aria-label="Bildirimleri kapat"
              @click="close"
            >
              ×
            </button>
          </span>
        </header>
        <p v-if="loading && !items.length" class="notification-state">Yükleniyor…</p>
        <p v-else-if="error" class="notification-state is-error">
          {{ error }} <button type="button" @click="load">Tekrar dene</button>
        </p>
        <template v-else>
          <router-link
            v-for="item in items"
            :key="item.id"
            :to="item.link || allPath"
            :class="['notification-item', { unread: !item.read }]"
            @click="openItem(item)"
          >
            <span class="notification-dot" aria-hidden="true"></span>
            <span class="notification-text">
              <strong>{{ item.title }}</strong>
              <span v-if="item.body">{{ item.body }}</span>
              <small>{{ item.group_label }} · {{ timeAgo(item.created_at) }}</small>
            </span>
          </router-link>
          <p v-if="!items.length" class="notification-state">
            Henüz bildirim yok. Teklif, teslimat, servis ve hatırlatmalar burada görünecek.
          </p>
        </template>
        <footer>
          <router-link :to="allPath" @click="open = false">Tüm bildirimler</router-link>
          <router-link :to="`${allPath}?tab=settings`" @click="open = false">Ayarlar</router-link>
        </footer>
      </section>
    </Teleport>
  </div>
</template>

<script setup>
import { UiButton } from './ui/index.js'
import NavIcon from './NavIcon.vue'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  notificationsApi,
  notificationsPath,
  portalFromPath,
  timeAgo,
} from '../api/notifications.js'

const props = defineProps({
  // customer | supplier | service; taken from the page address when left out.
  portal: { type: String, default: '' },
})
const route = useRoute()
const activePortal = computed(() => props.portal || portalFromPath(route.path))
const allPath = computed(() => notificationsPath[activePortal.value])
const api = computed(() => notificationsApi(activePortal.value))

const container = ref(null),
  panel = ref(null),
  trigger = ref(null),
  open = ref(false),
  loading = ref(false),
  error = ref(''),
  items = ref([]),
  unread = ref(0),
  panelPosition = ref({})
let timer

function close() {
  open.value = false
  trigger.value?.$el?.focus?.() || trigger.value?.focus?.()
}
function outside(event) {
  if (!container.value?.contains(event.target) && !panel.value?.contains(event.target))
    open.value = false
}
function positionPanel() {
  if (!open.value) return
  const el = trigger.value?.$el || trigger.value
  const rect = el.getBoundingClientRect()
  const width = Math.min(360, window.innerWidth - 32)
  panelPosition.value = {
    position: 'fixed',
    left: Math.max(16, Math.min(rect.right - width, window.innerWidth - width - 16)) + 'px',
    top: rect.bottom + 8 + 'px',
    width: width + 'px',
    maxHeight: Math.max(160, window.innerHeight - rect.bottom - 24) + 'px',
  }
}
async function toggle() {
  open.value = !open.value
  if (open.value) {
    positionPanel()
    await load()
  }
}
async function load() {
  error.value = ''
  loading.value = true
  try {
    const data = await api.value('?limit=8')
    items.value = data.items
    unread.value = data.unread
  } catch (e) {
    error.value = e.message || 'Bildirimler yüklenemedi.'
  } finally {
    loading.value = false
  }
}
async function refreshCount() {
  if (document.hidden) return
  try {
    unread.value = (await api.value('?limit=1&unread=true')).unread
  } catch {
    // Signed out or offline: the page's own session handling takes over.
  }
}
async function openItem(item) {
  open.value = false
  if (item.read) return
  item.read = true
  unread.value = Math.max(0, unread.value - 1)
  api.value(`/${item.id}/read`, { method: 'POST' }).catch(() => {})
}
async function markAll() {
  await api.value('/read-all', { method: 'POST' }).catch(() => {})
  items.value.forEach((item) => (item.read = true))
  unread.value = 0
}
onMounted(() => {
  refreshCount()
  timer = setInterval(refreshCount, 60000)
  document.addEventListener('pointerdown', outside)
  window.addEventListener('resize', positionPanel)
  window.addEventListener('scroll', positionPanel, true)
})
onUnmounted(() => {
  clearInterval(timer)
  document.removeEventListener('pointerdown', outside)
  window.removeEventListener('resize', positionPanel)
  window.removeEventListener('scroll', positionPanel, true)
})
</script>

<style scoped>
.notification-bell {
  position: relative;
  flex: none;
  color: var(--fr-ink, #10254c);
}
.notification-trigger {
  position: relative;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--fr-border, #dce6f1);
  border-radius: 8px;
  background: #fff;
  color: inherit;
  cursor: pointer;
}
.notification-trigger:hover {
  background: #eef5ff;
}
.notification-count {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  box-sizing: border-box;
  border: 2px solid #fff;
  border-radius: 999px;
  background: var(--fr-danger, #c92c3e);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 14px;
}
.notification-panel {
  z-index: 300;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--fr-border, #dce6f1);
  border-radius: 12px;
  box-shadow: 0 14px 40px rgba(16, 43, 80, 0.18);
  color: var(--fr-text, #244165);
  text-align: left;
  font-size: 13px;
}
.notification-panel header,
.notification-panel footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
}
.notification-panel header {
  border-bottom: 1px solid var(--fr-border, #edf1f6);
}
.notification-panel header strong {
  font-size: 14px;
  color: var(--fr-ink, #10254c);
}
.notification-head-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.notification-panel button {
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.notification-mark {
  padding: 4px 6px;
  color: var(--fr-primary, #0064ff) !important;
  font-weight: 600;
  font-size: 12px !important;
}
.notification-close {
  min-width: 30px;
  min-height: 30px;
  font-size: 22px !important;
  line-height: 1;
}
.notification-state {
  margin: 0;
  padding: 18px 14px;
  color: var(--fr-muted, #5a6e90);
}
.notification-state.is-error {
  color: var(--fr-danger, #c92c3e);
}
.notification-item {
  display: flex;
  gap: 10px;
  padding: 11px 14px;
  border-bottom: 1px solid #edf1f6;
  color: inherit;
  text-decoration: none;
}
.notification-panel > a,
.notification-item {
  flex: none;
}
.notification-panel {
  overflow-y: auto;
}
.notification-item:hover {
  background: #f4f8ff;
}
.notification-dot {
  width: 8px;
  height: 8px;
  margin-top: 5px;
  flex: none;
  border-radius: 50%;
  background: transparent;
}
.notification-item.unread .notification-dot {
  background: var(--fr-primary, #0064ff);
}
.notification-item.unread strong {
  color: var(--fr-ink, #10254c);
}
.notification-text {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.notification-text strong {
  font-size: 13px;
  font-weight: 600;
}
.notification-text span,
.notification-text small {
  overflow-wrap: anywhere;
  color: var(--fr-muted, #5a6e90);
}
.notification-text span {
  font-size: 12px;
}
.notification-text small {
  font-size: 11px;
}
.notification-panel footer {
  border-top: 1px solid var(--fr-border, #edf1f6);
  margin-top: auto;
}
.notification-panel footer a {
  color: var(--fr-primary, #0064ff);
  font-weight: 600;
  text-decoration: none;
}
</style>
