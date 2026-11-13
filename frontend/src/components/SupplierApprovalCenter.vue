<template>
  <div class="ac-center">
    <UiAlert v-if="error" tone="error">{{ error }}</UiAlert>
    <UiAlert v-if="notice" tone="success">{{ notice }}</UiAlert>

    <section class="ac-kpis" aria-label="Onay özeti">
      <button
        v-for="card in kpis"
        :key="card.label"
        type="button"
        class="ac-kpi"
        :class="{ active: tab === card.tab && card.tab }"
        @click="card.tab && (tab = card.tab)"
      >
        <span :class="['ac-kpi-icon', card.tone]" aria-hidden="true">{{ card.icon }}</span>
        <div>
          <small>{{ card.label }}</small>
          <strong>{{ card.value }}</strong>
          <em>{{ card.note }}</em>
        </div>
      </button>
    </section>

    <div class="ac-main">
      <section class="sw-card ac-queue">
        <div class="sw-card-heading ac-queue-heading">
          <h2>
            {{
              mine.length
                ? `Sizi Bekleyen ${mine.length} Karar`
                : `Bekleyen ${pending.length} Onay Talebi`
            }}
          </h2>
          <div class="ac-queue-tools">
            <label class="ac-inline">
              <input v-model="onlyMine" type="checkbox" /> Yalnızca benim adımım
            </label>
            <select v-model="sortBy" aria-label="Sıralama">
              <option value="priority">Öncelik sırasına göre</option>
              <option value="date">En eski talep önce</option>
              <option value="amount">Tutar (yüksekten)</option>
            </select>
          </div>
        </div>
        <nav class="ac-tabs" aria-label="Onay türleri">
          <button
            v-for="t in tabs"
            :key="t.key"
            type="button"
            :class="{ active: tab === t.key }"
            @click="tab = t.key"
          >
            {{ t.label }} ({{ countFor(t.key) }})
          </button>
        </nav>
        <div class="ac-table-wrap">
          <table class="sw-table ac-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    aria-label="Onaylayabileceğim tüm talepleri seç"
                    :checked="allSelected"
                    :disabled="!actionable.length"
                    @change="toggleAll"
                  />
                </th>
                <th>Tür / Konu</th>
                <th>Plaka / Araç</th>
                <th>Tutar</th>
                <th>Talep Eden / Tarih</th>
                <th>Öncelik / Aşama</th>
                <th>Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in shown"
                :key="a.id"
                :class="{ selected: focused?.id === a.id }"
                @click="focusedId = a.id"
              >
                <td @click.stop>
                  <input
                    v-model="selection"
                    type="checkbox"
                    :value="a.id"
                    :disabled="!canAct(a)"
                    :aria-label="`${a.number} seç`"
                  />
                </td>
                <td>
                  <span :class="['ac-type', a.category]">{{ kindLabel(a.parent?.kind) }}</span
                  ><strong>{{ a.parent?.title || a.title }}</strong
                  ><small
                    >{{ a.parent?.number || a.number }} · {{ a.details.reason || a.number }}</small
                  >
                </td>
                <td>
                  <strong>{{ a.plate || '—' }}</strong
                  ><small>{{ a.vehicle_name || a.customer_name || '' }}</small>
                </td>
                <td class="ac-amount">{{ a.amount ? money(a.amount) : '—' }}</td>
                <td>
                  <strong>{{ a.details.requested_by?.actor || 'Sistem' }}</strong
                  ><small>{{ roleText(a.details.requested_by?.role) }}</small
                  ><small>{{ dateText(a.created_at || a.date) }} · {{ ageText(a) }}</small>
                </td>
                <td>
                  <span :class="['ac-priority', a.priority.key]" :title="a.priority.reason">{{
                    a.priority.label
                  }}</span>

                  <small class="ac-stage"
                    >{{ a.stepIndex + 1 }}/{{ a.details.steps.length }} ·
                    {{ roleText(a.step?.role) }}</small
                  >
                </td>

                <td @click.stop>
                  <div class="ac-actions">
                    <template v-if="canAct(a)">
                      <button
                        type="button"
                        class="sw-button ac-approve"
                        :disabled="busy"
                        @click="approve(a)"
                      >
                        Onayla</button
                      ><button
                        type="button"
                        class="sw-button danger"
                        :disabled="busy"
                        @click="startReject(a)"
                      >
                        Reddet
                      </button>
                    </template>
                    <span v-else class="ac-waiting">{{ waitingText(a) }}</span>
                    <router-link v-if="a.parent" class="sw-button" :to="linkFor(a.parent)"
                      >Detay</router-link
                    >
                  </div>
                </td>
              </tr>
              <tr v-if="!shown.length">
                <td colspan="7" class="sw-empty">Bu görünümde bekleyen onay talebi yok.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="selection.length" class="ac-bulk">
          <span>{{ selection.length }} talep seçildi</span>
          <button type="button" class="sw-button primary" :disabled="busy" @click="bulkApprove">
            Seçilenleri Onayla
          </button>
          <button type="button" class="sw-button" @click="selection = []">Seçimi Temizle</button>
        </div>
      </section>

      <aside class="ac-side">
        <section class="sw-card">
          <div class="sw-card-heading">
            <h2>Onay Özeti</h2>
            <small>Bu ay</small>
          </div>
          <div class="ac-summary">
            <div class="ac-donut" :style="{ background: donut }">
              <div>
                <strong>{{ monthTotal }}</strong
                ><small>Toplam Talep</small>
              </div>
            </div>
            <ul>
              <li v-for="s in summary" :key="s.label">
                <i :style="{ background: s.color }" />
                <span
                  >{{ s.label }}<b>{{ s.count }}</b></span
                ><em>%{{ monthTotal ? Math.round((s.count / monthTotal) * 100) : 0 }}</em>
              </li>
            </ul>
          </div>
        </section>

        <section class="sw-card ac-quick">
          <h2>Hızlı Aksiyonlar</h2>
          <button type="button" :disabled="!actionable.length" @click="selectAllActionable">
            <span>☑</span>Toplu onay için seç ({{ actionable.length }})<b>›</b>
          </button>
          <button type="button" @click="openMatrix">
            <span>⚙</span>{{ isOwner ? 'Yetki limitlerini düzenle' : 'Yetki limitlerini gör'
            }}<b>›</b>
          </button>
          <router-link to="/supplier-portal/contracts"
            ><span>▤</span>Sözleşme yenileme sürecine git<b>›</b></router-link
          >
          <router-link to="/supplier-portal/maintenance"
            ><span>⚒</span>Bakım önerilerini incele<b>›</b></router-link
          >
          <router-link v-if="isOwner" to="/supplier-portal/users"
            ><span>👥</span>Onaycı kullanıcıları yönet<b>›</b></router-link
          >
        </section>

        <section v-if="urgent.length" class="sw-card ac-urgent">
          <h2>⚠ Acil Onay Gerekenler ({{ urgent.length }})</h2>
          <button
            v-for="a in urgent.slice(0, 4)"
            :key="a.id"
            type="button"
            @click="focusedId = a.id"
          >
            <div>
              <strong>{{ a.plate || a.parent?.number }} · {{ kindLabel(a.parent?.kind) }}</strong
              ><span>{{ a.amount ? money(a.amount) : a.title }}</span>
              <small>{{ ageText(a) }} · {{ roleText(a.step?.role) }}</small>
            </div>
            <b>›</b>
          </button>
        </section>
      </aside>
    </div>

    <div class="ac-bottom">
      <section ref="matrixCard" class="sw-card ac-matrix">
        <div class="sw-card-heading">
          <h2>Yetki Limitleri ve Onay Matrisi</h2>
          <template v-if="isOwner">
            <button v-if="!editing" type="button" class="sw-button" @click="startEdit">
              Düzenle
            </button>
            <span v-else class="ac-actions">
              <button type="button" class="sw-button" :disabled="busy" @click="editing = false">
                Vazgeç</button
              ><button type="button" class="sw-button primary" :disabled="busy" @click="saveMatrix">
                Kaydet
              </button>
            </span>
          </template>
        </div>
        <p class="sw-muted">
          {{ money(settings.approval_threshold) }} üzerindeki işlemler onaya düşer. Talep, tutarı
          kapsayan ilk role kadar sırayla ilerler; boş bırakılan rol o konuda onay zincirine girmez.
          Genel Müdür limitsizdir ve tek onayla zinciri tamamlar.
        </p>
        <div class="ac-table-wrap">
          <table class="sw-table">
            <thead>
              <tr>
                <th>Konu</th>
                <th v-for="r in approvalRoles" :key="r">{{ roleText(r) }}</th>
                <th>Genel Müdür</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in categoryKeys" :key="c">
                <td>{{ categoryLabels[c] }}</td>
                <td v-for="r in approvalRoles" :key="r">
                  <input
                    v-if="editing"
                    v-model="draft[c][r]"
                    class="ac-limit-input"
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="Yok"
                    :aria-label="`${categoryLabels[c]} ${roleText(r)} limiti`"
                  />
                  <span v-else>{{ limitText(matrix[c][r]) }}</span>
                </td>
                <td>Sınırsız</td>
              </tr>
            </tbody>
          </table>
        </div>
        <UiAlert v-if="matrixError" tone="error">{{ matrixError }}</UiAlert>
      </section>

      <section class="sw-card ac-flow">
        <div class="sw-card-heading">
          <h2>Onay Süreci Akışı</h2>
          <small v-if="focused">{{ focused.number }}</small>
        </div>
        <template v-if="focused">
          <p class="ac-flow-title">
            <strong>{{ focused.parent?.title || focused.title }}</strong
            ><span
              >{{ focused.plate || '' }} {{ focused.amount ? money(focused.amount) : '' }}</span
            >
          </p>
          <ol class="ac-steps">
            <li class="done">
              <strong>Talep Oluşturuldu</strong>
              <small
                >{{ focused.details.requested_by?.actor || 'Sistem' }} ·
                {{ dateText(focused.created_at || focused.date) }}</small
              >
            </li>
            <li v-for="(s, i) in focused.details.steps" :key="i" :class="stepClass(focused, s, i)">
              <strong
                >{{ roleText(s.role) }} Onayı
                <em>{{ s.limit == null ? 'limitsiz' : `≤ ${tl(s.limit)}` }}</em></strong
              >
              <small v-if="s.actor">{{ s.actor }} · {{ s.status }} · {{ dateText(s.at) }}</small>
              <small v-else-if="i === focused.stepIndex && focused.raw_status === 'Beklemede'"
                >Karar bekleniyor</small
              >
              <small v-else>Bekleniyor</small>
              <small v-if="s.note" class="ac-note">“{{ s.note }}”</small>
            </li>
            <li
              :class="
                focused.raw_status === 'Onaylandı'
                  ? 'done'
                  : focused.raw_status === 'Reddedildi'
                    ? 'rejected'
                    : ''
              "
            >
              <strong>{{
                focused.raw_status === 'Reddedildi' ? 'Reddedildi' : 'Tamamlandı'
              }}</strong>
              <small>{{
                focused.raw_status === 'Beklemede'
                  ? 'Onay tamamlanınca işlem devam edebilir'
                  : focused.raw_status
              }}</small>
            </li>
          </ol>
          <div v-if="canAct(focused)" class="ac-actions">
            <button
              type="button"
              class="sw-button primary"
              :disabled="busy"
              @click="approve(focused)"
            >
              Onayla</button
            ><button
              type="button"
              class="sw-button danger"
              :disabled="busy"
              @click="startReject(focused)"
            >
              Reddet
            </button>
          </div>
        </template>
        <p v-else class="sw-empty">Akışını görmek için bir onay talebi seçin.</p>
      </section>

      <section class="sw-card ac-history">
        <div class="sw-card-heading">
          <h2>Onay Geçmişi</h2>
          <small>Son {{ history.length }} karar</small>
        </div>
        <div class="ac-table-wrap">
          <table class="sw-table">
            <thead>
              <tr>
                <th>Tarih</th>
                <th>Plaka / Araç</th>
                <th>Konu</th>
                <th>Tutar</th>
                <th>Durum</th>
                <th>Karar Veren</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in history" :key="a.id" @click="focusedId = a.id">
                <td>{{ dateText(a.decidedAt) }}</td>
                <td>{{ a.plate || '—' }}</td>
                <td>{{ kindLabel(a.parent?.kind) }}</td>
                <td>{{ a.amount ? money(a.amount) : '—' }}</td>
                <td>
                  <span :class="['ac-status', a.raw_status === 'Onaylandı' ? 'ok' : 'no']">{{
                    a.raw_status
                  }}</span>
                </td>
                <td>{{ a.decidedBy }}</td>
              </tr>
              <tr v-if="!history.length">
                <td colspan="6" class="sw-empty">Henüz sonuçlanmış onay yok.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <UiModal v-if="rejecting" class="sw-modal-overlay" :busy="busy" @close="rejecting = null">
      <section class="sw-form-modal" aria-labelledby="ac-reject-title">
        <h2 id="ac-reject-title">Onay Talebini Reddet</h2>
        <p class="sw-muted">
          {{ rejecting.parent?.number || rejecting.number }} ·
          {{ rejecting.amount ? money(rejecting.amount) : '' }}. Ret gerekçesi talep sahibine ve
          onay geçmişine yazılır.
        </p>
        <form @submit.prevent="confirmReject">
          <UiField
            >Ret Gerekçesi<textarea
              v-model="rejectNote"
              rows="3"
              minlength="3"
              maxlength="1000"
              required
            />
          </UiField>
          <div class="ac-actions">
            <button type="button" class="sw-button" :disabled="busy" @click="rejecting = null">
              Vazgeç</button
            ><button type="submit" class="sw-button danger" :disabled="busy">Reddet</button>
          </div>
        </form>
      </section>
    </UiModal>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { UiAlert, UiField, UiModal } from './ui/index.js'
