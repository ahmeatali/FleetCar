<template>
  <UiModal class="ad-overlay" :busy="busy" @close="$emit('close')">
    <section class="ad-modal" aria-labelledby="ad-title">
      <header class="ad-head">
        <div>
          <h2 id="ad-title"><span aria-hidden="true">✦</span> AI ile {{ titles[docType] }} Oku</h2>
          <p>{{ hints[docType] }}</p>
        </div>
        <button
          type="button"
          class="ad-close"
          aria-label="Kapat"
          :disabled="busy"
          @click="$emit('close')"
        >
          ×
        </button>
      </header>

      <div
        v-if="!result"
        class="ad-drop"
        :class="{ over: dragging }"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <strong>{{ busy ? 'Belge okunuyor…' : 'Belgeyi buraya bırakın veya seçin' }}</strong>
        <small>PDF, JPG, PNG veya WEBP · en fazla 15 MB</small>
        <label v-if="!busy" class="ad-btn primary">
          Dosya Seç
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            @change="onPick"
          />
        </label>
        <p v-else class="ad-muted">Okuma genelde 10-40 saniye sürer.</p>
      </div>

      <UiAlert v-if="error" tone="error">{{ error }}</UiAlert>
      <UiAlert v-if="notice" tone="success">{{ notice }}</UiAlert>

      <div v-if="result" class="ad-body">
        <div class="ad-file">
          <span>📄 {{ fileName }}</span>
          <button type="button" class="ad-link" :disabled="busy" @click="reset">Başka belge</button>
        </div>
        <p v-if="d.notes" class="ad-note">AI notu: {{ d.notes }}</p>

        <!-- Receipt -> fuel expense -->
        <template v-if="docType === 'receipt'">
          <div class="ad-grid">
            <label
              >Araç<select v-model="form.vehicle_id">
                <option value="">Araç seçin</option>
                <option v-for="v in vehicles" :key="v.id" :value="v.id">
                  {{ v.plate }} · {{ v.brand }} {{ v.model }}
                </option>
              </select></label
            >
            <label>Tarih<input v-model="form.date" type="date" /></label>
            <label
              >Tutar (TL)<input v-model.number="form.amount" type="number" min="0" step="0.01"
            /></label>
            <label
              >Litre<input v-model.number="form.liters" type="number" min="0" step="0.01"
            /></label>
            <label>Km<input v-model.number="form.mileage" type="number" min="0" /></label>
            <label>Yakıt<input v-model="form.fuel_type" /></label>
            <label>İstasyon<input v-model="form.station" /></label>
            <label>Fiş No<input v-model="form.receipt_no" /></label>
          </div>
          <p v-if="d.plate && !d.vehicle" class="ad-warn">
            Fişteki plaka ({{ d.plate }}) filonuzda bulunamadı; aracı seçin.
          </p>
        </template>

        <!-- Invoice -> vehicle expense -->
        <template v-else-if="docType === 'invoice'">
          <dl class="ad-facts">
            <div>
              <dt>Satıcı</dt>
              <dd>{{ d.seller || '—' }}</dd>
            </div>
            <div>
              <dt>Alıcı</dt>
              <dd>{{ d.buyer || '—' }}</dd>
            </div>
            <div>
              <dt>Fatura No</dt>
              <dd>{{ d.invoice_no || '—' }}</dd>
            </div>
            <div>
              <dt>Tarih / Vade</dt>
              <dd>{{ d.date || '—' }} / {{ d.due_date || '—' }}</dd>
            </div>
            <div>
              <dt>KDV Hariç</dt>
              <dd>{{ money(d.subtotal_try) }}</dd>
            </div>
            <div>
              <dt>KDV</dt>
              <dd>{{ money(d.vat_try) }}</dd>
            </div>
            <div>
              <dt>Toplam</dt>
              <dd>
                <b>{{ money(d.total_try) }}</b>
              </dd>
            </div>
          </dl>
          <table v-if="d.lines?.length" class="ad-table">
            <thead>
              <tr>
                <th>Kalem</th>
                <th>Plaka</th>
                <th>Tutar</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(l, i) in d.lines" :key="i">
                <td>{{ l.description }}</td>
                <td>{{ l.vehicle ? l.vehicle.plate : l.plate || '—' }}</td>
                <td>{{ money(l.amount_try) }}</td>
              </tr>
            </tbody>
          </table>
          <h3>Araç giderine işle</h3>
          <div class="ad-grid">
            <label
              >Araç<select v-model="form.vehicle_id">
                <option value="">Araç seçin</option>
                <option v-for="v in vehicles" :key="v.id" :value="v.id">
                  {{ v.plate }} · {{ v.brand }} {{ v.model }}
                </option>
              </select></label
            >
            <label
              >Gider Türü<select v-model="form.kind">
                <option
                  v-for="k in ['Servis', 'Lastik', 'Yakıt', 'Sigorta', 'HGS', 'Kira', 'Diğer']"
                  :key="k"
                >
                  {{ k }}
                </option>
              </select></label
            >
            <label
              >Tutar (TL)<input v-model.number="form.amount" type="number" min="0" step="0.01"
            /></label>
            <label>Tarih<input v-model="form.date" type="date" /></label>
            <label>Km<input v-model.number="form.mileage" type="number" min="0" /></label>
          </div>
        </template>

        <!-- Contract + Ek-1/Ek-2 -> vehicle contract terms -->
        <template v-else>
          <dl class="ad-facts">
            <div>
              <dt>Sözleşme No</dt>
              <dd>{{ d.contract_no || '—' }}</dd>
            </div>
            <div>
              <dt>Kiraya Veren</dt>
              <dd>{{ d.lessor || '—' }}</dd>
            </div>
            <div>
              <dt>Kiracı</dt>
              <dd>{{ d.lessee || '—' }}</dd>
            </div>
            <div>
              <dt>Süre</dt>
              <dd>
                {{ d.start_date || '—' }} → {{ d.end_date || '—' }} ({{ d.duration_months || '—' }}
                ay)
              </dd>
            </div>
          </dl>
          <details v-if="d.general_terms?.length" class="ad-terms">
            <summary>{{ d.general_terms.length }} genel şart</summary>
            <ul>
              <li v-for="(t, i) in d.general_terms" :key="i">{{ t }}</li>
            </ul>
          </details>
          <table class="ad-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    :checked="allPicked"
                    @change="toggleAll"
                    aria-label="Tümünü seç"
                  />
                </th>
                <th>Araç (belge)</th>
                <th>Eşleşen araç</th>
                <th>Aylık Kira</th>
                <th>Km Limiti / Ay</th>
                <th>Toplam Km</th>
                <th>Süre</th>
                <th>Kaynak</th>
                <th>Sonuç</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(v, i) in d.vehicles" :key="i">
                <td>
                  <input v-model="picked" type="checkbox" :value="i" :disabled="!v.vehicle" />
                </td>
                <td>
                  <strong>{{ v.plate || '—' }}</strong
                  ><small>{{ v.chassis_no }} {{ v.brand_model }}</small>
                </td>
                <td>
                  <span v-if="v.vehicle" class="ad-ok">{{ v.vehicle.plate }}</span
                  ><span v-else class="ad-warn">Filoda yok</span>
                </td>
                <td>{{ money(v.monthly_rent_try) }}</td>
                <td>{{ v.monthly_km_limit || '—' }}</td>
                <td>{{ v.total_km || '—' }}</td>
                <td>{{ v.duration_months || d.duration_months || '—' }} ay</td>
                <td>{{ v.source || '—' }}</td>
                <td>
                  <small :class="outcome[i]?.ok ? 'ad-ok' : 'ad-warn'">{{
                    outcome[i]?.text
                  }}</small>
                </td>
              </tr>
              <tr v-if="!d.vehicles?.length">
                <td colspan="9" class="ad-muted">Belgede araç listesi bulunamadı.</td>
              </tr>
            </tbody>
          </table>
          <p class="ad-muted">
            Seçilen araçların kartına sözleşme no, başlangıç/bitiş, süre, aylık kira ve km limiti
            işlenir. Aktif kiralaması olan araçlarda bu alanlar sözleşme akışından yönetildiği için
            değiştirilmez.
          </p>
        </template>
      </div>

      <footer v-if="result" class="ad-foot">
        <small class="ad-muted">Değerleri kontrol edin; AI okuması hatalı olabilir.</small>
        <div class="ad-actions">
          <button type="button" class="ad-btn" :disabled="busy" @click="$emit('close')">
            Kapat
          </button>
          <button
            type="button"
            class="ad-btn primary"
            :disabled="busy || !canApply || applied"
            @click="apply"
          >
            {{ busy ? 'Kaydediliyor…' : applied ? 'Kaydedildi' : applyLabel }}
          </button>
        </div>
      </footer>
    </section>
  </UiModal>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { UiAlert, UiModal } from './ui/index.js'
