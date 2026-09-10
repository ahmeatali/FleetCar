<template>
  <aside class="portal-sidebar">
    <router-link to="/dashboard" class="nav-logo" style="margin-bottom: 20px;">
      <div class="nav-logo-icon">F</div>
      <span>FleetCar</span>
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
    <div v-if="documentsUploaded === false" style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 12px; margin-bottom: 16px;">
      <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #c2410c; margin-bottom: 4px; font-size: 0.82rem;">
        <span>⚠️</span>
        <span>Evraklar Eksik!</span>
      </div>
      <p style="color: #9a3412; font-size: 0.76rem; line-height: 1.4; margin-bottom: 8px;">
        İşlem yapmadan önce şirket evraklarınızı tamamlayın.
      </p>
      <router-link to="/dashboard/settings?tab=sirket_evraklari" style="display: block; text-align: center; background: #ea580c; color: #ffffff; font-weight: 700; padding: 6px 0; border-radius: 8px; text-decoration: none; font-size: 0.78rem;">
        📂 Evrakları Tamamla ➔
      </router-link>
    </div>

    <!-- Navigation links -->
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
        <div v-if="documentsUploaded && hasNoVehicles" style="margin: 6px 0 12px 16px; background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%); border: 1px solid #c7d2fe; border-radius: 10px; padding: 10px;">
          <div style="display: flex; align-items: center; gap: 5px; font-weight: 700; color: #3730a3; margin-bottom: 4px; font-size: 0.78rem;">
            <span>🚗</span>
            <span>Henüz aracınız yok!</span>
          </div>
          <p style="color: #4338ca; font-size: 0.72rem; line-height: 1.35; margin-bottom: 8px; font-weight: 500;">
            Hemen teklif alın, filonuzu kurun.
          </p>
          <router-link to="/dashboard/quotes?new=true" style="display: block; text-align: center; background: #4f46e5; color: #ffffff; font-weight: 700; padding: 6px 0; border-radius: 6px; text-decoration: none; font-size: 0.75rem; box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);">
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
        <ul v-if="$route.path.includes('/settings')" style="list-style: none; padding-left: 24px; margin: 4px 0 8px; display: flex; flex-direction: column; gap: 4px;">
          <li>
            <router-link to="/dashboard/settings?tab=kullanicilar" style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;" :style="{ background: $route.query.tab === 'kullanicilar' || !$route.query.tab ? '#eff6ff' : 'transparent', color: $route.query.tab === 'kullanicilar' || !$route.query.tab ? '#2563eb' : '#64748b', fontWeight: $route.query.tab === 'kullanicilar' || !$route.query.tab ? '700' : '500' }">
              <span>👥</span> Kullanıcılar
            </router-link>
          </li>
          <li>
            <router-link to="/dashboard/settings?tab=teslim_formlari" style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;" :style="{ background: $route.query.tab === 'teslim_formlari' ? '#eff6ff' : 'transparent', color: $route.query.tab === 'teslim_formlari' ? '#2563eb' : '#64748b', fontWeight: $route.query.tab === 'teslim_formlari' ? '700' : '500' }">
              <span>📋</span> Teslim Formları
            </router-link>
          </li>
          <li>
            <router-link to="/dashboard/settings?tab=bayi_sozlesmesi" style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;" :style="{ background: $route.query.tab === 'bayi_sozlesmesi' ? '#eff6ff' : 'transparent', color: $route.query.tab === 'bayi_sozlesmesi' ? '#2563eb' : '#64748b', fontWeight: $route.query.tab === 'bayi_sozlesmesi' ? '700' : '500' }">
              <span>📜</span> Bayi Sözleşmesi
            </router-link>
          </li>
          <li>
            <router-link to="/dashboard/settings?tab=sirket_evraklari" style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;" :style="{ background: $route.query.tab === 'sirket_evraklari' ? '#eff6ff' : 'transparent', color: $route.query.tab === 'sirket_evraklari' ? '#2563eb' : '#64748b', fontWeight: $route.query.tab === 'sirket_evraklari' ? '700' : '500' }">
              <span>🏢</span> Şirket Evraklarım
            </router-link>
          </li>
          <li>
            <router-link to="/dashboard/settings?tab=entegrasyonlar" style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; transition: all 0.2s;" :style="{ background: $route.query.tab === 'entegrasyonlar' ? '#eff6ff' : 'transparent', color: $route.query.tab === 'entegrasyonlar' ? '#2563eb' : '#64748b', fontWeight: $route.query.tab === 'entegrasyonlar' ? '700' : '500' }">
              <span>📡</span> API & Entegrasyonlar
            </router-link>
          </li>
        </ul>
      </li>

    </ul>

    <!-- Bottom area: Profile Link + Logout -->
    <div style="margin-top: auto; display: flex; flex-direction: column; gap: 8px; width: 100%;">
      <!-- Profile Page Link -->
      <router-link to="/profile" class="sidebar-link" active-class="active">
        <span class="icon">👤</span>
        <span>Profilim</span>
      </router-link>

      <!-- Logout Button -->
      <button @click="logout" class="sidebar-link logout-btn" style="width: 100%; border: none; background: transparent; cursor: pointer; text-align: left;">
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
  localStorage.removeItem('fleet_customer')
  router.push('/login?role=customer')
}
</script>


<style scoped>
.user-profile-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  margin-bottom: 15px;
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
}

.company-name {
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.role-badge {
  font-size: 0.7rem;
  color: var(--secondary);
  font-weight: 500;
}

.logout-btn {
  color: var(--text-dark);
}

.logout-btn:hover {
  background: #fef2f2;
  color: #dc2626;
}

.icon {
  font-size: 1.2rem;
}
</style>
