<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Breadcrumb -->
      <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <router-link to="/dashboard" style="color: #64748b; text-decoration: none;">← Geri</router-link>
        <span>/ Ayarlar / {{ activeTabTitle }}</span>
      </div>

      <!-- Header -->
      <header class="dashboard-header" style="margin-bottom: 25px;">
        <div>
          <h1>Sistem ve Şirket Ayarları</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Kullanıcı hesapları, araç teslim formları, bayi sözleşmeleri ve şirket evrakları.</p>
        </div>
        <button v-if="activeTab === 'kullanicilar'" @click="showAddUserModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>👤</span> Yeni Kullanıcı Ekle
        </button>
        <button v-if="activeTab === 'teslim_formlari'" @click="showAddFormModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>📋</span> Yeni Teslim Formu
        </button>
        <button v-if="activeTab === 'sirket_evraklari'" @click="showUploadDocModal = true" class="btn btn-blue" style="padding: 10px 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>📤</span> Evrak Yükle
        </button>
      </header>

      <!-- 4-Tab Navigation Bar (Matching Screenshot Dropdown Options) -->
      <div class="category-tabs-bar">
        <button @click="activeTab = 'kullanicilar'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'kullanicilar' }">
          <span>👥</span> Kullanıcılar
        </button>
        <button @click="activeTab = 'teslim_formlari'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'teslim_formlari' }">
          <span>📋</span> Teslim Formları
        </button>
        <button @click="activeTab = 'bayi_sozlesmesi'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'bayi_sozlesmesi' }">
          <span>📜</span> Bayi Sözleşmesi
        </button>
        <button @click="activeTab = 'sirket_evraklari'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'sirket_evraklari' }">
          <span>🏢</span> Şirket Evraklarım
        </button>
      </div>

      <!-- ============================================================== -->
      <!-- 1. KULLANICILAR (Kullanıcı Listesi ve Kullanıcı Ekleme)       -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'kullanicilar'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a;">Sistem Kullanıcıları</h2>
            <div style="width: 280px;">
              <input type="text" v-model="userSearch" class="form-input" placeholder="Ad, e-posta veya rol ara...">
            </div>
          </div>

          <!-- User Table -->
          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Kullanıcı Adı / E-Posta</th>
                  <th>Telefon</th>
                  <th>Kullanıcı Rolü</th>
                  <th>Tahsis Edilen Araç</th>
                  <th>Kayıt Tarihi</th>
                  <th>Durum</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <td>#{{ user.id }}</td>
                  <td>
                    <strong style="color: #0f172a; font-size: 0.95rem;">{{ user.name }}</strong>
                    <div style="font-size: 0.8rem; color: #64748b;">{{ user.email }}</div>
                  </td>
                  <td>{{ user.phone }}</td>
                  <td>
                    <span class="badge" :class="getRoleBadgeClass(user.role)">{{ user.role }}</span>
                  </td>
                  <td>
                    <span v-if="user.assigned_plate" style="font-family: monospace; font-weight: 700; color: #2563eb; background: #eff6ff; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe;">
                      {{ user.assigned_plate }}
                    </span>
                    <span v-else style="color: #94a3b8; font-size: 0.85rem;">— Tahsis Yok</span>
                  </td>
                  <td>{{ user.created_at }}</td>
                  <td>
                    <span style="font-size: 0.8rem; font-weight: 700; padding: 4px 10px; border-radius: 20px;"
                      :style="{ background: user.is_active ? '#dcfce7' : '#fef2f2', color: user.is_active ? '#16a34a' : '#dc2626' }">
                      {{ user.is_active ? '🟢 Aktif' : '🔴 Pasif' }}
                    </span>
                  </td>
                  <td>
                    <div style="display: flex; gap: 8px;">
                      <button @click="editUser(user)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem;">
                        Düzenle
                      </button>
                      <button @click="toggleUserStatus(user)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem;" :style="{ color: user.is_active ? '#dc2626' : '#16a34a' }">
                        {{ user.is_active ? 'Pasife Al' : 'Aktif Et' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Stat Cards -->
        <div class="grid-3" style="gap: 20px;">
          <div class="glass-panel text-center" style="padding: 20px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563eb;">{{ users.length }} Kullanıcı</div>
            <div style="font-size: 0.85rem; color: #1d4ed8; margin-top: 4px;">Toplam Kayıtlı Kullanıcı</div>
          </div>
          <div class="glass-panel text-center" style="padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #16a34a;">{{ activeUsersCount }} Aktif</div>
            <div style="font-size: 0.85rem; color: #15803d; margin-top: 4px;">Sistemi Kullanan Yetkililer</div>
          </div>
          <div class="glass-panel text-center" style="padding: 20px; background: #fefce8; border: 1px solid #fef08a; border-radius: 16px;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #d97706;">{{ driverUsersCount }} Sürücü</div>
            <div style="font-size: 0.85rem; color: #b45309; margin-top: 4px;">Araç Zimmetli Sürücüler</div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 2. TESLİM FORMLARI                                             -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'teslim_formlari'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Teslim & Tesellüm Formları</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Form No</th>
                  <th>Plaka</th>
                  <th>Teslim Alan Kullanıcı</th>
                  <th>Teslim Eden Yetkili</th>
                  <th>Teslim Tarihi</th>
                  <th>Başlangıç KM</th>
                  <th>Araç Hasar / Not</th>
                  <th>Doküman</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="form in deliveryForms" :key="form.id">
                  <td><strong style="color: #2563eb;">#TF-{{ form.id }}</strong></td>
                  <td><strong style="color: #0f172a;">{{ form.plate }}</strong></td>
                  <td>{{ form.receiver }}</td>
                  <td>{{ form.issuer }}</td>
                  <td>{{ form.date }}</td>
                  <td>{{ form.km.toLocaleString() }} km</td>
                  <td><span style="font-size: 0.85rem; color: #64748b;">{{ form.notes }}</span></td>
                  <td>
                    <button @click="downloadForm(form)" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.78rem; color: #2563eb;">
                      📄 İmzalı Form (PDF)
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 3. BAYİ SÖZLEŞMESİ                                              -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'bayi_sozlesmesi'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Aktif Bayi ve Tedarikçi Sözleşmeleri</h2>

          <div class="grid-2" style="gap: 20px;">
            <div class="glass-panel" style="padding: 20px; background: #fafafa; border: 1px solid #e2e8f0; border-radius: 14px;" v-for="contract in contracts" :key="contract.id">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                  <h3 style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">{{ contract.name }}</h3>
                  <div style="font-size: 0.85rem; color: #64748b;">Sözleşme No: <strong>#BS-{{ contract.code }}</strong></div>
                </div>
                <span class="badge badge-active">Yürürlükte</span>
              </div>

              <div style="font-size: 0.88rem; color: #475569; margin-bottom: 15px; line-height: 1.6;">
                <div><strong>Başlangıç Tarihi:</strong> {{ contract.start_date }}</div>
                <div><strong>Bitiş Tarihi:</strong> {{ contract.end_date }}</div>
                <div><strong>Komisyon / Hizmet Oranı:</strong> {{ contract.commission }}</div>
              </div>

              <button @click="downloadContract(contract)" class="btn btn-secondary" style="width: 100%; font-size: 0.85rem; font-weight: 600; color: #2563eb;">
                📄 İmzalı Bayi Sözleşmesini İndir (PDF)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 4. ŞİRKET EVRAKLARIM                                            -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'sirket_evraklari'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Kurumsal Şirket Evrakları & Belgeler</h2>

          <div class="grid-2" style="gap: 20px;">
            <div class="glass-panel" style="padding: 20px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;" v-for="doc in companyDocs" :key="doc.id">
              <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 14px;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: #eff6ff; color: #2563eb; font-size: 1.4rem; display: flex; align-items: center; justify-content: center;">
                  📄
                </div>
                <div>
                  <h4 style="font-size: 1rem; font-weight: 800; color: #0f172a;">{{ doc.title }}</h4>
                  <div style="font-size: 0.8rem; color: #64748b;">Son Güncelleme: {{ doc.updated_at }}</div>
                </div>
                <span class="badge badge-active" style="margin-left: auto;">{{ doc.status }}</span>
              </div>

              <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button @click="viewDoc(doc)" class="btn btn-secondary" style="flex: 1; font-size: 0.82rem;">
                  👁️ Görüntüle
                </button>
                <button @click="downloadDoc(doc)" class="btn btn-blue" style="flex: 1; font-size: 0.82rem;">
                  ⬇️ İndir
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 👤 NEW USER MODAL (KULLANICI EKLEME EKRANI) -->
  <div v-if="showAddUserModal" class="modal-overlay" @click.self="showAddUserModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 540px; padding: 32px; background: #ffffff;">
      <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">Yeni Kullanıcı Ekle</h2>
      <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 24px;">
        Sisteme erişecek yeni yönetici, sürücü veya operasyon personelini tanımlayın.
      </p>

      <form @submit.prevent="addUser">
        <div class="form-group">
          <label class="form-label">Ad Soyad *</label>
          <input type="text" v-model="userForm.name" required class="form-input" placeholder="Örn: Caner Erkin">
        </div>

        <div class="grid-2" style="gap: 16px;">
          <div class="form-group">
            <label class="form-label">E-Posta Adresi *</label>
            <input type="email" v-model="userForm.email" required class="form-input" placeholder="isim@sirket.com">
          </div>

          <div class="form-group">
            <label class="form-label">Telefon Numarası *</label>
            <input type="tel" v-model="userForm.phone" required class="form-input" placeholder="0532 000 00 00">
          </div>
        </div>

        <div class="grid-2" style="gap: 16px;">
          <div class="form-group">
            <label class="form-label">Kullanıcı Rolü *</label>
            <select v-model="userForm.role" required class="form-select">
              <option value="Sürücü">Sürücü</option>
              <option value="Filo Yöneticisi">Filo Yöneticisi</option>
              <option value="Finans Sorumlusu">Finans Sorumlusu</option>
              <option value="Operasyon Personeli">Operasyon Personeli</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Tahsis Edilecek Araç</label>
            <select v-model="userForm.assigned_plate" class="form-select">
              <option value="">Yok / Serbest</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.plate">
                {{ v.plate }} ({{ v.brand }} {{ v.model }})
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Giriş Şifresi *</label>
          <input type="password" v-model="userForm.password" required class="form-input" placeholder="••••••••">
          <span style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Kullanıcı ilk girişte şifresini değiştirebilir</span>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 25px;">
          <button type="button" @click="showAddUserModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue" style="padding: 12px 24px;">Kullanıcıyı Kaydet</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 📋 NEW HANDOVER FORM MODAL -->
  <div v-if="showAddFormModal" class="modal-overlay" @click.self="showAddFormModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 500px; padding: 30px; background: #ffffff;">
      <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Yeni Araç Teslim Formu</h2>
      <form @submit.prevent="addHandoverForm">
        <div class="form-group">
          <label class="form-label">Teslim Edilecek Araç Plakası</label>
          <select v-model="formHandover.plate" required class="form-select">
            <option value="" disabled>Araç seçiniz...</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.plate">
              {{ v.plate }} ({{ v.brand }} {{ v.model }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Teslim Alan Kullanıcı</label>
          <input type="text" v-model="formHandover.receiver" required class="form-input" placeholder="Ad Soyad">
        </div>
        <div class="form-group">
          <label class="form-label">Teslim Tarihi</label>
          <input type="date" v-model="formHandover.date" required class="form-input">
        </div>
        <div class="form-group">
          <label class="form-label">Mevcut Kilometre</label>
          <input type="number" v-model.number="formHandover.km" required class="form-input" placeholder="45230">
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px;">
          <button type="button" @click="showAddFormModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue">Formu Oluştur</button>
        </div>
      </form>
    </div>
  </div>

  <!-- 📤 UPLOAD DOCUMENT MODAL -->
  <div v-if="showUploadDocModal" class="modal-overlay" @click.self="showUploadDocModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 500px; padding: 30px; background: #ffffff;">
      <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Şirket Evrakı Yükle</h2>
      <form @submit.prevent="uploadDocument">
        <div class="form-group">
          <label class="form-label">Evrak Başlığı</label>
          <input type="text" v-model="newDocTitle" required class="form-input" placeholder="Örn: 2026 Vergi Levhası">
        </div>
        <div class="form-group">
          <div class="upload-dropzone">
            <div style="font-size: 2rem;">📁</div>
            <div style="font-weight: 600; color: #0f172a; margin-top: 6px;">Dosya Seçin veya Sürükleyin</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">PDF, PNG, JPG (Maks. 10MB)</div>
          </div>
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px;">
          <button type="button" @click="showUploadDocModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-blue">Yükle ve Kaydet</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const activeTab = ref('kullanicilar')
const userSearch = ref('')
const showAddUserModal = ref(false)
const showAddFormModal = ref(false)
const showUploadDocModal = ref(false)
const newDocTitle = ref('')

const activeTabTitle = computed(() => {
  switch (activeTab.value) {
    case 'kullanicilar': return 'Kullanıcılar'
    case 'teslim_formlari': return 'Teslim Formları'
    case 'bayi_sozlesmesi': return 'Bayi Sözleşmesi'
    case 'sirket_evraklari': return 'Şirket Evraklarım'
    default: return 'Ayarlar'
  }
})

// Vehicles state for plate selects
const vehicles = ref([])

const fetchVehicles = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  const url = customerId ? `/api/vehicles?customer_id=${customerId}` : '/api/vehicles'
  try {
    const res = await fetch(url)
    if (res.ok) {
      vehicles.value = await res.json()
    }
  } catch (err) {
    console.error('Error fetching vehicles for settings:', err)
  }
}

// Users List Data
const storedUsersStr = localStorage.getItem('fleet_customer_users')
const defaultUser = {
  id: 1,
  name: localStorage.getItem('fleetcar_customer_name') || 'Filo Yöneticisi',
  email: localStorage.getItem('fleetcar_user_email') || 'yonetici@sirket.com',
  phone: '-',
  role: 'Filo Yöneticisi',
  assigned_plate: '',
  created_at: new Date().toLocaleDateString('tr-TR'),
  is_active: true
}

const users = ref(storedUsersStr ? JSON.parse(storedUsersStr) : [defaultUser])

const saveUsers = () => {
  localStorage.setItem('fleet_customer_users', JSON.stringify(users.value))
}

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  const q = userSearch.value.toLowerCase()
  return users.value.filter(u => 
    u.name.toLowerCase().includes(q) || 
    u.email.toLowerCase().includes(q) || 
    u.role.toLowerCase().includes(q)
  )
})

const activeUsersCount = computed(() => users.value.filter(u => u.is_active).length)
const driverUsersCount = computed(() => users.value.filter(u => u.role === 'Sürücü').length)

const userForm = reactive({
  name: '',
  email: '',
  phone: '',
  role: 'Sürücü',
  assigned_plate: '',
  password: '123456'
})

const addUser = () => {
  users.value.unshift({
    id: Date.now(),
    name: userForm.name,
    email: userForm.email,
    phone: userForm.phone,
    role: userForm.role,
    assigned_plate: userForm.assigned_plate,
    created_at: new Date().toLocaleDateString('tr-TR'),
    is_active: true
  })
  saveUsers()
  alert(`Yeni kullanıcı "${userForm.name}" başarıyla eklendi!`)
  showAddUserModal.value = false
  userForm.name = ''
  userForm.email = ''
  userForm.phone = ''
  userForm.assigned_plate = ''
}

const toggleUserStatus = (user) => {
  user.is_active = !user.is_active
  saveUsers()
}

const editUser = (user) => {
  alert(`"${user.name}" kullanıcısını düzenleme ekranı açılıyor...`)
}

// Delivery / Handover Forms
const storedFormsStr = localStorage.getItem('fleet_customer_delivery_forms')
const deliveryForms = ref(storedFormsStr ? JSON.parse(storedFormsStr) : [])

const saveForms = () => {
  localStorage.setItem('fleet_customer_delivery_forms', JSON.stringify(deliveryForms.value))
}

const formHandover = reactive({
  plate: '',
  receiver: '',
  date: new Date().toISOString().slice(0, 10),
  km: 0
})

const addHandoverForm = () => {
  deliveryForms.value.unshift({
    id: Date.now(),
    plate: formHandover.plate,
    receiver: formHandover.receiver,
    issuer: localStorage.getItem('fleetcar_customer_name') || 'Filo Yönetimi',
    date: formHandover.date,
    km: formHandover.km,
    notes: 'Yeni teslim alma formu kaydı.'
  })
  saveForms()
  showAddFormModal.value = false
  alert(`${formHandover.plate} plaka için araç teslim formu kaydedildi!`)
}

onMounted(() => {
  fetchVehicles()
})


const downloadForm = (form) => {
  alert(`#TF-${form.id} numaralı Teslim Formu PDF olarak indiriliyor...`)
}

// Contracts Data
const contracts = ref([
  { id: 1, name: 'Otokoç Otomotiv Bayi Hizmet Sözleşmesi', code: '2025-OKC-01', start_date: '01.01.2025', end_date: '31.12.2026', commission: '%4.5 Bayi İskontosu' },
  { id: 2, name: 'VDF Filo Tedarik ve İhale Çerçeve Sözleşmesi', code: '2025-VDF-09', start_date: '15.02.2025', end_date: '15.02.2027', commission: 'Sabit Hizmet Tarifesi' }
])

const downloadContract = (c) => {
  alert(`"${c.name}" sözleşme metni indiriliyor...`)
}

// Company Docs Data
const companyDocs = ref([
  { id: 1, title: '2025 Vergi Levhası', updated_at: '10.01.2025', status: 'Onaylandı' },
  { id: 2, title: 'İmza Sirküleri', updated_at: '15.01.2025', status: 'Onaylandı' },
  { id: 3, title: 'Ticaret Sicil Gazetesi', updated_at: '05.02.2025', status: 'Onaylandı' },
  { id: 4, title: 'Oda Kayıt & Faaliyet Belgesi', updated_at: '20.02.2025', status: 'Onaylandı' }
])

const uploadDocument = () => {
  if (newDocTitle.value) {
    companyDocs.value.unshift({
      id: companyDocs.value.length + 1,
      title: newDocTitle.value,
      updated_at: new Date().toLocaleDateString('tr-TR'),
      status: 'Onaylandı'
    })
    showUploadDocModal.value = false
    newDocTitle.value = ''
    alert('Evrak başarıyla yüklendi!')
  }
}

const viewDoc = (d) => alert(`"${d.title}" evrakı önizleniyor...`)
const downloadDoc = (d) => alert(`"${d.title}" evrakı indiriliyor...`)

const getRoleBadgeClass = (role) => {
  switch (role) {
    case 'Filo Yöneticisi': return 'badge-service'
    case 'Finans Sorumlusu': return 'badge-tire'
    case 'Operasyon Personeli': return 'badge-replacement'
    default: return 'badge-active'
  }
}
</script>