import { supplierApi } from '../utils/supplierApi'
import { roleLabels, supplierModules } from '../utils/supplierModules'
import { formatDate, formatMoney } from '../utils/formatters.js'

const props = defineProps({
  data: { type: Object, required: true },
  role: { type: String, default: 'viewer' },
  linkFor: { type: Function, required: true },
})
const emit = defineEmits(['updated'])

const approvalRoles = ['fleet_manager', 'operations', 'finance']
const approverLabels = {
  fleet_manager: 'Filo Yöneticisi',
  operations: 'Operasyon Müdürü',
  finance: 'Finans Müdürü',
  owner: 'Genel Müdür',
}
const categoryLabels = {
  service: 'Servis / Bakım',
  tire: 'Lastik',
  damage: 'Hasar / Kaza',
  contract: 'Sözleşme / Teklif',
  policy: 'Sigorta / Kasko',
  return: 'Teslim / İade',
  invoice: 'Fatura / Ceza',
  sale: 'Araç Satışı',
  other: 'Diğer',
}
const categoryKeys = Object.keys(categoryLabels)
const tabGroups = {
  financial: ['invoice'],
  operation: ['service', 'tire', 'damage', 'return'],
  contract: ['contract', 'policy', 'sale'],
  other: ['other'],
}
const tabs = [
  { key: 'all', label: 'Tümü' },
  { key: 'financial', label: 'Finansal' },
  { key: 'operation', label: 'Operasyon' },
  { key: 'contract', label: 'Sözleşme' },
  { key: 'other', label: 'Diğer' },
]

