<template>
  <section v-if="!hidden" class="sw-card ai-card">
    <div class="ai-head">
      <div>
        <h2><span class="ai-spark" aria-hidden="true">✦</span> AI Filo Önerileri</h2>
        <p class="ai-muted">
          {{ isCustomer ? 'Kiraladığınız araçlar' : 'Filonuz' }} her sabah 06:00'da km, sözleşme ve
          kullanım verilerine göre otomatik analiz edilir; öneriler hangi rakama dayandığıyla
          birlikte gösterilir.
        </p>
      </div>
      <div class="ai-actions">
        <small v-if="result?.generated_at" class="ai-muted"
          >{{ result.trigger === 'daily' ? 'Günlük analiz' : 'Son analiz' }}:
          {{ when(result.generated_at) }}</small
        >
        <button
          v-if="canRun"
          type="button"
          :class="['sw-button', 'ai-btn', { primary: !result }]"
          :disabled="busy"
          @click="run(Boolean(result))"
        >
          {{ busy ? 'Analiz ediliyor…' : result ? 'Şimdi Yenile' : 'Şimdi Analiz Et' }}
        </button>
      </div>
    </div>

    <UiAlert v-if="error" tone="error">{{ error }}</UiAlert>
    <div v-if="busy" class="ai-progress" role="status">
      <span class="ai-dot" /><span class="ai-dot" /><span class="ai-dot" />
      Filo verileriniz inceleniyor. Büyük filolarda bu 1-2 dakika sürebilir.
    </div>

    <template v-if="result && !busy">
      <p class="ai-summary">{{ result.summary }}</p>
      <div v-if="result.insights.length && showAll" class="ai-filters">
        <button
          v-for="f in filters"
          :key="f.key"
          type="button"
          :class="{ active: filter === f.key }"
          @click="filter = f.key"
        >
          {{ f.label }} ({{ f.count }})
        </button>
      </div>
      <div class="ai-list">
        <article v-for="(item, i) in shown" :key="i" :class="['ai-item', item.severity]">
          <header>
            <span :class="['ai-sev', item.severity]">{{ severityLabels[item.severity] }}</span>
            <span class="ai-type">{{ typeLabels[item.type] || 'Öneri' }}</span>
            <strong>{{ item.title }}</strong>
            <b v-if="item.estimated_monthly_impact_try" class="ai-impact"
              >≈ {{ money(item.estimated_monthly_impact_try) }}/ay</b
            >
          </header>
          <p class="ai-rec">{{ item.recommendation }}</p>
          <p class="ai-why"><span>Dayanak:</span> {{ item.rationale }}</p>
          <div v-if="item.plates.length" class="ai-plates">
            <router-link
              v-for="p in item.plates.slice(0, expanded[i] ? undefined : 8)"
              :key="p"
              :to="plateLink(p)"
              :title="metricText(p)"
              >{{ p }}</router-link
            ><button
              v-if="item.plates.length > 8 && !expanded[i]"
              type="button"
              @click="expanded[i] = true"
            >
              +{{ item.plates.length - 8 }} araç
            </button>
          </div>
        </article>
        <p v-if="!result.insights.length" class="ai-muted">Şu an öneri gerektiren bir durum yok.</p>
        <button
          v-if="!showAll && result.insights.length > COMPACT_COUNT"
          type="button"
          class="ai-more"
          @click="expandedAll = true"
        >
          Tüm önerileri gör ({{ result.insights.length }})
        </button>
        <button v-else-if="compact && expandedAll" type="button" class="ai-more" @click="collapse">
          Daha az göster
        </button>
      </div>
      <p class="ai-foot ai-muted">
        {{ result.vehicle_count }} araç tarandı, {{ result.flagged_count }} araç kural eşiklerine
        takıldı ve AI'ya gönderildi. Öneriler karar desteğidir; uygulamadan önce kaydı kontrol edin.
      </p>
    </template>
    <p v-else-if="!busy && !error && loaded" class="ai-muted ai-empty">
      Henüz analiz yapılmadı. İlk öneriler bir sonraki sabah 06:00'da otomatik hazırlanır{{
        canRun ? '; beklemek istemezseniz "Şimdi Analiz Et"e basın.' : '.'
      }}
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { UiAlert } from './ui/index.js'
import { supplierApi } from '../utils/supplierApi'
import { apiRequest } from '../api/http.js'
import { formatMoney } from '../utils/formatters.js'

