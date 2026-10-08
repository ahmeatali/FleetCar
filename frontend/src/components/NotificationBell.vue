<template>
  <div ref="container" class="notification-bell" @keydown.esc.stop="close">
    <button ref="trigger" type="button" class="notification-trigger" aria-label="Bildirimler" :aria-expanded="open" @click="toggle">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M10 21h4"/></svg>
    </button>
    <Teleport to="body">
    <section v-if="open" ref="panel" class="notification-panel" :style="panelPosition" aria-label="Bildirimler" :aria-busy="loading" @keydown.esc.stop="close">
      <header><strong>Bildirimler</strong><button type="button" aria-label="Bildirimleri kapat" @click="close">×</button></header>
      <p>Son taleplerinizin güncel durumları</p>
      <p v-if="loading" role="status">Yükleniyor…</p>
      <p v-else-if="error" role="alert">{{ error }} <button type="button" @click="load">Tekrar Dene</button></p>
      <template v-else>
        <router-link v-for="request in requests" :key="request.id" :to="{path:'/dashboard/requests',query:{type:'list',request_id:request.id}}" @click="open=false">
          <strong>{{ request.vehicle_plate }} · {{ request.status }}</strong><span>{{ request.description || 'Talep #' + request.id }}</span>
        </router-link>
        <p v-if="!requests.length">Henüz bildirim bulunmuyor.</p>
      </template>
      <router-link class="notification-all" to="/dashboard/requests?type=list" @click="open=false">Tüm talepleri gör</router-link>
    </section>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
const container = ref(null), panel = ref(null), trigger = ref(null), open = ref(false), loading = ref(false), error = ref(''), requests = ref([]), panelPosition = ref({})
let controller
function close() { open.value = false; trigger.value?.focus() }
function outside(event) { if (!container.value?.contains(event.target) && !panel.value?.contains(event.target)) open.value = false }
function focusOutside(event) { outside(event) }
function positionPanel() {
  if (!open.value) return
  const rect = trigger.value.getBoundingClientRect()
  const width = Math.min(330, window.innerWidth - 32)
  panelPosition.value = { position: 'fixed', right: 'auto', left: Math.max(16, Math.min(rect.right - width, window.innerWidth - width - 16)) + 'px', top: rect.bottom + 8 + 'px', maxHeight: Math.max(80, window.innerHeight - rect.bottom - 24) + 'px' }
}
async function toggle() { open.value = !open.value; if (open.value) { positionPanel(); await load() } }
async function load() {
  controller?.abort()
  controller = new AbortController()
  const signal = controller.signal
  const customerId = localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
  error.value = ''; loading.value = true
  try {
    if (!customerId) throw new Error('Müşteri bilgisi bulunamadı.')
    const response = await fetch('/api/requests?customer_id=' + encodeURIComponent(customerId), { signal })
    if (!response.ok) throw new Error('Bildirimler yüklenemedi.')
    const data = await response.json()
    requests.value = data.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)) || b.id - a.id).slice(0, 5)
  } catch (e) { if (e.name !== 'AbortError') error.value = e.message }
  finally { if (!signal.aborted) loading.value = false }
}
onMounted(() => { document.addEventListener('pointerdown', outside); document.addEventListener('focusin', focusOutside); window.addEventListener('resize', positionPanel); window.addEventListener('scroll', positionPanel, true) })
onUnmounted(() => { controller?.abort(); document.removeEventListener('pointerdown', outside); document.removeEventListener('focusin', focusOutside); window.removeEventListener('resize', positionPanel); window.removeEventListener('scroll', positionPanel, true) })
</script>

<style scoped>
.notification-bell{position:relative;flex:none;color:#244165}.notification-trigger{display:grid;place-items:center;width:40px;height:40px;border:1px solid #dce6f1;border-radius:8px;background:#fff;color:inherit;cursor:pointer}.notification-trigger:hover{background:#eef5ff}.notification-trigger:focus-visible{outline:2px solid #0064ff;outline-offset:2px}.notification-panel{position:absolute;right:0;top:calc(100% + 8px);z-index:150;width:min(330px,calc(100vw - 32px));max-height:70dvh;overflow:auto;background:white;border:1px solid #dce6f1;border-radius:10px;box-shadow:0 12px 35px #102b5026;color:#244165;text-align:left;font-size:13px}.notification-panel header{display:flex;justify-content:space-between;align-items:center;padding:12px 14px}.notification-panel button{border:0;background:transparent;color:inherit;cursor:pointer;min-height:32px}.notification-panel header button{font-size:22px;min-width:32px}.notification-panel p{padding:0 14px;margin:8px 0 14px;color:#64748b;font-size:12px}.notification-panel a{display:block;padding:12px 14px;border-top:1px solid #edf1f6;color:inherit;text-decoration:none}.notification-panel a:hover{background:#f1f6ff}.notification-panel a strong,.notification-panel a span{display:block;font-size:12px;overflow-wrap:anywhere}.notification-panel a span{margin-top:4px;color:#64748b}.notification-panel .notification-all{color:#0064ff;text-align:center}
</style>
