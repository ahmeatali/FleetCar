<template>
  <div class="portal-layout">
    <Sidebar />
    <main class="portal-main savings-page" :aria-busy="loading">
      <header class="savings-heading">
        <div>
          <h1>Filo Kontrol & Tasarruf Merkezi</h1>
          <p>Filonuzdaki kullanım, bakım ve gider kayıtlarından inceleme önerileri.</p>
        </div>
        <UiButton
          class="btn btn-blue"
          :disabled="loading || !!error || !findings.length"
          @click="exportFindings"
          >CSV İndir</UiButton
        >
      </header>
      <UiAlert v-if="loading" tone="info">Filo verileriniz yükleniyor…</UiAlert>
      <UiAlert v-else-if="error" tone="error">
        {{ error }} <UiButton class="btn" @click="load">Tekrar Dene</UiButton>
      </UiAlert>
      <template v-else>
        <section class="savings-filters glass-panel" aria-label="İnceleme eşikleri">
          <UiField
            >Araç<select v-model="vehicleId" class="form-input">
              <option value="">Tüm araçlar</option>
              <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">
                {{ vehicle.plate }}
              </option>
            </select></UiField
          >
          <UiField
            >Düşük kullanım (km/ay)<input
              v-model.number="thresholds.low_usage_km"
              class="form-input"
              type="number"
              min="0"
          /></UiField>
          <UiField
            >Düşük HGS bakiyesi (TL)<input
              v-model.number="thresholds.low_balance"
              class="form-input"
              type="number"
              min="0"
          /></UiField>
          <UiField
            >Yakıt inceleme eşiği (L/100 km)<input
              v-model.number="thresholds.fuel_l100_threshold"
              class="form-input"
              type="number"
              min="0.1"
              step="0.1"
          /></UiField>
        </section>
        <section class="savings-metrics" aria-label="İnceleme özeti">
          <article v-for="metric in metrics" :key="metric.label" class="glass-panel">
            <span>{{ metric.label }}</span
            ><strong>{{ metric.count }}</strong>
          </article>
        </section>
        <section class="glass-panel savings-results">
          <h2>Tespitler ve Öneriler</h2>
          <p class="savings-note">
            Bu tespitler inceleme önerisidir. İncelenecek tutarlar gerçekleşmiş tasarruf değildir.
            Yakıt hesapları kayıtlar arasındaki yaklaşık tüketimi gösterir; dolum kapsamını
            doğrulayın. Eşikler yalnızca bu ekrandaki analizi değiştirir.
          </p>
          <UiTable
            ><table class="data-table">
              <thead>
                <tr>
                  <th>Kategori</th>
                  <th>Tespit</th>
                  <th>Kanıt</th>
                  <th>İncelenecek Tutar</th>
                  <th>Aksiyon</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="finding in findings" :key="finding.id">
                  <td>{{ finding.category }}</td>
                  <td>{{ finding.title }}</td>
                  <td>{{ finding.evidence }}</td>
                  <td>{{ finding.amount ? money(finding.amount) : '—' }}</td>
                  <td>
                    <router-link
                      :to="`/dashboard/vehicles/${encodeURIComponent(finding.vehicle_id)}`"
                      class="btn"
                      >Araç Detayı</router-link
                    >
                  </td>
                </tr>
                <tr v-if="!findings.length">
                  <td colspan="5">
                    {{
                      vehicles.length
                        ? 'Kayıtlı verilerde bu eşikleri aşan tespit bulunamadı.'
                        : 'Henüz filonuza atanmış araç bulunmuyor.'
                    }}
                  </td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
      </template>
    </main>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import { UiAlert, UiButton, UiField, UiTable } from '../components/ui/index.js'
import { apiRequest } from '../api/http.js'
import { detectCustomerFindings } from '../utils/customerFindings.js'
import { downloadCsv } from '../utils/downloads.js'

const vehicles = ref([]),
  expenses = ref([]),
  vehicleId = ref(''),
  loading = ref(true),
  error = ref('')
const thresholds = reactive({ low_usage_km: 500, low_balance: 200, fuel_l100_threshold: 12 })
const findings = computed(() =>
  detectCustomerFindings(
    vehicles.value.filter((vehicle) => !vehicleId.value || vehicle.id === vehicleId.value),
    expenses.value,
    thresholds,
  ),
)
const metrics = computed(() => [
  { label: 'İnceleme Tespiti', count: findings.value.length },
  ...['KM', 'Kullanım', 'Servis', 'Yakıt', 'HGS', 'Fatura'].map((category) => ({
    label: category,
    count: findings.value.filter((finding) => finding.category === category).length,
  })),
])
const money = (amount) =>
  new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(amount)
async function load() {
  loading.value = true
  error.value = ''
  vehicles.value = []
  expenses.value = []
  try {
    const [cars, records] = await Promise.all([
      apiRequest('/api/vehicles', { account: 'customer' }),
      apiRequest('/api/vehicle-expenses', { account: 'customer' }),
    ])
    vehicles.value = cars
    expenses.value = records
  } catch (failure) {
    error.value = failure.message || 'Filo verileri alınamadı.'
  } finally {
    loading.value = false
  }
}
function exportFindings() {
  downloadCsv(
    [
      ['Kategori', 'Tespit', 'Kanıt', 'İncelenecek Tutar'],
      ...findings.value.map((finding) => [
        finding.category,
        finding.title,
        finding.evidence,
        finding.amount || '',
      ]),
    ],
    'fleetrent-filo-tespitleri.csv',
  )
}
onMounted(load)
</script>
<style scoped>
.savings-page {
  min-width: 0;
}
.savings-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.savings-heading h1 {
  margin: 0 0 8px;
  font-size: 26px;
}
.savings-heading p,
.savings-note {
  color: #64748b;
  line-height: 1.6;
}
.savings-filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  padding: 20px;
  margin-bottom: 20px;
}
.savings-filters :deep(label) {
  display: grid;
  gap: 8px;
  font-size: 13px;
}
.savings-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.savings-metrics article {
  padding: 18px;
  display: grid;
  gap: 12px;
}
.savings-metrics strong {
  font-size: 28px;
  color: #1655ad;
}
.savings-results {
  padding: 24px;
}
.data-table {
  min-width: 760px;
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.data-table th,
.data-table td {
  padding: 14px;
  border-bottom: 1px solid #e2e8f0;
}
.data-table th {
  background: #f8fafc;
}
.data-table .btn {
  white-space: nowrap;
}
@media (max-width: 1100px) {
  .savings-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 600px) {
  .savings-heading {
    align-items: stretch;
    flex-direction: column;
  }
  .savings-filters {
    grid-template-columns: 1fr;
  }
  .savings-results {
    padding: 14px;
  }
}
</style>
