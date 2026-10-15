<template>
  <section class="sw-card sw-settings">
    <h2>Arvento GPS Bağlantısı</h2>
    <p class="sw-muted">
      Cihazları kalıcı araç kayıtlarıyla eşleyin. Son konum ve kilometre, doğrulanan kaynak zamanı
      ile araç geçmişine işlenir.
    </p>
    <UiAlert v-if="error" as="p" tone="error" class="sw-error">{{ error }}</UiAlert>
    <UiAlert v-if="notice" as="p" tone="info">{{ notice }}</UiAlert>
    <template v-if="state">
      <p>
        <strong>{{
          state.credentials_configured
            ? 'Sunucu erişim bilgileri tanımlı'
            : 'Sunucu erişim bilgileri bekleniyor'
        }}</strong>
        · {{ state.mappings.length }} cihaz eşlendi
      </p>
      <p class="sw-muted">
        Arvento kullanıcı adı ve PIN bilgileri sunucu ortamında tanımlanır. Arvento yanıtındaki alan
        adlarını hesabınızın örnek verisine göre girin. Kilometre alanı yoksa yalnızca konum alınır.
      </p>
      <form v-if="role === 'owner'" @submit.prevent="saveConfig">
        <UiField v-for="field in columns" :key="field.key"
          >{{ field.label
          }}<input
            v-model="config[field.key]"
            :required="field.key !== 'mileage_column'"
            maxlength="100"
        /></UiField>
        <UiField
          >Kilometre Birimi<select v-model="config.mileage_unit">
            <option value="km">Kilometre</option>
            <option value="m">Metre</option>
          </select></UiField
        >
        <UiField
          >Tarih Biçimi (boşsa ISO 8601)<input
            v-model="config.time_format"
            placeholder="%d.%m.%Y %H:%M:%S"
        /></UiField>
        <UiField
          >Saat Dilimi Farkı (dakika)<input
            v-model.number="config.timezone_offset_minutes"
            type="number"
            min="-840"
            max="840"
        /></UiField>
        <UiButton class="sw-button" :disabled="busy">Alan Eşlemesini Kaydet</UiButton>
      </form>
      <form v-if="role === 'owner'" @submit.prevent="saveMapping">
        <UiField
          >Arvento Cihaz Kimliği<input v-model="mapping.external_id" required maxlength="150"
        /></UiField>
        <UiField
          >Araç<select aria-label="Arvento Aracı" v-model="mapping.vehicle_id" required>
            <option value="">Araç seçin</option>
            <option v-for="car in vehicles" :key="car.id" :value="car.id">
              {{ car.plate }} · {{ car.brand }} {{ car.model }}
            </option>
          </select></UiField
        >
        <UiButton class="sw-button" :disabled="busy">Cihazı Eşle</UiButton>
      </form>
      <UiTable class="sw-table-scroll"
        ><table class="sw-table">
          <thead>
            <tr>
              <th>Cihaz</th>
              <th>Araç</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in state.mappings" :key="row.external_id">
              <td>{{ row.external_id }}</td>
              <td>{{ plate(row.vehicle_id) }}</td>
            </tr>
            <tr v-if="!state.mappings.length">
              <td colspan="2">Henüz cihaz eşlenmedi.</td>
            </tr>
          </tbody>
        </table></UiTable
      >
      <UiButton
        v-if="role === 'owner'"
        class="sw-button primary"
        :disabled="busy || !state.credentials_configured || !state.config"
        @click="sync"
        >Arvento Verilerini Al</UiButton
      >
      <h3>GPS İşleme Geçmişi</h3>
      <UiTable class="sw-table-scroll"
        ><table class="sw-table">
          <thead>
            <tr>
              <th>Cihaz / Araç</th>
              <th>Kaynak Zamanı</th>
              <th>Km</th>
              <th>Durum / Açıklama</th>
              <th>İşlem</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in state.events" :key="row.id">
              <td>{{ row.device_id }}<br />{{ plate(row.vehicle_id) }}</td>
              <td>{{ new Date(row.occurred_at).toLocaleString('tr-TR') }}</td>
              <td>{{ row.mileage ?? '—' }}</td>
              <td>
                {{ row.status }}<small>{{ row.reason }}</small>
              </td>
              <td>
                <UiButton
                  v-if="role === 'owner' && row.status === 'Eşleştirme Bekliyor'"
                  class="sw-button"
                  :disabled="busy"
                  @click="retry(row.id)"
                  >Eşlemeyi Uygula</UiButton
                >
              </td>
            </tr>
            <tr v-if="!state.events.length">
              <td colspan="5">Henüz Arvento verisi alınmadı.</td>
            </tr>
          </tbody>
        </table></UiTable
      >
    </template>
  </section>
</template>
<script setup>
import { UiAlert, UiButton, UiField, UiTable } from './ui/index.js'

import { onMounted, reactive, ref } from 'vue'
import { supplierApi } from '../utils/supplierApi'
const props = defineProps({
  vehicles: { type: Array, default: () => [] },
  role: { type: String, default: 'viewer' },
})
const emit = defineEmits(['updated'])
const state = ref(null),
  busy = ref(false),
  error = ref(''),
  notice = ref('')
const columns = [
  { key: 'device_column', label: 'Cihaz Kimliği Alanı' },
  { key: 'time_column', label: 'Konum Zamanı Alanı' },
  { key: 'latitude_column', label: 'Enlem Alanı' },
  { key: 'longitude_column', label: 'Boylam Alanı' },
  { key: 'mileage_column', label: 'Kilometre Alanı (isteğe bağlı)' },
]
const config = reactive({
  device_column: '',
  time_column: '',
  latitude_column: '',
  longitude_column: '',
  mileage_column: '',
  mileage_unit: 'km',
  time_format: '',
  timezone_offset_minutes: 180,
})
const mapping = reactive({ external_id: '', vehicle_id: '' })
const plate = (id) => props.vehicles.find((v) => v.id === id)?.plate || 'Eşlenmemiş'
async function load() {
  try {
    state.value = await supplierApi('/integrations/arvento')
    if (state.value.config) Object.assign(config, state.value.config)
  } catch (e) {
    error.value = e.message
  }
}
async function act(path, method, body, message, refreshFleet = false) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await supplierApi('/integrations/arvento' + path, { method, body })
    await load()
    notice.value = typeof message === 'function' ? message(result) : message
    if (refreshFleet) emit('updated')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
const saveConfig = () =>
  act(
    '/config',
    'PUT',
    {
      ...config,
      mileage_column: config.mileage_column || null,
      time_format: config.time_format || null,
    },
    'Arvento alan eşlemesi kaydedildi.',
  )
const saveMapping = () => act('/mappings', 'PUT', { ...mapping }, 'Cihaz araca bağlandı.')
const sync = () =>
  act(
    '/sync',
    'POST',
    undefined,
    (r) =>
      `${r.processed} kayıt işlendi, ${r.duplicate} tekrar atlandı, ${r.pending} kayıt inceleme/eşleştirme bekliyor, ${r.stale} eski kayıt korundu.`,
    true,
  )
const retry = (id) =>
  act(`/events/${id}/retry`, 'POST', undefined, 'Eşleştirme sonucu güncellendi.', true)
onMounted(load)
</script>
