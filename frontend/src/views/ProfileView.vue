<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header">
        <div>
          <h1>Şirket Profili</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Şirketinizin kurumsal kimlik, tescil ve yetkili kullanıcı bilgilerini görüntüleyin.</p>
        </div>
      </header>

      <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>

      <div v-else class="grid-2" style="margin-top: 30px; gap: 30px;">
        <!-- Left Side: Kurumsal Kimlik -->
        <div class="glass-panel profile-card">
          <div class="card-title">
            <span class="card-icon">🏢</span>
            <h3>Kurumsal Kimlik & Tescil</h3>
          </div>
          <div class="divider"></div>
          
          <div class="profile-details-list">
            <div class="profile-detail-row">
              <span class="label">Şirket Adı</span>
              <span class="value">{{ profile.company_name }}</span>
            </div>
            <div class="profile-detail-row">
              <span class="label">Ticari Unvanı</span>
              <span class="value">{{ profile.legal_title }}</span>
            </div>
            <div class="profile-detail-row">
              <span class="label">Kayıtlı Araç Sayısı</span>
              <span class="value highlight-badge">{{ profile.registered_vehicles_count }} Araç</span>
            </div>
            <div class="profile-detail-row">
              <span class="label">Müşteri Tipi</span>
              <span class="value">Kurumsal Filo</span>
            </div>
          </div>
        </div>

        <!-- Right Side: İletişim & Adres -->
        <div class="glass-panel profile-card">
          <div class="card-title">
            <span class="card-icon">📞</span>
            <h3>İletişim & Adres Bilgileri</h3>
          </div>
          <div class="divider"></div>
          
          <div class="profile-details-list">
            <div class="profile-detail-row">
              <span class="label">E-posta Adresi</span>
              <span class="value">{{ profile.email }}</span>
            </div>
            <div class="profile-detail-row">
              <span class="label">Telefon Numarası</span>
              <span class="value">{{ profile.phone }}</span>
            </div>
            <div class="profile-detail-row">
              <span class="label">Adres</span>
              <span class="value" style="text-align: right; line-height: 1.4; max-width: 250px;">{{ profile.address }}</span>
            </div>
          </div>
        </div>

        <!-- Full Width Bottom Side: Yetkili Hesap -->
        <div class="glass-panel profile-card" style="grid-column: span 2;">
          <div class="card-title">
            <span class="card-icon">👨‍💼</span>
            <h3>Sözleşme & Yetkili Kullanıcı</h3>
          </div>
          <div class="divider"></div>
          
          <div class="grid-3" style="gap: 20px;">
            <div class="user-info-box">
              <span class="info-label">Filo Yöneticisi</span>
              <strong class="info-val">Ahmet Yılmaz</strong>
            </div>
            <div class="user-info-box">
              <span class="info-label">Kullanıcı Rolü</span>
              <strong class="info-val" style="color: var(--secondary);">Yönetici / Admin</strong>
            </div>
            <div class="user-info-box">
              <span class="info-label">Sözleşme Durumu</span>
              <strong class="info-val" style="color: #059669;">Aktif Kiralama</strong>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const profile = ref({
  company_name: '',
  legal_title: '',
  registered_vehicles_count: 0,
  email: '',
  phone: '',
  address: ''
})
const loading = ref(true)

const fetchProfile = async () => {
  try {
    const response = await fetch('/api/company/profile')
    if (response.ok) {
      profile.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching profile:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
.profile-card {
  padding: 30px;
  height: 100%;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  font-size: 1.5rem;
}

.card-title h3 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.divider {
  height: 1px;
  background: var(--border-color);
  margin: 20px 0;
}

.profile-details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95rem;
}

.profile-detail-row .label {
  color: var(--text-dark);
  font-weight: 500;
}

.profile-detail-row .value {
  color: var(--text-main);
  font-weight: 600;
}

.highlight-badge {
  background: rgba(79, 70, 229, 0.08);
  color: var(--primary) !important;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  border: 1px solid rgba(79, 70, 229, 0.15);
}

.user-info-box {
  background: #f8fafc;
  border: 1px solid var(--border-color);
  padding: 15px 20px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-label {
  font-size: 0.8rem;
  color: var(--text-dark);
  font-weight: 500;
}

.info-val {
  font-size: 1rem;
  color: var(--text-main);
}

@media (max-width: 768px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
  .profile-card {
    grid-column: span 1 !important;
  }
}
</style>