const tab = ref('all'),
  sortBy = ref('priority'),
  onlyMine = ref(false),
  selection = ref([]),
  focusedId = ref(null),
  busy = ref(false),
  error = ref(''),
  notice = ref(''),
  rejecting = ref(null),
  rejectNote = ref(''),
  editing = ref(false),
  matrixError = ref(''),
  matrixCard = ref(null),
  draft = reactive({})

const money = (v) => formatMoney(Number(v) || 0)
const dateText = (v) => (v ? formatDate(String(v).slice(0, 10)) : '—')
const roleText = (r) => approverLabels[r] || roleLabels[r] || (r ? r : 'Sistem')
const tl = (v) => `${Math.round(Number(v) || 0).toLocaleString('tr-TR')} TL`
const limitText = (v) => (v == null ? '—' : `≤ ${tl(v)}`)
const kindNames = {
  contract: 'Sözleşme',
  offer: 'Teklif',
  policy: 'Sigorta / Kasko',
  damage: 'Hasar / Kaza',
  maintenance: 'Bakım',
  service: 'Servis',
  tire: 'Lastik',
  delivery: 'Teslimat',
  return: 'Araç İade',
  invoice: 'Fatura',
  fine: 'Trafik Cezası',
  sale: 'Araç Satışı',
}
const kindLabel = (kind) =>
  kindNames[kind] ||
  Object.values(supplierModules).find((m) => m.kind === kind && !m.readonly)?.label ||
  'İşlem'
