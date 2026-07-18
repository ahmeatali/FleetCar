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
        <h4 class="company-name">Ahmet Yılmaz</h4>
        <span class="role-badge">Filo Yöneticisi</span>
      </div>
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
          <span>Araç Takibi</span>
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
import { useRouter } from 'vue-router'

const router = useRouter()

const logout = () => {
  localStorage.removeItem('fleetcar_token')
  localStorage.removeItem('fleetcar_user_email')
  router.push('/')
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
