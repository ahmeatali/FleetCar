<template>
  <UiModal class="vi-overlay" :busy="busy" @close="$emit('close')">
    <section class="vi-modal" aria-labelledby="vi-title">
      <header class="vi-head">
        <div>
          <h2 id="vi-title">Toplu Araç Yükleme</h2>
          <p>
            Excel (.xlsx) veya CSV listenizi yükleyin. Önce önizleme gösterilir; araçlar siz
            onaylayınca kaydedilir. Aynı şaseye sahip araçlar güncellenir.
          </p>
        </div>
        <button
          type="button"
          class="vi-close"
          aria-label="Kapat"
          :disabled="busy"
          @click="$emit('close')"
        >
          ×
        </button>
      </header>

      <div
        v-if="!summary"
        class="vi-drop"
        :class="{ over: dragging }"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <strong>Dosyayı buraya bırakın veya seçin</strong>
        <small
          >En fazla 5 MB, 2.000 araç. Zorunlu sütunlar: Plaka, Şase, Marka, Tip, Model Yılı,
          Yakıt.</small
        >
        <label class="vi-btn primary vi-pick">
          Dosya Seç
          <input type="file" accept=".xlsx,.csv" :disabled="busy" @change="onPick" />
        </label>
        <button type="button" class="vi-link" @click="downloadTemplate">
          Örnek şablonu indir (CSV)
        </button>
        <p v-if="busy" class="vi-muted">Dosya okunuyor…</p>
      </div>

      <UiAlert v-if="error" tone="error">{{ error }}</UiAlert>

      <template v-if="summary">
        <div class="vi-file">
          <span>📄 {{ file?.name }}</span>
          <button type="button" class="vi-link" :disabled="busy" @click="reset">
            Başka dosya seç
          </button>
        </div>
        <div v-if="result" class="vi-done">
          <strong>Yükleme tamamlandı</strong>
          <span
            >{{ result.created }} yeni araç eklendi, {{ result.updated }} araç güncellendi.</span
          >
        </div>
        <div class="vi-stats">
          <button
            v-for="s in stats"
            :key="s.key"
            type="button"
            :class="['vi-stat', s.key, { active: filter === s.key }]"
            @click="filter = filter === s.key ? '' : s.key"
          >
            <strong>{{ s.value }}</strong
            ><small>{{ s.label }}</small>
          </button>
        </div>
        <details v-if="summary.ignored_columns.length" class="vi-ignored">
          <summary>{{ summary.ignored_columns.length }} sütun aktarılmayacak</summary>
          <p>
            Kiralama, müşteri, alış ve gelir/gider bilgileri araç kartına aktarılmaz; bunlar
            sözleşme ve muhasebe akışından yönetilir.
          </p>
          <span v-for="c in summary.ignored_columns" :key="c">{{ c }}</span>
        </details>
        <div class="vi-table-wrap">
          <table class="vi-table">
            <thead>
              <tr>
                <th>Satır</th>
                <th>Durum</th>
                <th>Plaka</th>
                <th>Şase</th>
                <th>Araç</th>
                <th>Yıl</th>
                <th>KM</th>
                <th>Muayene</th>
                <th>Not</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in shownRows" :key="r.row" :class="r.action">
                <td>{{ r.row }}</td>
                <td>
                  <span :class="['vi-badge', r.action]">{{ actionLabels[r.action] }}</span>
                </td>
                <td>{{ r.values.plate || '—' }}</td>
                <td class="vi-mono">{{ r.values.chassis_no || '—' }}</td>
                <td>
                  <strong>{{ r.values.brand }} {{ r.values.model }}</strong
                  ><small>{{ r.values.version }}</small>
                </td>
                <td>{{ r.values.year || '—' }}</td>
                <td>
                  {{ r.values.mileage != null ? r.values.mileage.toLocaleString('tr-TR') : '—' }}
                </td>
                <td>{{ r.values.inspection_date || '—' }}</td>
                <td class="vi-notes">
                  <span v-for="e in r.errors" :key="e" class="err">{{ e }}</span>
                  <span v-for="w in r.warnings" :key="w" class="warn">{{ w }}</span>
                  <span v-if="r.action === 'update'" class="info"
                    >Güncellenecek: {{ r.changes.map((c) => fieldLabels[c] || c).join(', ') }}</span
                  >
                </td>
              </tr>
              <tr v-if="!shownRows.length">
                <td colspan="9" class="vi-empty">Bu filtrede satır yok.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="vi-foot">
          <span v-if="summary.error && !result" class="vi-muted"
            >Hatalı {{ summary.error }} satır atlanır. Düzeltip dosyayı yeniden
            yükleyebilirsiniz.</span
          >
          <span v-else />
          <div class="vi-actions">
            <button type="button" class="vi-btn" :disabled="busy" @click="$emit('close')">
              {{ result ? 'Kapat' : 'Vazgeç' }}
            </button>
            <button
              v-if="!result"
              type="button"
              class="vi-btn primary"
              :disabled="busy || !(summary.create + summary.update)"
              @click="commit"
            >
              {{ busy ? 'Kaydediliyor…' : `${summary.create + summary.update} Aracı Kaydet` }}
            </button>
          </div>
        </footer>
      </template>
    </section>
  </UiModal>