const isOwner = computed(() => props.role === 'owner')
const userId = computed(() => props.data.session?.user_id ?? null)
const settings = computed(() => props.data.settings || {})
const matrix = computed(() => settings.value.approval_matrix || {})

const todayMs = new Date(new Date().toDateString()).getTime()
const ageDays = (a) =>
  Math.max(
    0,
    Math.floor(
      (todayMs - new Date(String(a.created_at || a.date).slice(0, 10)).getTime()) / 86400000,
    ),
  )
const ageText = (a) => {
  const d = ageDays(a)
  return d === 0 ? 'Bugün' : `${d} gündür bekliyor`
}

// Priority is derived from waiting time and amount so the rule is visible to the user.
function priority(a) {
  const d = ageDays(a),
    amount = Number(a.amount) || 0
  if (d >= 3 || amount >= 250000)
    return { key: 'high', label: 'Yüksek', reason: '3+ gündür bekliyor veya tutar ≥ 250.000 TL' }
  if (d >= 1 || amount >= 50000)
    return { key: 'mid', label: 'Orta', reason: '1+ gündür bekliyor veya tutar ≥ 50.000 TL' }
  return { key: 'low', label: 'Düşük', reason: 'Yeni ve düşük tutarlı talep' }
}

const records = computed(() => props.data.records || [])
const byId = computed(() => Object.fromEntries(records.value.map((r) => [r.id, r])))
const approvals = computed(() =>
  records.value
    .filter((r) => r.kind === 'approval')
    .map((r) => {
      const steps = r.details?.steps || []
      const stepIndex = Math.max(
        0,
        steps.findIndex((s) => s.status === 'Bekliyor'),
      )
      const decided = [...steps].reverse().find((s) => s.at)
      return {
        ...r,
        details: { ...r.details, steps },
        parent: byId.value[r.parent_id],
        category: r.details?.category || 'other',
        stepIndex,
        step: steps[stepIndex],
        priority: priority(r),
        decidedAt: decided?.at || r.date,
        decidedBy: decided ? `${decided.actor} (${roleText(decided.actor_role)})` : '—',
      }
    }),
)
const pending = computed(() => approvals.value.filter((a) => a.raw_status === 'Beklemede'))
const canAct = (a) =>
  a.raw_status === 'Beklemede' &&
  !!a.step &&
  (isOwner.value ||
    (a.step.role === props.role &&
      !(userId.value && a.details.requested_by?.user_id === userId.value)))
