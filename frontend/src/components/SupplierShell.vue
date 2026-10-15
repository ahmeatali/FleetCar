<template>
  <section class="sw-card sw-settings">
    <h2>Shell Taşıt Tanıma Bağlantısı</h2>
    <p class="sw-muted">
      Gün sonu onaylı yakıt alımları araçların yakıt giderlerine eklenir. Aynı Shell kaydı tekrar
      gider oluşturmaz.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>
    <UiAlert v-if="notice" as="p" tone="info">{{ notice }}</UiAlert>
    <p v-if="!state && !error" class="sw-muted">Bağlantı bilgileri yükleniyor…</p>
    <UiButton v-if="!state && error" class="sw-button" @click="load">Tekrar Dene</UiButton>
    <template v-if="state">
      <p>
        <strong>{{
          state.credentials_configured
            ? 'Sunucu erişim bilgileri tanımlı'
            : 'Sunucu erişim bilgileri bekleniyor'
        }}</strong>
        · {{ state.mappings.length }} plaka eşlendi
      </p>
      <p class="sw-muted">
        Shell müşteri kodu, kullanıcı adı ve şifresi sunucu ortamında tanımlanır. Üçüncü taraf
        hesaplarda alt müşteri kodu zorunludur.
      </p>
      <form v-if="role === 'owner'" @submit.prevent="saveConfig">
        <UiField
          >Alt Müşteri Kodu (Branch Code)<input
            v-model="config.branch_code"
            maxlength="10"
            placeholder="Hesabınıza göre boş bırakılabilir"
        /></UiField>
        <UiButton class="sw-button" :disabled="busy">Bağlantı Ayarlarını Kaydet</UiButton>
      </form>
      <h3>Araç Eşleştirmeleri</h3>
      <p class="sw-muted">
        Shell’deki plakayı kalıcı filo aracıyla eşleyin. Geçmişi korumak için kaydedilen eşleme
        başka araca taşınamaz.
      </p>
      <form v-if="role === 'owner'" @submit.prevent="saveMapping">
        <UiField
          >Shell Plakası<input
            v-model="mapping.external_id"
            required
            maxlength="20"
            placeholder="34 ABC 123"
        /></UiField>
        <UiField
          >Araç<select v-model="mapping.vehicle_id" aria-label="Shell Aracı" required>
            <option value="">Araç seçin</option>
            <option v-for="car in vehicles" :key="car.id" :value="car.id">
              {{ car.plate }} · {{ car.brand }} {{ car.model }}
            </option>
          </select></UiField
        >
        <UiButton class="sw-button" :disabled="busy">Plakayı Eşle</UiButton>
      </form>
      <UiTable class="sw-table-scroll"
        ><table class="sw-table">
          <thead>
            <tr>
              <th>Shell Plakası</th>
              <th>Filo Aracı</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in state.mappings" :key="row.external_id">
              <td>{{ row.external_id }}</td>
              <td>{{ plate(row.vehicle_id) }}</td>
            </tr>
            <tr v-if="!state.mappings.length">
              <td colspan="2">Henüz plaka eşlenmedi.</td>
            </tr>
          </tbody>
        </table></UiTable
      >
      <h3>Yakıt Alımlarını Aktar</h3>
      <p class="sw-muted">
        Son 15 ay içinden en fazla 31 günlük aralık seçin. Bir önceki günün verileri Shell
        tarafından saat 08.30’dan itibaren sunulur.
      </p>
      <form v-if="role === 'owner'" @submit.prevent="sync">
        <UiField
          >Başlangıç Tarihi<input v-model="query.start_date" type="date" :max="yesterday" required
        /></UiField>
        <UiField
          >Bitiş Tarihi<input
            v-model="query.end_date"
            type="date"
            :min="query.start_date"
            :max="yesterday"
            required
        /></UiField>
        <UiButton
          class="sw-button primary"
          :disabled="busy || !state.credentials_configured || !state.config"
          >{{ busy ? 'İşleniyor…' : 'Shell Yakıt Alımlarını Getir' }}</UiButton
        >
      </form>
      <h3>Yakıt Aktarım Geçmişi</h3>
      <UiTable class="sw-table-scroll"
        ><table class="sw-table">
          <thead>
            <tr>
              <th>RID / Plaka</th>
              <th>Tarih / İstasyon</th>
              <th>Litre / Tutar</th>
              <th>Durum</th>
              <th>İşlem</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in state.events" :key="row.id">
              <td>{{ row.rid }}<br />{{ row.plate }}</td>
              <td>
                {{ new Date(row.occurred_at).toLocaleString('tr-TR') }}<br />{{ row.station }}
              </td>
              <td>
                {{ row.liters.toLocaleString('tr-TR') }} L<br />{{
                  row.amount.toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })
                }}
              </td>
              <td>
                {{ row.status }}<small>{{ row.reason }}</small>
              </td>
              <td>
                <UiButton
                  v-if="role === 'owner' && row.status !== 'İşlendi'"
                  class="sw-button"
                  :disabled="busy"
                  @click="retry(row.id)"
                  >Tekrar İşle</UiButton
                >
              </td>
            </tr>
            <tr v-if="!state.events.length">
              <td colspan="5">Henüz Shell verisi alınmadı.</td>
            </tr>
          </tbody>
        </table></UiTable
      >
    </template>
  </section>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UiAlert, UiButton, UiField, UiTable } from './ui/index.js'
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
const config = reactive({ branch_code: '' })
const mapping = reactive({ external_id: '', vehicle_id: '' })
// Calendar dates follow the Shell service's Istanbul day boundary.
const localDate = (d) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(d)
const yesterday = localDate(new Date(Date.now() - 86400000))
const query = reactive({ start_date: yesterday, end_date: yesterday })
const plate = (id) => props.vehicles.find((v) => v.id === id)?.plate || 'Eşlenmemiş'
async function load() {
  error.value = ''
  try {
    state.value = await supplierApi('/integrations/shell')
    if (state.value.config) Object.assign(config, state.value.config)
  } catch (e) {
    error.value = e.message
  }
}
async function act(path, method, body, message, refresh = false) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const result = await supplierApi('/integrations/shell' + path, { method, body })
    await load()
    notice.value = typeof message === 'function' ? message(result) : message
    if (refresh) emit('updated')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
const saveConfig = () => act('/config', 'PUT', { ...config }, 'Shell bağlantı ayarları kaydedildi.')
const saveMapping = () => act('/mappings', 'PUT', { ...mapping }, 'Shell plakası araca bağlandı.')
const sync = () =>
  act(
    '/sync',
    'POST',
    { ...query },
    (r) =>
      `${r.processed} yakıt gideri aktarıldı, ${r.duplicate} tekrar atlandı, ${r.pending} kayıt eşleştirme veya inceleme bekliyor.`,
    true,
  )
const retry = (id) =>
  act(`/events/${id}/retry`, 'POST', undefined, 'Shell kaydı yeniden değerlendirildi.', true)
onMounted(load)
</script>
