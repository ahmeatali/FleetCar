<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <!-- Reusable Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header">
        <div>
          <h1>Filo Yönetim Paneli</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Genel filo durumu, aktif talepler ve istatistikler.</p>
        </div>
        <div class="current-date">
          📅 Bugün: {{ currentDate }}
        </div>
      </header>

      <!-- Stats Grid -->
      <section class="grid-4" style="margin-top: 30px;">
        <div class="glass-panel stat-card">
          <div class="stat-header">
            <span class="stat-title">Toplam Araç</span>
            <span class="stat-icon">🚗</span>
          </div>
          <div class="stat-value">{{ stats.total_vehicles }}</div>
          <div class="stat-desc">Kayıtlı aktif filo adedi</div>
        </div>

        <div class="glass-panel stat-card">
          <div class="stat-header">
            <span class="stat-title">Aktif Araçlar</span>
            <span class="stat-icon" style="color: var(--status-active-text);">🟢</span>
          </div>
          <div class="stat-value" style="color: var(--status-active-text);">{{ stats.active_vehicles }}</div>
          <div class="stat-desc">Sorunsuz seyir halinde</div>
        </div>

        <div class="glass-panel stat-card">
          <div class="stat-header">
            <span class="stat-title">İşlemdeki Talepler</span>
            <span class="stat-icon" style="color: var(--status-service-text);">⚙️</span>
          </div>
          <div class="stat-value" style="color: var(--status-service-text);">{{ stats.pending_requests }}</div>
          <div class="stat-desc">Servis, lastik veya yol yardımda</div>
        </div>

        <div class="glass-panel stat-card">
          <div class="stat-header">
            <span class="stat-title">Ortalama Kilometre</span>
            <span class="stat-icon">📈</span>
          </div>
          <div class="stat-value">{{ stats.avg_mileage?.toLocaleString() }} km</div>
          <div class="stat-desc">Araç başı kat edilen mesafe</div>
        </div>
      </section>

      <!-- Secondary Detailed Stats -->
      <section class="grid-4" style="margin-top: 20px;">
        <div class="glass-panel stat-mini">
          <span class="dot" style="background: var(--status-service-text);"></span>
          <span>Bakım/Onarımda:</span>
          <strong>{{ stats.in_service }} Araç</strong>
        </div>
        <div class="glass-panel stat-mini">
          <span class="dot" style="background: var(--status-tire-text);"></span>
          <span>Lastik Değişiminde:</span>
          <strong>{{ stats.tire_change }} Araç</strong>
        </div>
        <div class="glass-panel stat-mini">
          <span class="dot" style="background: var(--status-roadside-text);"></span>
          <span>Yol Yardımında:</span>
          <strong>{{ stats.roadside_assistance }} Araç</strong>
        </div>
        <div class="glass-panel stat-mini">
          <span class="dot" style="background: var(--status-replacement-text);"></span>
          <span>İkame Araç Alan:</span>
          <strong>{{ stats.replacement_waiting }} Araç</strong>
        </div>
      </section>

      <!-- Grid for Visuals and Activities -->
      <div class="grid-2" style="margin-top: 30px; grid-template-columns: 1.2fr 0.8fr;">
        <!-- Recent Supplier Requests -->
        <div class="glass-panel card-panel">
          <div class="panel-header">
            <h3>Son Tedarikçi İşlemleri</h3>
            <router-link to="/dashboard/requests" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">Tümünü Gör</router-link>
          </div>
          
          <div v-if="loading" class="text-center" style="padding: 40px 0;">Yükleniyor...</div>
          
          <div v-else-if="requests.length === 0" class="empty-state">
            <p>Aktif tedarikçi talebi bulunmamaktadır.</p>
          </div>

          <div v-else class="requests-list">
            <div v-for="req in requests.slice(0, 3)" :key="req.id" class="request-item">
              <div class="req-left">
                <span class="badge" :class="getBadgeClass(req.type)">{{ req.type }}</span>
                <div class="req-title">
                  <strong>{{ req.vehicle_plate }}</strong> - {{ req.supplier_name }}
                  <p class="req-desc">{{ req.description }}</p>
                </div>
              </div>
              <div class="req-right">
                <span class="badge" :class="getStatusBadgeClass(req.status)">{{ req.status }}</span>
                <span class="req-time">{{ req.created_at }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Visual Analytics Simulation -->
        <div class="glass-panel card-panel">
          <h3>Filo Yakıt Kırılımı</h3>
          <div class="visual-chart" style="margin-top: 25px;">
            <div v-for="(count, fuel) in stats.fuel_stats" :key="fuel" class="chart-row">
              <div class="chart-label">
                <span>{{ fuel }}</span>
                <strong>{{ count }} Araç ({{ Math.round((count / stats.total_vehicles) * 100) }}%)</strong>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar" :style="{ width: ((count / stats.total_vehicles) * 100) + '%', background: getFuelColor(fuel) }"></div>
              </div>
            </div>
          </div>

          <div class="quick-actions-panel" style="margin-top: 30px;">
            <h3>Hızlı Aksiyonlar</h3>
            <div class="actions-buttons" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
              <router-link to="/dashboard/vehicles" class="btn btn-secondary" style="font-size: 0.8rem; padding: 10px;">🚗 Yeni Araç Ekle</router-link>
              <router-link to="/dashboard/requests" class="btn btn-secondary" style="font-size: 0.8rem; padding: 10px;">⚙️ Servis Kaydı Aç</router-link>
              <router-link to="/dashboard/requests" class="btn btn-secondary" style="font-size: 0.8rem; padding: 10px;">🛞 Lastik Talebi</router-link>
              <router-link to="/dashboard/requests" class="btn btn-danger" style="font-size: 0.8rem; padding: 10px;">🚨 Acil Yol Yardım</router-link>
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

const stats = ref({})
const requests = ref([])
const loading = ref(true)
const currentDate = ref(new Date().toLocaleDateString('tr-TR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }))

const fetchDashboardData = async () => {
  try {
    const [statsRes, reqsRes] = await Promise.all([
      fetch('/api/dashboard/stats'),
      fetch('/api/requests')
    ])
    
    if (statsRes.ok && reqsRes.ok) {
      stats.value = await statsRes.json()
      requests.value = await reqsRes.json()
      // Reverse to show newest requests first
      requests.value.reverse()
    }
  } catch (error) {
    console.error('Error fetching dashboard stats:', error)
  } finally {
    loading.value = false
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

const getFuelColor = (fuel) => {
  switch (fuel) {
    case 'Elektrik': return '#34d399'
    case 'Hibrit': return '#60a5fa'
    case 'Benzin': return '#a855f7'
    case 'Dizel': return '#fbbf24'
    default: return '#cbd5e1'
  }
}

onMounted(() => {
  fetchDashboardData()
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

.current-date {
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  padding: 8px 16px;
  border-radius: 8px;
  color: var(--text-muted);
}

.stat-card {
  padding: 24px;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.stat-title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.stat-icon {
  font-size: 1.25rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 5px;
}

.stat-desc {
  font-size: 0.75rem;
  color: var(--text-dark);
}

.stat-mini {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  font-size: 0.85rem;
}

.stat-mini .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-mini strong {
  margin-left: auto;
}

.card-panel {
  padding: 30px;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.requests-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.request-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.request-item:hover {
  border-color: rgba(99, 102, 241, 0.2);
  background: rgba(255,255,255,0.04);
}

.req-left {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.req-title {
  font-size: 0.95rem;
}

.req-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.req-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.req-time {
  font-size: 0.75rem;
  color: var(--text-dark);
}

.empty-state {
  padding: 50px 0;
  text-align: center;
  color: var(--text-muted);
}

.chart-row {
  margin-bottom: 15px;
}

.chart-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.chart-label span {
  color: var(--text-muted);
}

.progress-bar-container {
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}
</style>