const mine = computed(() => pending.value.filter(canAct))
const actionable = computed(() => shown.value.filter(canAct))
const inTab = (a, key) => key === 'all' || (tabGroups[key] || []).includes(a.category)
const countFor = (key) =>
  pending.value.filter((a) => inTab(a, key) && (!onlyMine.value || canAct(a))).length
const priorityRank = { high: 0, mid: 1, low: 2 }
const shown = computed(() =>
  pending.value
    .filter((a) => inTab(a, tab.value) && (!onlyMine.value || canAct(a)))
    .sort((x, y) =>
      sortBy.value === 'amount'
        ? (y.amount || 0) - (x.amount || 0)
        : sortBy.value === 'date'
          ? String(x.created_at || x.date).localeCompare(String(y.created_at || y.date))
          : priorityRank[x.priority.key] - priorityRank[y.priority.key] || ageDays(y) - ageDays(x),
    ),
)
const urgent = computed(() =>
  pending.value.filter((a) => a.priority.key === 'high').sort((x, y) => ageDays(y) - ageDays(x)),
)
const allSelected = computed(
  () =>
    actionable.value.length > 0 && actionable.value.every((a) => selection.value.includes(a.id)),
)
const focused = computed(
  () => approvals.value.find((a) => a.id === focusedId.value) || shown.value[0] || null,
)
const history = computed(() =>
  approvals.value
    .filter((a) => a.raw_status !== 'Beklemede')
    .sort((x, y) => String(y.decidedAt).localeCompare(String(x.decidedAt)))
    .slice(0, 8),
)

const monthKey = new Date().toLocaleDateString('en-CA').slice(0, 7)
const inMonth = (a, field) => String(a[field] || '').slice(0, 7) === monthKey
const monthApproved = computed(
  () =>
    approvals.value.filter((a) => a.raw_status === 'Onaylandı' && inMonth(a, 'decidedAt')).length,
)
const monthRejected = computed(
  () =>
    approvals.value.filter((a) => a.raw_status === 'Reddedildi' && inMonth(a, 'decidedAt')).length,
)
const summary = computed(() => [
  { label: 'Onaylanan', count: monthApproved.value, color: '#13b785' },
  { label: 'Reddedilen', count: monthRejected.value, color: '#f15d6d' },
  { label: 'Bekleyen', count: pending.value.length, color: '#ffb547' },
])
const monthTotal = computed(() => summary.value.reduce((s, x) => s + x.count, 0))
const donut = computed(() => {
  if (!monthTotal.value) return 'conic-gradient(#e8eef6 0 100%)'
  let at = 0
  return `conic-gradient(${summary.value
    .map((s) => {
      const from = at
      at += (s.count / monthTotal.value) * 100
      return `${s.color} ${from}% ${at}%`
    })
    .join(', ')})`
})

