<template>
  <aside class="portal-sidebar">
    <!-- Top Header & Profile Summary -->
    <div class="sidebar-top">
      <router-link to="/dashboard" class="nav-logo" style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px; text-decoration: none;">
        <div class="nav-logo-icon" style="background: #2563eb; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800;">F</div>
        <span style="font-weight: 800; font-size: 1.3rem; color: #0f172a;">FleetRent</span>
      </router-link>

      <!-- User profile summary -->
      <div class="user-profile-summary">
        <div class="avatar">👨‍💼</div>
        <div class="profile-details">
          <h4 class="company-name" :title="customerName">{{ customerName }}</h4>
          <span class="role-badge">Filo Yöneticisi</span>
        </div>
      </div>

      <!-- Warning Box for Missing Company Documents -->
      <div v-if="documentsUploaded === false" class="doc-warning-box">
        <div class="doc-warning-title">
          <span>⚠️</span>
          <span>Evraklar Eksik!</span>
        </div>
        <p class="doc-warning-text">
          İşlem yapmadan önce şirket evraklarınızı tamamlayın.
        </p>
        <router-link to="/dashboard/settings?tab=sirket_evraklari" class="doc-warning-btn">
          📂 Evrakları Tamamla ➔
        </router-link>
      </div>
    </div>

    <!-- Scrollable Middle Navigation Menu -->
    <div class="sidebar-menu-wrapper">
      <ul class="sidebar-menu">
        <li>
          <router-link to="/dashboard" class="sidebar-link" exact-active-class="active">
            <span class="icon">📊</span>
            <span>Genel Bakış</span>
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/vehicles" class="sidebar-link" active-class="active">
            <span class="icon">🚗</span>
            <span>Araç Yönetimi</span>
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/requests" class="sidebar-link" active-class="active">
            <span class="icon">⚙️</span>
            <span>Tedarikçi İşlemleri</span>
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/quotes" class="sidebar-link" active-class="active">
            <span class="icon">📑</span>
            <span>Kiralama Teklifleri</span>
          </router-link>
          <!-- Guidance box when customer has uploaded documents but has 0 registered vehicles -->
          <div v-if="documentsUploaded && hasNoVehicles" class="promo-guidance-box">
            <div class="promo-guidance-title">
              <span>🚗</span>
              <span>Henüz aracınız yok!</span>
            </div>
            <p class="promo-guidance-text">
              Hemen teklif alın, filonuzu kurun.
            </p>
            <router-link to="/dashboard/quotes?new=true" class="promo-guidance-btn">
              ✨ Hemen Teklif Al
            </router-link>
          </div>
        </li>
        <li>
          <router-link to="/dashboard/reports" class="sidebar-link" active-class="active">
            <span class="icon">📈</span>
            <span>Raporlar</span>
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/settings" class="sidebar-link" active-class="active">
            <span class="icon">⚙️</span>
            <span>Ayarlar</span>
          </router-link>
          <!-- Sub-links under Ayarlar -->
          <ul v-if="$route.path.includes('/settings')" class="settings-sub-menu">
            <li>
              <router-link to="/dashboard/settings?tab=kullanicilar" class="sub-link" :class="{ 'sub-active': $route.query.tab === 'kullanicilar' || !$route.query.tab }">
                <span>👥</span> Kullanıcılar
              </router-link>
            </li>
            <li>
              <router-link to="/dashboard/settings?tab=teslim_formlari" class="sub-link" :class="{ 'sub-active': $route.query.tab === 'teslim_formlari' }">
                <span>📋</span> Teslim Formları
              </router-link>
            </li>
            <li>
              <router-link to="/dashboard/settings?tab=bayi_sozlesmesi" class="sub-link" :class="{ 'sub-active': $route.query.tab === 'bayi_sozlesmesi' }">
                <span>📜</span> Bayi Sözleşmesi
              </router-link>
            </li>
            <li>
              <router-link to="/dashboard/settings?tab=sirket_evraklari" class="sub-link" :class="{ 'sub-active': $route.query.tab === 'sirket_evraklari' }">
                <span>🏢</span> Şirket Evraklarım
              </router-link>
            </li>
            <li>
              <router-link to="/dashboard/settings?tab=entegrasyonlar" class="sub-link" :class="{ 'sub-active': $route.query.tab === 'entegrasyonlar' }">
                <span>📡</span> API & Entegrasyonlar
              </router-link>
            </li>
          </ul>
        </li>
      </ul>
    </div>

    <!-- Pinned Bottom Footer: Profile Link + Logout -->
    <div class="sidebar-footer">
      <router-link to="/profile" class="sidebar-link" active-class="active">
        <span class="icon">👤</span>
        <span>Profilim</span>
      </router-link>

      <button @click="logout" class="sidebar-link logout-btn">
        <span class="icon">🚪</span>
        <span>Çıkış Yap</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const documentsUploaded = ref(true)