</template>

<script setup>
import { computed, ref } from 'vue'
import { UiAlert, UiModal } from './ui/index.js'
import { supplierFetch } from '../utils/supplierApi'
import { downloadCsv } from '../utils/downloads.js'

const emit = defineEmits(['close', 'imported'])
const file = ref(null),
  summary = ref(null),
  result = ref(null),
  error = ref(''),
  busy = ref(false),
  dragging = ref(false),
  filter = ref('')

const actionLabels = {
  create: 'Yeni',
  update: 'Güncelleme',
  unchanged: 'Değişiklik yok',
  error: 'Hatalı',
}
const fieldLabels = {
  plate: 'Plaka',
  brand: 'Marka',
  model: 'Model',
  version: 'Versiyon',
  year: 'Yıl',
  fuel: 'Yakıt',
  color: 'Renk',
  transmission: 'Vites',
  engine_no: 'Motor No',
  inspection_date: 'Muayene',
  registration_date: 'Tescil',
  vehicle_segment: 'Segment',
  vehicle_group: 'Grup',
  license_serial_no: 'Ruhsat',
  casco_insurance_expiry_date: 'Kasko bitiş',
  traffic_insurance_expiry_date: 'Trafik bitiş',
  hgs_no: 'HGS',
  erp_id: 'ERP ID',
  mileage: 'KM',
}
const stats = computed(() =>
  summary.value
    ? [
        { key: 'create', label: 'Yeni araç', value: summary.value.create },
        { key: 'update', label: 'Güncellenecek', value: summary.value.update },
        { key: 'unchanged', label: 'Değişiklik yok', value: summary.value.unchanged },
        { key: 'error', label: 'Hatalı satır', value: summary.value.error },
      ]
    : [],
)
const shownRows = computed(() =>
  (summary.value?.rows || [])
    .filter((r) => !filter.value || r.action === filter.value)
    .sort((a, b) =>
      (a.action === 'error') === (b.action === 'error')
        ? a.row - b.row
        : a.action === 'error'
          ? -1
          : 1,
    ),
)

