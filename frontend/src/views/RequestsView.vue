<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header">
        <div>
          <h1>Tedarikçi İşlemleri</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Tedarikçi hizmet talepleri oluşturun ve işlem süreçlerini yönetin.</p>
        </div>
        <button @click="openRequestModal" class="btn btn-accent">
          ⚙️ Yeni Hizmet Talebi
        </button>
      </header>

      <!-- Requests List -->
      <div class="glass-panel" style="margin-top: 30px; padding: 20px;">
        <h3 style="margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
          <span>📋 Talep Listesi ve Süreç Takibi</span>
        </h3>
        
        <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>
        
        <div v-else-if="requests.length === 0" class="empty-state">
          <p>Kayıtlı hizmet talebi bulunamadı.</p>
        </div>

        <div v-else class="custom-table-container">
          <table class="custom-table">
            <thead>
              <tr>
                <th>Talep ID</th>
                <th>Araç Plaka / Detay</th>
                <th>Hizmet Türü</th>
                <th>Tedarikçi</th>
                <th>Açıklama / Detay</th>
                <th>Oluşturma</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="req in requests" :key="req.id">
                <td>#{{ req.id }}</td>
                <td>
                  <strong style="color: #fff;">{{ req.vehicle_plate }}</strong>
                  <div style="font-size: 0.8rem; color: var(--text-muted);">{{ req.vehicle_brand_model }}</div>
                </td>
                <td>
                  <span class="badge" :class="getBadgeClass(req.type)">{{ req.type }}</span>
                </td>
                <td>{{ req.supplier_name }}</td>
                <td>
                  <div class="req-description-cell">
                    <span>{{ req.description }}</span>
                    <!-- Dynamic Details display -->
                    <div class="details-mini-box" v-if="req.details">
                      <span v-if="req.details.appointment_date">📅 Randevu: {{ req.details.appointment_date }}</span>
                      <span v-if="req.details.tire_type">🛞 Lastik: {{ req.details.tire_type }}</span>
                      <span v-if="req.details.location">📍 Konum: {{ req.details.location }}</span>
                      <span v-if="req.details.vehicle_class">🚗 Sınıf: {{ req.details.vehicle_class }}</span>
                    </div>
                  </div>
                </td>
                <td>{{ req.created_at }}</td>
                <td>
                  <span class="badge" :class="getStatusBadgeClass(req.status)">{{ req.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>

  <!-- Create Request Modal -->
  <div v-if="showRequestModal" class="modal-overlay">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 600px; padding: 30px;">
      <h2 class="gradient-brand" style="margin-bottom: 20px;">Tedarikçi Hizmet Talebi Oluştur</h2>

      <form @submit.prevent="createRequest">
        <!-- Vehicle Select -->
        <div class="form-group">
          <label class="form-label">Talep Yapılacak Araç</label>
          <select v-model="newRequestForm.vehicle_id" required class="form-select">
            <option value="" disabled>Araç seçiniz...</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.id">
              {{ v.plate }} - {{ v.brand }} {{ v.model }} (Mevcut Durum: {{ v.status }})
            </option>
          </select>
        </div>

        <!-- Service Type -->
        <div class="form-group">
          <label class="form-label">Hizmet Türü</label>
          <select v-model="newRequestForm.type" required class="form-select" @change="onTypeChange">
            <option value="servis">Yetkili Servis (Bakım/Onarım)</option>
            <option value="lastik">Lastik Hizmetleri (Değişim/Otel)</option>
            <option value="yol_yardim">7/24 Yol Yardım & Çekici</option>
            <option value="ikame_arac">İkame Araç Tedariği</option>
          </select>
        </div>

        <!-- Supplier Select (Filtered dynamically) -->
        <div class="form-group">
          <label class="form-label">Tedarikçi Seçimi</label>
          <select v-model="newRequestForm.supplier_id" required class="form-select">
            <option value="" disabled>Tedarikçi seçiniz...</option>
            <option v-for="s in filteredSuppliers" :key="s.id" :value="s.id">
              {{ s.name }} ({{ s.city }} / {{ s.district }}) — [{{ s.contract_type }}] — Hizmetler: {{ s.services?.join(', ') }}
            </option>
          </select>
        </div>

        <!-- DYNAMIC FIELDS BASED ON TYPE -->
        
        <!-- SERVICE FIELDS -->
        <div v-if="newRequestForm.type === 'servis'" class="dynamic-fields">
          <div class="form-group">
            <label class="form-label">Randevu Tarih ve Saati</label>
            <input type="datetime-local" v-model="newRequestForm.details.appointment_date" required class="form-input">
          </div>
        </div>

        <!-- TIRE FIELDS -->
        <div v-if="newRequestForm.type === 'lastik'" class="dynamic-fields">
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Lastik Tipi</label>
              <select v-model="newRequestForm.details.tire_type" class="form-select">
                <option value="Kış Lastiği">Kış Lastiği</option>
                <option value="Yaz Lastiği">Yaz Lastiği</option>
                <option value="Dört Mevsim">Dört Mevsim</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Randevu Zamanı</label>
              <input type="datetime-local" v-model="newRequestForm.details.appointment_date" required class="form-input">
            </div>
          </div>
        </div>

        <!-- ROADSIDE FIELDS -->
        <div v-if="newRequestForm.type === 'yol_yardim'" class="dynamic-fields">
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1.3fr 0.7fr;">
            <div class="form-group">
              <label class="form-label">Olay Mahalli / Konum Tarifi</label>
              <input type="text" v-model="newRequestForm.details.location" required class="form-input" placeholder="Örn: Maslak İTÜ Çıkışı Tem Bağlantı Yolu">
            </div>
            <div class="form-group">
              <label class="form-label">Arıza Derecesi</label>
              <select v-model="newRequestForm.details.issue_severity" class="form-select">
                <option value="Düşük">Düşük (Yürür Durumda)</option>
                <option value="Orta">Orta (Sürüş Riskli)</option>
                <option value="Yüksek">Yüksek (Çekici Gerekli)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- REPLACEMENT VEHICLE FIELDS -->
        <div v-if="newRequestForm.type === 'ikame_arac'" class="dynamic-fields">
          <div class="grid-3" style="gap: 10px; grid-template-columns: 1fr 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Araç Grubu</label>
              <select v-model="newRequestForm.details.vehicle_class" class="form-select">
                <option value="Ekonomik">Ekonomik (Clio, Egea vb.)</option>
                <option value="Konfor">Konfor (Megane, Focus vb.)</option>
                <option value="Premium">Premium (3 Serisi, C Serisi vb.)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Başlangıç Tarihi</label>
              <input type="date" v-model="newRequestForm.details.start_date" required class="form-input">
            </div>
            <div class="form-group">
              <label class="form-label">Bitiş Tarihi</label>
              <input type="date" v-model="newRequestForm.details.end_date" required class="form-input">
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Talep Açıklaması / Notlar</label>
          <textarea v-model="newRequestForm.description" required class="form-textarea" rows="3" placeholder="Tedarikçiye iletilecek notlar..."></textarea>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end;">
          <button type="button" @click="showRequestModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-accent" :disabled="saving">
            {{ saving ? 'Gönderiliyor...' : 'Talebi Oluştur' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const requests = ref([])
const vehicles = ref([])
const suppliers = ref([])
const loading = ref(true)
const saving = ref(false)
const showRequestModal = ref(false)

const isCustomer = computed(() => localStorage.getItem('fleetcar_token') === 'logged_in')

const newRequestForm = reactive({
  vehicle_id: '',
  supplier_id: '',
  type: 'servis',
  description: '',
  details: {}
})

const fetchRequests = async () => {
  try {
    const response = await fetch('/api/requests')
    if (response.ok) {
      requests.value = await response.json()
      // Show newest first
      requests.value.reverse()
    }
  } catch (error) {
    console.error('Error fetching requests:', error)
  }
}

const fetchVehiclesAndSuppliers = async () => {
  try {
    const [vehRes, supRes] = await Promise.all([
      fetch('/api/vehicles'),
      fetch('/api/suppliers')
    ])
    if (vehRes.ok && supRes.ok) {
      vehicles.value = await vehRes.json()
      suppliers.value = await supRes.json()
    }
  } catch (error) {
    console.error('Error fetching supplementary data:', error)
  } finally {
    loading.value = false
  }
}

const filteredSuppliers = computed(() => {
  return suppliers.value.filter(s => s.type === newRequestForm.type)
})

const onTypeChange = () => {
  newRequestForm.supplier_id = ''
  newRequestForm.details = {}
  
  // Set defaults for details based on type
  if (newRequestForm.type === 'lastik') {
    newRequestForm.details = { tire_type: 'Kış Lastiği', appointment_date: '' }
  } else if (newRequestForm.type === 'yol_yardim') {
    newRequestForm.details = { location: '', issue_severity: 'Orta' }
  } else if (newRequestForm.type === 'ikame_arac') {
    newRequestForm.details = { vehicle_class: 'Ekonomik', start_date: '', end_date: '' }
  } else if (newRequestForm.type === 'servis') {
    newRequestForm.details = { appointment_date: '' }
  }
}

const openRequestModal = () => {
  // Pre-fill type defaults
  onTypeChange()
  showRequestModal.value = true
}

const createRequest = async () => {
  saving.value = true
  try {
    const response = await fetch('/api/requests', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newRequestForm)
    })
    
    if (response.ok) {
      // Reload requests & vehicles
      await Promise.all([fetchRequests(), fetchVehiclesAndSuppliers()])
      showRequestModal.value = false
      // Reset form
      newRequestForm.vehicle_id = ''
      newRequestForm.supplier_id = ''
      newRequestForm.type = 'servis'
      newRequestForm.description = ''
      newRequestForm.details = {}
    }
  } catch (error) {
    console.error('Error creating request:', error)
  } finally {
    saving.value = false
  }
}

const updateStatus = async (requestId, statusValue) => {
  try {
    const response = await fetch(`/api/requests/${requestId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status: statusValue })
    })
    
    if (response.ok) {
      // Reload requests & vehicles to show correct updated status
      await Promise.all([fetchRequests(), fetchVehiclesAndSuppliers()])
    }
  } catch (error) {
    console.error('Error updating status:', error)
  }
}

const getBadgeClass = (type) => {
  return {
    'badge-service': type === 'servis',
    'badge-tire': type === 'lastik',
    'badge-roadside': type === 'yol_yardim',
    'badge-replacement': type === 'ikame_arac'
  }
}

const getStatusBadgeClass = (status) => {
  return {
    'badge-active': status === 'Tamamlandı',
    'badge-service': status === 'İşlemde',
    'badge-tire': status === 'Onaylandı',
    'badge-roadside': status === 'İptal Edildi',
    'badge-pending': status === 'Beklemede'
  }
}

onMounted(() => {
  Promise.all([fetchRequests(), fetchVehiclesAndSuppliers()])
})
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}

.req-description-cell {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.details-mini-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.75rem;
  color: var(--secondary);
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 4px;
}

.status-select-mini {
  padding: 4px 8px;
  font-size: 0.8rem;
  width: 120px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.status-select-mini:focus {
  box-shadow: none;
  border-color: var(--secondary);
}

.empty-state {
  padding: 50px 0;
  text-align: center;
  color: var(--text-muted);
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}

.modal-content {
  width: 100%;
}

.dynamic-fields {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}
</style>