import { supplierApi, supplierFetch } from '../utils/supplierApi'
import { formatMoney } from '../utils/formatters.js'

const props = defineProps({
  docType: { type: String, required: true },
  vehicles: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'saved'])
const titles = { receipt: 'Fiş', invoice: 'Fatura', contract: 'Sözleşme' }
const hints = {
  receipt:
    'Akaryakıt fişi veya UTTS dökümünü yükleyin; plaka, litre, tutar ve km okunur ve yakıt giderine işlenir.',
  invoice:
    'Servis, lastik, sigorta vb. faturayı yükleyin; tutarlar ve kalemler okunur, araç giderine işlenir.',
  contract:
    'Sözleşmeyi Ek-1, Ek-2 ile birlikte (tek PDF) yükleyin; araç bazında şartlar okunur ve şaseyle eşleşen araç kartlarına işlenir.',
}
const result = ref(null),
  busy = ref(false),
  error = ref(''),
  notice = ref(''),
  dragging = ref(false),
  fileName = ref(''),
  applied = ref(false),
  picked = ref([]),
  outcome = reactive({})
const form = reactive({})
const d = computed(() => result.value?.data || {})
const money = (v) => (Number(v) ? formatMoney(Number(v)) : '—')
const today = () => new Date().toLocaleDateString('en-CA')
const vehicleById = (id) => props.vehicles.find((v) => v.id === id)