async function send(commitRows) {
  const query = new URLSearchParams({
    filename: file.value.name,
    commit: commitRows ? 'true' : 'false',
  })
  const response = await supplierFetch(`/vehicle-import?${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: file.value,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail
    throw new Error(typeof detail === 'string' ? detail : 'Dosya işlenemedi.')
  }
  return data
}
async function preview(picked) {
  if (!picked) return
  if (!/\.(xlsx|csv)$/i.test(picked.name)) {
    error.value = 'Yalnızca .xlsx veya .csv dosyası yükleyin.'
    return
  }
  file.value = picked
  error.value = ''
  busy.value = true
  try {
    summary.value = await send(false)
    filter.value = summary.value.error ? 'error' : ''
  } catch (e) {
    error.value = e.message
    summary.value = null
  } finally {
    busy.value = false
  }
}
function onPick(event) {
  preview(event.target.files?.[0])
  event.target.value = ''
}
function onDrop(event) {
  dragging.value = false
  preview(event.dataTransfer.files?.[0])
}
async function commit() {
  busy.value = true
  error.value = ''
  try {
    const data = await send(true)
    summary.value = data
    result.value = data.result
    filter.value = ''
    emit('imported', data.result)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
function reset() {
  file.value = null
  summary.value = null
  result.value = null
  error.value = ''
  filter.value = ''
}
function downloadTemplate() {
  downloadCsv(
    [
      [
        'Plaka',
        'Şase',
        'Marka',
        'Tip',
        'Model Yılı',
        'Yakıt',
        'KM',
        'Şanzıman',
        'Renk',
        'Motor Numarası',
        'Segment',
        'Grup',
        'Muayene Bitiş Tarih',
        'İlk Tescil Tarihi',
        'Ruhsat Seri No',
      ],
      [
        '34 ABC 123',
        'VR7EDYHZ8TJ697022',
        'CITROEN',
        'BERLINGO PLUS 1.5 BLUEHDI 130 EAT8',
        '2026',
        'Dizel',
        '7000',
        'Otomatik',
        'GRİ',
        '10Q4EP0413325',
        'B',
        'PROACE',
        '2027-04-20',
        '2026-02-13',
        'AB123456',
      ],
    ],
    'toplu-arac-sablonu.csv',
  )
}
</script>

<style scoped>
.vi-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: #03182680;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.vi-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dfe9f4;
  border-radius: 6px;
  background: white;
  color: #1b4889;
  font: inherit;
  font-size: 12px;
  min-height: 36px;
  padding: 8px 14px;
  cursor: pointer;
  white-space: nowrap;
}
.vi-btn.primary {
  color: white;
  background: #0064ff;
  border-color: #0064ff;
}
.vi-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.vi-table {
  width: 100%;
  border-collapse: collapse;
}
.vi-table th {
  text-align: left;
  color: #60769c;
  font-weight: 600;
  border-bottom: 1px solid #e7eff8;
}
.vi-table td {
  border-bottom: 1px solid #f0f4f9;
}
.vi-empty {
  text-align: center;
  color: #8a9ab3;
  padding: 20px !important;
}
.vi-modal {
  background: white;
  border-radius: 10px;
  width: min(1100px, 100%);
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 22px;
  overflow: hidden;
  color: #102e64;
}
.vi-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.vi-head h2 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #061d63;
}
.vi-head p,
.vi-muted {
  margin: 0;
  font-size: 12px;
  color: #6b7f9f;
}
.vi-close {
  border: 0;
  background: none;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: #6b7f9f;
}
.vi-drop {
  border: 2px dashed #c9d8ec;
  border-radius: 10px;
  padding: 36px 20px;
  display: grid;
  justify-items: center;
  gap: 10px;
  text-align: center;
  background: #f7faff;
}
.vi-drop.over {
  border-color: #0064ff;
  background: #eef5ff;
}
.vi-drop small {
  color: #6b7f9f;
  font-size: 11px;
}
.vi-pick input {
  display: none;
}
.vi-link {
  border: 0;
  background: none;
  color: #0064ff;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.vi-file {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}
.vi-done {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background: #e8f8f0;
  color: #138a65;
  font-size: 12px;
}
.vi-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.vi-stat {
  border: 1px solid #e3ebf5;
  border-radius: 7px;
  background: white;
  padding: 10px 12px;
  text-align: left;
  font: inherit;
  cursor: pointer;
}
.vi-stat strong {
  display: block;
  font-size: 20px;
}
.vi-stat small {
  font-size: 11px;
  color: #6b7f9f;
}
.vi-stat.create strong {
  color: #138a65;
}
.vi-stat.update strong {
  color: #0064ff;
}
.vi-stat.error strong {
  color: #d4304a;
}
.vi-stat.active {
  border-color: #0064ff;
  box-shadow: 0 0 0 1px #0064ff inset;
}
.vi-ignored {
  font-size: 11px;
  color: #4c6690;
}
.vi-ignored summary {
  cursor: pointer;
}
.vi-ignored p {
  margin: 6px 0;
}
.vi-ignored span {
  display: inline-block;
  margin: 2px 4px 2px 0;
  padding: 2px 7px;
  border-radius: 10px;
  background: #f0f4f9;
}
.vi-table-wrap {
  overflow: auto;
  min-height: 120px;
  border: 1px solid #edf2f8;
  border-radius: 7px;
}
.vi-table th,
.vi-table td {
  font-size: 11px;
  padding: 8px;
  white-space: nowrap;
  vertical-align: top;
}
.vi-table th {
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}
.vi-table td small {
  display: block;
  color: #7f91ad;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vi-table tr.error {
  background: #fff7f8;
}
.vi-mono {
  font-family: ui-monospace, Menlo, monospace;
}
.vi-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  background: #eef1f6;
  color: #6b7a92;
}
.vi-badge.create {
  background: #e8f8f0;
  color: #138a65;
}
.vi-badge.update {
  background: #eaf2ff;
  color: #1f5fc4;
}
.vi-badge.error {
  background: #ffe9ed;
  color: #c9304a;
}
.vi-notes {
  white-space: normal !important;
  min-width: 220px;
}
.vi-notes span {
  display: block;
}
.vi-notes .err {
  color: #c9304a;
}
.vi-notes .warn {
  color: #b8730c;
}
.vi-notes .info {
  color: #1f5fc4;
}
.vi-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.vi-actions {
  display: flex;
  gap: 8px;
}
@media (max-width: 700px) {
  .vi-modal {
    padding: 16px;
  }
  .vi-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .vi-foot {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