const sumOf = (list) => list.reduce((s, a) => s + (Number(a.amount) || 0), 0)
const group = (key) => pending.value.filter((a) => inTab(a, key))
const kpis = computed(() => [
  {
    label: 'Bekleyen Onaylar',
    value: pending.value.length,
    note: `${urgent.value.length} acil`,
    icon: '◷',
    tone: 'red',
    tab: 'all',
  },
  {
    label: 'Sizi Bekleyen',
    value: mine.value.length,
    note: roleText(props.role),
    icon: '☑',
    tone: 'blue',
  },
  {
    label: 'Onaylanan (Bu Ay)',
    value: monthApproved.value,
    note: 'Sonuçlanan talepler',
    icon: '✓',
    tone: 'green',
  },
  {
    label: 'Reddedilen (Bu Ay)',
    value: monthRejected.value,
    note: 'Gerekçeli ret',
    icon: '✕',
    tone: 'red',
  },
  {
    label: 'Finansal Onaylar',
    value: group('financial').length,
    note: `Toplam ${money(sumOf(group('financial')))}`,
    icon: '▤',
    tone: 'blue',
    tab: 'financial',
  },
  {
    label: 'Operasyon Onayları',
    value: group('operation').length,
    note: `Toplam ${money(sumOf(group('operation')))}`,
    icon: '⚒',
    tone: 'purple',
    tab: 'operation',
  },
  {
    label: 'Sözleşme Onayları',
    value: group('contract').length,
    note: `Toplam ${money(sumOf(group('contract')))}`,
    icon: '▣',
    tone: 'amber',
    tab: 'contract',
  },
])

function waitingText(a) {
  if (a.step && userId.value && a.details.requested_by?.user_id === userId.value)
    return 'Kendi talebiniz'
  return `${roleText(a.step?.role)} bekleniyor`
}
function stepClass(a, s, i) {
  if (s.status === 'Onaylandı') return 'done'
  if (s.status === 'Reddedildi') return 'rejected'
  return i === a.stepIndex && a.raw_status === 'Beklemede' ? 'current' : ''
}
function toggleAll(e) {
  selection.value = e.target.checked ? actionable.value.map((a) => a.id) : []
}
function selectAllActionable() {
  selection.value = actionable.value.map((a) => a.id)
}
watch(shown, (list) => {
  const ids = new Set(list.filter(canAct).map((a) => a.id))
  selection.value = selection.value.filter((id) => ids.has(id))
})

async function decide(a, decision, note = '') {
  return supplierApi(`/records/${a.id}/decision`, {
    method: 'POST',
    body: { decision, note, version: a.version },
  })
}
async function run(task, message) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await task()
    notice.value = typeof message === 'function' ? message(result) : message
    emit('updated')
  } catch (e) {
    error.value = e.message
    emit('updated')
  } finally {
    busy.value = false
  }
}
function approve(a) {
  focusedId.value = a.id
  run(
    () => decide(a, 'approve'),
    (result) => {
      const ref = a.parent?.number || a.number
      if (result.raw_status === 'Onaylandı') return `${ref} için onay süreci tamamlandı.`
      const next = (result.details?.steps || []).find((s) => s.status === 'Bekliyor')
      return `${ref}: adım onaylandı, sıradaki onaycı ${roleText(next?.role)}.`
    },
  )
}
function startReject(a) {
  rejecting.value = a
  rejectNote.value = ''
}
function confirmReject() {
  const a = rejecting.value
  run(
    async () => {
      await decide(a, 'reject', rejectNote.value)
      rejecting.value = null
    },
    `${a.parent?.number || a.number} reddedildi.`,
  )
}
function bulkApprove() {
  const list = pending.value.filter((a) => selection.value.includes(a.id) && canAct(a))
  let done = 0
  const failed = []
  run(async () => {
    for (const a of list) {
      try {
        await decide(a, 'approve')
        done++
      } catch (e) {
        failed.push(`${a.parent?.number || a.number}: ${e.message}`)
      }
    }
    selection.value = []
    if (failed.length)
      throw new Error(`${done} talep onaylandı. Onaylanamayanlar: ${failed.join(' · ')}`)
  }, `${list.length} talep onaylandı.`)
}