const props = defineProps({
  role: { type: String, default: 'viewer' },
  vehicles: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  // "supplier": the rental company's own fleet; "customer": the vehicles a customer rents
  portal: { type: String, default: 'supplier' },
})
const isCustomer = computed(() => props.portal === 'customer')
function api(query = '', options = {}) {
  return isCustomer.value
    ? apiRequest(`/api/customer/reports/ai-insights${query}`, { account: 'customer', ...options })
    : supplierApi(`/ai/fleet-insights${query}`, options)
}
const COMPACT_COUNT = 3
const result = ref(null),
  busy = ref(false),
  error = ref(''),
  loaded = ref(false),
  filter = ref('all'),
  expanded = reactive({}),
  expandedAll = ref(false),
  hidden = ref(false)
const showAll = computed(() => !props.compact || expandedAll.value)

const canRun = computed(() =>
  isCustomer.value
    ? !['Görüntüleyici', 'Sürücü'].includes(props.role)
    : ['owner', 'fleet_manager', 'operations', 'finance'].includes(props.role),
)
const severityLabels = { yuksek: 'Yüksek', orta: 'Orta', dusuk: 'Düşük' }
const typeLabels = {
  km_asimi: 'Km aşımı',
  dusuk_kullanim: 'Düşük kullanım',
  transfer: 'Araç aktarımı',
  iade: 'İade',
  havuzda_bekleyen: 'Havuzda bekleyen',
  muayene_bakim: 'Muayene / bakım',
  sozlesme: 'Sözleşme',
  diger: 'Diğer',
}
const filters = computed(() => {
  const items = result.value?.insights || []
  const groups = [
    { key: 'all', label: 'Tümü', match: () => true },
    { key: 'km', label: 'Km', match: (i) => ['km_asimi', 'dusuk_kullanim'].includes(i.type) },
    {
      key: 'move',
      label: 'Aktarım / İade',
      match: (i) => ['transfer', 'iade', 'havuzda_bekleyen'].includes(i.type),
    },
    { key: 'contract', label: 'Sözleşme', match: (i) => i.type === 'sozlesme' },
    { key: 'other', label: 'Diğer', match: (i) => ['muayene_bakim', 'diger'].includes(i.type) },
  ]
  return groups
    .map((g) => ({ ...g, count: items.filter(g.match).length }))
    .filter((g) => g.key === 'all' || g.count)
})
const shown = computed(() => {
  const group = filters.value.find((f) => f.key === filter.value) || filters.value[0]
  const items = (result.value?.insights || []).filter(group.match)
  return showAll.value ? items : items.slice(0, COMPACT_COUNT)
})
function collapse() {
  expandedAll.value = false
  filter.value = 'all'
}
const byPlate = computed(() => Object.fromEntries(props.vehicles.map((v) => [v.plate, v])))
const money = (v) => formatMoney(Number(v) || 0)
const when = (v) =>
  new Date(v).toLocaleString('tr-TR', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
const plateLink = (plate) => {
  const v = byPlate.value[plate]
  const base = isCustomer.value ? '/dashboard/vehicles' : '/supplier-portal/vehicles'
  return v ? `${base}/${encodeURIComponent(v.id)}` : base
}
function metricText(plate) {
  const m = result.value?.metrics?.[plate]
  if (!m) return plate
  return [
    m.customer || m.supplier,
    m.assigned_to,
    m.usage_ratio != null ? `Kullanım oranı ${m.usage_ratio}` : null,
    m.projected_overage_km != null ? `Projeksiyon farkı ${m.projected_overage_km} km` : null,
    m.idle_days != null ? `${m.idle_days} gündür havuzda` : null,
  ]
    .filter(Boolean)
    .join(' · ')
}

async function load() {
  try {
    result.value = await api()
  } catch (e) {
    if (e.status === 403)
      hidden.value = true // e.g. drivers: the panel is not for them
    else error.value = e.message
  } finally {
    loaded.value = true
  }
}
async function run(force) {
  busy.value = true
  error.value = ''
  try {
    result.value = await api(force ? '?force=true' : '', { method: 'POST' })
    filter.value = 'all'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>

<style scoped>
/* Self-contained so the panel also looks right on pages without the workspace CSS. */
.ai-card {
  display: grid;
  gap: 12px;
  border: 1px solid #dfe6ff;
  border-radius: 7px;
  padding: 18px;
  min-width: 0;
  border-color: #dfe6ff;
  background: linear-gradient(180deg, #f7f8ff 0, white 120px);
}
.ai-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.ai-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dfe9f4;
  border-radius: 5px;
  background: white;
  color: #1b4889;
  font: inherit;
  font-size: 11px;
  min-height: 34px;
  padding: 0 14px;
  cursor: pointer;
  white-space: nowrap;
}
.ai-btn.primary {
  color: white;
  background: #0064ff;
  border-color: #0064ff;
}
.ai-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.ai-head h2 {
  font-size: 14px;
  color: #062464;
  margin: 0 0 4px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.ai-spark {
  color: #6a4cff;
}
.ai-muted {
  margin: 0;
  font-size: 11px;
  color: #6b7f9f;
}
.ai-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.ai-progress {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: #4c5ab8;
  padding: 10px 12px;
  border-radius: 6px;
  background: #f0f1ff;
}
.ai-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6a4cff;
  animation: ai-pulse 1.2s infinite ease-in-out;
}
.ai-dot:nth-child(2) {
  animation-delay: 0.2s;
}
.ai-dot:nth-child(3) {
  animation-delay: 0.4s;
  margin-right: 6px;
}
@keyframes ai-pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .ai-dot {
    animation: none;
  }
}
.ai-summary {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #1b2f5e;
}
.ai-filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.ai-filters button {
  border: 1px solid #dfe6f2;
  background: white;
  border-radius: 14px;
  font: inherit;
  font-size: 11px;
  padding: 4px 10px;
  cursor: pointer;
  color: #4c6690;
}
.ai-filters button.active {
  border-color: #6a4cff;
  color: #4b33d6;
  background: #f0edff;
}
.ai-list {
  display: grid;
  gap: 10px;
}
.ai-item {
  border: 1px solid #e7edf6;
  border-left: 3px solid #a5aec0;
  border-radius: 7px;
  padding: 12px 14px;
  background: white;
}
.ai-item.yuksek {
  border-left-color: #e34058;
}
.ai-item.orta {
  border-left-color: #f0a527;
}
.ai-item header {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.ai-item header strong {
  font-size: 13px;
  color: #061d63;
}
.ai-sev,
.ai-type {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #eef1f6;
  color: #4c6690;
}
.ai-sev.yuksek {
  background: #ffe9ed;
  color: #c9304a;
}
.ai-sev.orta {
  background: #fff4e2;
  color: #b8730c;
}
.ai-impact {
  margin-left: auto;
  font-size: 12px;
  color: #138a65;
}
.ai-rec {
  margin: 8px 0 4px;
  font-size: 12.5px;
  line-height: 1.5;
  color: #102e64;
}
.ai-why {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.5;
  color: #5a6e90;
}
.ai-why span {
  font-weight: 600;
}
.ai-plates {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}
.ai-plates a,
.ai-plates button {
  font: inherit;
  font-size: 10.5px;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid #d5deeb;
  background: #f7f9fc;
  color: #1b3f78;
  text-decoration: none;
  font-family: ui-monospace, Menlo, monospace;
  cursor: pointer;
}
.ai-foot {
  border-top: 1px solid #eef2f8;
  padding-top: 10px;
}
.ai-more {
  justify-self: start;
  border: 0;
  background: none;
  padding: 2px 0;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  color: #4b33d6;
  cursor: pointer;
}
.ai-empty {
  padding: 12px 0;
}
</style>
