<template>
  <div class="app-bg-glow"></div>
  <div class="auth-container">
    <div class="glass-panel auth-card fade-in-up">
      <router-link to="/" class="nav-logo" style="justify-content: center; margin-bottom: 30px;">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #10b981, #059669);">F</div>
        <span style="font-size: 1.6rem; font-weight: 800;">FleetCar <span style="color: #10b981; font-size: 0.9rem; vertical-align: super; font-weight: 500;">Tedarikçi</span></span>
      </router-link>

      <h2 style="font-size: 1.5rem; text-align: center; margin-bottom: 8px;">Tedarikçi Girişi</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; margin-bottom: 25px;">
        Servis, lastik, yol yardım veya ikame araç hizmet taleplerini yönetmek için giriş yapın.
      </p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Tedarikçi Seçimi</label>
          <select v-model="selectedSupplierId" required class="form-select">
            <option value="" disabled>Tedarikçinizi seçin...</option>
            <option v-for="s in suppliers" :key="s.id" :value="s.id">
              {{ s.name }} ({{ getTypeName(s.type) }})
            </option>
          </select>
        </div>

        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Şifre</label>
          <input 
            type="password" 
            v-model="password" 
            required 
            class="form-input" 
            placeholder="••••••••"
          >
        </div>

        <button type="submit" class="btn btn-accent btn-block" style="background: linear-gradient(135deg, #10b981, #059669); border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
          Tedarikçi Portaline Giriş Yap
        </button>
      </form>

      <!-- Supplier Info Box -->
      <div class="supplier-info-box">
        <p>
          🔑 <strong>Test Giriş Bilgisi:</strong><br>
          İstediğiniz tedarikçiyi seçtikten sonra şifre olarak <code>supplier123</code> yazarak giriş yapabilirsiniz.
        </p>
      </div>

      <div style="margin-top: 25px; display: flex; flex-direction: column; gap: 10px; text-align: center;">
        <router-link to="/login" style="color: var(--text-muted); font-size: 0.85rem; text-decoration: none;" class="hover-underline">
          ← Müşteri Portalı Girişine Dön
        </router-link>
        <router-link to="/admin-login" style="color: var(--text-muted); font-size: 0.85rem; text-decoration: none;" class="hover-underline">
          ← Yönetici Girişine Dön
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const selectedSupplierId = ref('')
const password = ref('')

const suppliers = ref([
  { id: 1, name: "OtoPratik Maslak", type: "servis" },
  { id: 2, name: "Borusan Oto Servis", type: "servis" },
  { id: 3, name: "Lassa Bayi - Seçkin Oto", type: "lastik" },
  { id: 4, name: "Michelin - Uzman Lastik", type: "lastik" },
  { id: 5, name: "7/24 Acil Yol Yardım & Çekici", type: "yol_yardim" },
  { id: 6, name: "Güven Çekici Hizmetleri", type: "yol_yardim" },
  { id: 7, name: "Enterprise Filo Kiralama", type: "ikame_arac" },
  { id: 8, name: "Sixt Rent a Car", type: "ikame_arac" }
])

onMounted(async () => {
  try {
    const res = await fetch('/api/suppliers')
    if (res.ok) {
      suppliers.value = await res.json()
    }
  } catch (err) {
    console.error('Error fetching suppliers list:', err)
  }
})

const getTypeName = (type) => {
  const map = {
    'servis': 'Yetkili Servis',
    'lastik': 'Lastik Bayisi',
    'yol_yardim': 'Yol Yardım & Çekici',
    'ikame_arac': 'İkame Araç Tedarikçisi'
  }
  return map[type] || type
}

const handleLogin = () => {
  if (password.value === 'supplier123') {
    const selected = suppliers.value.find(s => s.id === parseInt(selectedSupplierId.value))
    if (selected) {
      localStorage.setItem('fleetcar_supplier_token', 'supplier_logged_in')
      localStorage.setItem('fleetcar_supplier_id', selected.id)
      localStorage.setItem('fleetcar_supplier_name', selected.name)
      localStorage.setItem('fleetcar_supplier_type', selected.type)
      router.push('/supplier-portal')
    }
  } else {
    alert('Hatalı şifre! Lütfen test şifresini (supplier123) girin.')
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}

.supplier-info-box {
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.15);
  padding: 12px 15px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text-muted);
}

.supplier-info-box code {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-weight: bold;
}
</style>