function startEdit() {
  for (const c of categoryKeys) draft[c] = { ...(matrix.value[c] || {}) }
  matrixError.value = ''
  editing.value = true
}
async function openMatrix() {
  if (isOwner.value && !editing.value) startEdit()
  await nextTick()
  matrixCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
async function saveMatrix() {
  matrixError.value = ''
  const next = {}
  for (const c of categoryKeys) {
    next[c] = {}
    let previous = 0
    for (const r of approvalRoles) {
      const raw = draft[c][r]
      const value = raw === '' || raw == null ? null : Number(raw)
      if (value != null && (!Number.isFinite(value) || value < 0)) {
        matrixError.value = `${categoryLabels[c]}: limitler sıfır veya pozitif olmalı.`
        return
      }
      if (value != null && value < previous) {
        matrixError.value = `${categoryLabels[c]}: ${roleText(r)} limiti alt rolden düşük olamaz.`
        return
      }
      if (value != null) previous = value
      next[c][r] = value
    }
  }
  busy.value = true
  try {
    await supplierApi('/settings', {
      method: 'PUT',
      body: { ...settings.value, approval_matrix: next },
    })
    editing.value = false
    notice.value = 'Onay matrisi kaydedildi. Yeni talepler bu limitlerle oluşturulur.'
    emit('updated')
  } catch (e) {
    matrixError.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.ac-center {
  display: grid;
  gap: 16px;
  min-width: 0;
}
.ac-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}
.ac-kpi {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  text-align: left;
  background: white;
  border: 1px solid #e8eff6;
  border-radius: 7px;
  padding: 14px 12px;
  color: #102e64;
  font: inherit;
  cursor: pointer;
  min-width: 0;
}
.ac-kpi.active {
  border-color: #0064ff;
  box-shadow: 0 0 0 1px #0064ff inset;
}
.ac-kpi small {
  font-size: 11px;
  color: #60769c;
}
.ac-kpi strong {
  display: block;
  font-size: 22px;
  color: #061d63;
  margin-top: 2px;
}
.ac-kpi em {
  display: block;
  font-size: 11px;
  font-style: normal;
  color: #5f759a;
  overflow-wrap: anywhere;
}
.ac-kpi-icon {
  display: grid;
  place-items: center;
  width: 36px;
  min-width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 17px;
  background: #eaf2ff;
  color: #0064ff;
}
.ac-kpi-icon.green {
  background: #e8f8f0;
  color: #047857;
}
.ac-kpi-icon.red {
  background: #ffe9ed;
  color: #e34058;
}
.ac-kpi-icon.amber {
  background: #fff4e2;
  color: #f0a527;
}
.ac-kpi-icon.purple {
  background: #f1ebfd;
  color: #8d68d7;
}
.ac-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}
.ac-side {
  display: grid;
  gap: 16px;
}
.ac-queue-heading {
  flex-wrap: wrap;
}
.ac-queue-tools {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 11px;
}
.ac-queue-tools select {
  font: inherit;
  font-size: 11px;
  padding: 6px 8px;
  border: 1px solid #dfe9f4;
  border-radius: 5px;
  color: #1b4889;
}
.ac-inline {
  display: flex;
  gap: 6px;
  align-items: center;
  color: #4c6690;
}
.ac-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #e7eff8;
  margin-bottom: 8px;
  overflow-x: auto;
}
.ac-tabs button {
  border: 0;
  background: none;
  font: inherit;
  font-size: 11px;
  padding: 8px 12px;
  color: #60769c;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
}
.ac-tabs button.active {
  color: #0064ff;
  border-color: #0064ff;
  font-weight: 600;
}
.ac-table-wrap {
  overflow-x: auto;
}
.ac-table td,
.ac-table th {
  white-space: nowrap;
  vertical-align: middle;
  padding: 11px 7px;
}
.ac-table td small,
.ac-history td small {
  display: block;
  color: #607596;
  font-size: 11px;
}
.ac-table tbody tr {
  cursor: pointer;
}
.ac-table tbody tr.selected {
  background: #f3f8ff;
}
.ac-amount {
  font-weight: 700;
}
.ac-type {
  display: inline-block;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 5px;
  background: #eaf2ff;
  color: #1f5fc4;
}
.ac-type.damage {
  background: #ffe9ed;
  color: #c9304a;
}
.ac-type.invoice {
  background: #fff4e2;
  color: #b8730c;
}
.ac-type.contract,
.ac-type.policy {
  background: #eef0ff;
  color: #4b56c7;
}
.ac-type.tire,
.ac-type.return {
  background: #f1ebfd;
  color: #7650c4;
}
.ac-type.sale {
  background: #e8f8f0;
  color: #047857;
}
.ac-priority {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 10px;
}
.ac-priority::before {
  content: '●';
  margin-right: 4px;
}
.ac-priority.high {
  background: #ffe9ed;
  color: #d4304a;
}
.ac-priority.mid {
  background: #fff4e2;
  color: #c47d0f;
}
.ac-priority.low {
  background: #eef1f6;
  color: #67758c;
}
.ac-stage {
  color: #4c6690;
  margin-top: 4px;
}
.ac-table .ac-actions {
  flex-wrap: nowrap;
}
.ac-table .sw-button {
  min-height: 28px;
  padding: 5px 9px;
}
.ac-table .ac-type {
  margin-bottom: 4px;
}
.ac-table td:nth-child(2) strong,
.ac-table td:nth-child(2) small {
  display: block;
  max-width: 210px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ac-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}