const allPicked = computed(() => {
  const ok = (d.value.vehicles || []).map((v, i) => (v.vehicle ? i : null)).filter((i) => i != null)
  return ok.length > 0 && ok.every((i) => picked.value.includes(i))
})
const canApply = computed(() =>
  props.docType === 'contract'
    ? picked.value.length > 0
    : Boolean(form.vehicle_id && form.amount >= 0),
)
const applyLabel = computed(() =>
  props.docType === 'contract' ? `${picked.value.length} Araca İşle` : 'Gider Olarak Kaydet',
)

function toggleAll(e) {
  picked.value = e.target.checked
    ? (d.value.vehicles || []).map((v, i) => (v.vehicle ? i : null)).filter((i) => i != null)
    : []
}
async function read(file) {
  if (!file) return
  fileName.value = file.name
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const response = await supplierFetch(`/ai/read-document?doc_type=${props.docType}`, {
      method: 'POST',
      headers: { 'Content-Type': file.type || 'application/octet-stream' },
      body: file,
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok)
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Belge okunamadı.')
    result.value = data
    prefill(data.data)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
function prefill(x) {
  if (props.docType === 'receipt') {
    const car = x.vehicle ? vehicleById(x.vehicle.id) : null
    Object.assign(form, {
      vehicle_id: car?.id || '',
      date: x.date || today(),
      amount: x.total_try || 0,
      liters: x.liters || null,
      mileage: x.mileage || car?.mileage || 0,
      fuel_type: x.fuel_type || car?.fuel || '',
      station: x.station || '',
      receipt_no: x.receipt_no || '',
    })
  } else if (props.docType === 'invoice') {
    const matched = (x.lines || []).map((l) => l.vehicle).filter(Boolean)
    const car = matched.length ? vehicleById(matched[0].id) : null
    Object.assign(form, {
      vehicle_id: car?.id || '',
      kind: x.category || 'Diğer',
      amount: x.total_try || 0,
      date: x.date || today(),
      mileage: car?.mileage || 0,
    })
  } else {
    picked.value = (x.vehicles || []).map((v, i) => (v.vehicle ? i : null)).filter((i) => i != null)
  }
}
async function apply() {
  busy.value = true
  error.value = ''
  try {
    if (props.docType === 'contract') await applyContract()
    else await applyExpense()
    applied.value = props.docType !== 'contract' || Object.values(outcome).every((o) => o.ok)
    emit('saved')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function applyExpense() {
  const car = vehicleById(form.vehicle_id)
  const x = d.value
  const note =
    props.docType === 'invoice'
      ? `AI ile okunan fatura ${x.invoice_no || ''} · ${x.seller || ''}`.trim()
      : 'AI ile okunan fiş'
  await supplierApi('/expenses', {
    method: 'POST',
    body: {
      vehicle_id: form.vehicle_id,
      kind: props.docType === 'receipt' ? 'Yakıt' : form.kind,
      amount: Number(form.amount) || 0,
      date: form.date || today(),
      liters: props.docType === 'receipt' && Number(form.liters) > 0 ? Number(form.liters) : null,
      mileage: Math.max(0, Number(form.mileage) || 0),
      fuel_type: props.docType === 'receipt' ? form.fuel_type || car?.fuel || null : null,
      station: props.docType === 'receipt' ? form.station || null : x.seller || null,
      receipt_no: props.docType === 'receipt' ? form.receipt_no || null : x.invoice_no || null,
      note,
    },
  })
  notice.value = `${car?.plate || 'Araç'} için ${formatMoney(Number(form.amount) || 0)} gider kaydedildi.`
}
async function applyContract() {
  const x = d.value
  let ok = 0
  for (const i of picked.value) {
    const v = x.vehicles[i]
    const months = Number(v.duration_months || x.duration_months) || null
    const monthlyKm =
      Number(v.monthly_km_limit) || (v.total_km && months ? Math.round(v.total_km / months) : null)
    const body = Object.fromEntries(
      Object.entries({
        contract_no: x.contract_no || null,
        contract_start_date: x.start_date || null,
        contract_end_date: x.end_date || null,
        contract_duration_months: months,
        monthly_rent: Number(v.monthly_rent_try) || null,
        monthly_km_limit: monthlyKm,
        contract_committed_km:
          Number(v.total_km) || (monthlyKm && months ? monthlyKm * months : null),
      }).filter(([, value]) => value != null && value !== ''),
    )
    try {
      await supplierApi(`/vehicles/${encodeURIComponent(v.vehicle.id)}`, { method: 'PUT', body })
      outcome[i] = { ok: true, text: 'İşlendi' }
      ok++
    } catch (e) {
      outcome[i] = { ok: false, text: e.message }
    }
  }
  notice.value = `${ok} / ${picked.value.length} araca sözleşme şartları işlendi.`
}
function onPick(e) {
  read(e.target.files?.[0])
  e.target.value = ''
}
function onDrop(e) {
  dragging.value = false
  read(e.dataTransfer.files?.[0])
}
function reset() {
  result.value = null
  applied.value = false
  notice.value = ''
  error.value = ''
  picked.value = []
  for (const k of Object.keys(outcome)) delete outcome[k]
}
</script>

<style scoped>
.ad-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: #03182680;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.ad-modal {
  background: white;
  border-radius: 10px;
  width: min(1000px, 100%);
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px;
  overflow: hidden;
  color: #102e64;
}
.ad-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.ad-head h2 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #061d63;
}
.ad-head h2 span {
  color: #6a4cff;
}
.ad-head p,
.ad-muted {
  margin: 0;
  font-size: 12px;
  color: #627697;
}
.ad-close {
  border: 0;
  background: none;
  font-size: 24px;
  cursor: pointer;
  color: #627697;
}
.ad-drop {
  border: 2px dashed #cfd6f3;
  border-radius: 10px;
  padding: 36px 20px;
  display: grid;
  justify-items: center;
  gap: 10px;
  text-align: center;
  background: #f8f8ff;
}
.ad-drop.over {
  border-color: #6a4cff;
}
.ad-drop small {
  color: #627697;
  font-size: 11px;
}
.ad-drop input {
  display: none;
}
.ad-btn {
  display: inline-flex;
  align-items: center;
  border: 1px solid #dfe9f4;
  border-radius: 6px;
  background: white;
  color: #1b4889;
  font: inherit;
  font-size: 12px;
  min-height: 36px;
  padding: 8px 14px;
  cursor: pointer;
}
.ad-btn.primary {
  background: #0064ff;
  border-color: #0064ff;
  color: white;
}
.ad-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.ad-link {
  border: 0;
  background: none;
  color: #0064ff;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.ad-body {
  overflow: auto;
  display: grid;
  gap: 12px;
}
.ad-file {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}
.ad-note {
  margin: 0;
  font-size: 11.5px;
  color: #8a5a00;
  background: #fff8e8;
  padding: 8px 10px;
  border-radius: 6px;
}
.ad-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.ad-grid label {
  display: grid;
  gap: 4px;
  font-size: 11px;
  color: #4c6690;
}
.ad-grid input,
.ad-grid select {
  font: inherit;
  font-size: 12px;
  padding: 7px 8px;
  border: 1px solid #d5deeb;
  border-radius: 5px;
  color: #102e64;
  min-width: 0;
}
.ad-facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}
.ad-facts div {
  background: #f7f9fc;
  border-radius: 6px;
  padding: 8px 10px;
}
.ad-facts dt {
  font-size: 11px;
  color: #627697;
}
.ad-facts dd {
  margin: 2px 0 0;
  font-size: 12px;
  overflow-wrap: anywhere;
}
.ad-body h3 {
  margin: 4px 0 0;
  font-size: 13px;
}
.ad-terms {
  font-size: 12px;
}
.ad-terms summary {
  cursor: pointer;
  color: #4c6690;
}
.ad-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.ad-table th {
  text-align: left;
  color: #60769c;
  border-bottom: 1px solid #e7eff8;
  padding: 6px;
}
.ad-table td {
  border-bottom: 1px solid #f0f4f9;
  padding: 6px;
  vertical-align: top;
}
.ad-table td small {
  display: block;
  color: #607596;
}
.ad-ok {
  color: #047857;
}
.ad-warn {
  color: #b8730c;
  font-size: 11.5px;
}
.ad-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.ad-actions {
  display: flex;
  gap: 8px;
}
@media (max-width: 760px) {
  .ad-grid,
  .ad-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .ad-foot {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