const hasNoVehicles = ref(false)

const customerName = computed(() => {
  return localStorage.getItem('fleetcar_customer_name') || localStorage.getItem('fleetcar_user_email') || 'Filo Müşterisi'
})

const checkCompanyStatus = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) return
  try {
    const res = await fetch(`/api/company/profile?customer_id=${customerId}`)
    if (res.ok) {
      const data = await res.json()
      documentsUploaded.value = Boolean(data.documents_uploaded)
      const totalVehicles = (data.actual_vehicles_count || 0) + (data.registered_vehicles_count || 0)
      hasNoVehicles.value = (totalVehicles === 0)
    }
  } catch (e) {
    console.error('Company status check error:', e)
  }
}

onMounted(() => {
  checkCompanyStatus()
})

const logout = () => {
  localStorage.removeItem('fleetcar_token')
  localStorage.removeItem('fleetcar_customer_id')
  localStorage.removeItem('fleetcar_customer_name')
  localStorage.removeItem('fleetcar_user_email')
  localStorage.removeItem('fleetcar_user_verified')
  localStorage.removeItem('fleet_customer')
  router.push('/login?role=customer')
}
</script>

<style scoped>
.portal-sidebar {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px 16px 16px 16px;
  box-sizing: border-box;
  background: #ffffff;
}

.sidebar-top {
  flex-shrink: 0;
}

.sidebar-menu-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin: 10px 0;
  padding-right: 2px;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

.sidebar-menu-wrapper::-webkit-scrollbar {
  width: 4px;
}
.sidebar-menu-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.sidebar-footer {
  flex-shrink: 0;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #ffffff;
  z-index: 5;
}

.user-profile-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  margin-bottom: 10px;
}

.avatar {
  font-size: 1.3rem;
  background: rgba(79, 70, 229, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-details {
  min-width: 0;
}

.company-name {
  font-size: 0.88rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
  margin: 0;
  color: #0f172a;
}

.role-badge {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 500;
}

.doc-warning-box {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 10px;
}

.doc-warning-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  color: #c2410c;
  margin-bottom: 4px;
  font-size: 0.82rem;
}

.doc-warning-text {
  color: #9a3412;
  font-size: 0.76rem;
  line-height: 1.35;
  margin: 0 0 8px 0;
}

.doc-warning-btn {
  display: block;
  text-align: center;
  background: #ea580c;
  color: #ffffff;
  font-weight: 700;
  padding: 6px 0;
  border-radius: 8px;
  text-decoration: none;
  font-size: 0.78rem;
}

.promo-guidance-box {
  margin: 6px 0 10px 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
  border: 1px solid #c7d2fe;
  border-radius: 10px;
  padding: 10px;
}

.promo-guidance-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 700;
  color: #3730a3;
  margin-bottom: 4px;
  font-size: 0.78rem;
}

.promo-guidance-text {
  color: #4338ca;
  font-size: 0.72rem;
  line-height: 1.35;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.promo-guidance-btn {
  display: block;
  text-align: center;
  background: #4f46e5;
  color: #ffffff;
  font-weight: 700;
  padding: 6px 0;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.75rem;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
}

.settings-sub-menu {
  list-style: none;
  padding-left: 20px;
  margin: 4px 0 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sub-link {
  font-size: 0.8rem;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  color: #64748b;
  font-weight: 500;
}

.sub-link:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.sub-active {
  background: #eff6ff !important;
  color: #2563eb !important;
  font-weight: 700 !important;
}

.logout-btn {
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  color: #64748b;
  font-weight: 600;
}

.logout-btn:hover {
  background: #fef2f2 !important;
  color: #dc2626 !important;
}

.icon {
  font-size: 1.2rem;
}
</style>