.ac-approve {
  background: #13a874;
  border-color: #13a874;
  color: white;
}
.ac-waiting {
  font-size: 11px;
  color: #627696;
}
.ac-bulk {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 10px 12px;
  background: #f3f8ff;
  border-radius: 6px;
  font-size: 12px;
}
.ac-summary {
  display: flex;
  align-items: center;
  gap: 16px;
}
.ac-donut {
  width: 116px;
  min-width: 116px;
  height: 116px;
  border-radius: 50%;
  display: grid;
  place-items: center;
}
.ac-donut > div {
  width: 78px;
  height: 78px;
  border-radius: 50%;
  background: white;
  display: grid;
  place-content: center;
  text-align: center;
}
.ac-donut strong {
  font-size: 22px;
  color: #061d63;
}
.ac-donut small {
  font-size: 11px;
  color: #627698;
}
.ac-summary ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
  flex: 1;
  font-size: 11px;
}
.ac-summary li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 8px;
  align-items: start;
}
.ac-summary li i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 3px;
}
.ac-summary li b {
  display: block;
  font-size: 13px;
  color: #061d63;
}
.ac-summary li em {
  font-style: normal;
  color: #627698;
}
.ac-quick {
  display: grid;
  gap: 2px;
}
.ac-quick h2 {
  margin-bottom: 8px;
}
.ac-quick button,
.ac-quick a {
  display: grid;
  grid-template-columns: 22px 1fr auto;
  align-items: center;
  gap: 6px;
  border: 0;
  border-bottom: 1px solid #f0f4f9;
  background: none;
  font: inherit;
  font-size: 12px;
  color: #1b3f78;
  padding: 9px 2px;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}
.ac-quick button:disabled {
  opacity: 0.5;
  cursor: default;
}
.ac-quick span {
  color: #0064ff;
}
.ac-quick b {
  color: #627696;
}
.ac-urgent {
  border-color: #f8cdd5;
  background: #fff7f8;
}
.ac-urgent h2 {
  color: #c9304a;
  margin-bottom: 10px;
}
.ac-urgent button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  border: 0;
  border-bottom: 1px solid #f8dde2;
  background: none;
  font: inherit;
  text-align: left;
  padding: 9px 0;
  cursor: pointer;
  color: #102e64;
}
.ac-urgent strong,
.ac-urgent span,
.ac-urgent small {
  display: block;
}
.ac-urgent strong {
  font-size: 12px;
}
.ac-urgent span {
  font-size: 13px;
  font-weight: 700;
}
.ac-urgent small {
  font-size: 11px;
  color: #c9304a;
}
.ac-bottom {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.ac-matrix .sw-muted {
  font-size: 11px;
  margin: -8px 0 10px;
}
.ac-matrix td,
.ac-matrix th {
  white-space: nowrap;
  font-size: 11px;
  padding: 8px 8px;
}
.ac-limit-input {
  width: 96px;
  font: inherit;
  font-size: 11px;
  padding: 4px 6px;
  border: 1px solid #cfdcec;
  border-radius: 4px;
}
.ac-flow-title {
  margin: 0 0 12px;
  font-size: 12px;
}
.ac-flow-title span {
  display: block;
  color: #627698;
}
.ac-steps {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
}
.ac-steps li {
  position: relative;
  padding: 0 0 14px 28px;
  font-size: 12px;
}
.ac-steps li::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #c6d2e2;
  background: white;
}
.ac-steps li:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 13px;
  top: 18px;
  bottom: 0;
  width: 2px;
  background: #e1e8f2;
}
.ac-steps li.done::before {
  background: #13b785;
  border-color: #13b785;
}
.ac-steps li.current::before {
  background: #0064ff;
  border-color: #0064ff;
  box-shadow: 0 0 0 4px #dbe8ff;
}
.ac-steps li.rejected::before {
  background: #f15d6d;
  border-color: #f15d6d;
}
.ac-steps strong {
  display: block;
  color: #061d63;
}
.ac-steps em {
  font-style: normal;
  font-weight: 400;
  font-size: 11px;
  color: #607596;
  margin-left: 4px;
}
.ac-steps small {
  display: block;
  color: #607596;
  font-size: 11px;
}
.ac-note {
  color: #4c6690 !important;
  font-style: italic;
}
.ac-history tbody tr {
  cursor: pointer;
}
.ac-history td {
  font-size: 11px;
  white-space: nowrap;
}
.ac-status {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 10px;
}
.ac-status.ok {
  background: #e8f8f0;
  color: #047857;
}
.ac-status.no {
  background: #ffe9ed;
  color: #c9304a;
}
.ac-history {
  grid-column: 1 / -1;
}
@media (max-width: 1100px) {
  .ac-main,
  .ac-bottom {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 600px) {
  .ac-queue-tools {
    flex-wrap: wrap;
  }
  .ac-summary {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
