<template>
  <div class="app-bg-glow"></div>
  <div class="auth-container">
    <div class="glass-panel auth-card fade-in-up">
      <router-link to="/" class="nav-logo" style="justify-content: center; margin-bottom: 30px;">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #7c3aed, #db2777);">F</div>
        <span style="font-size: 1.6rem; font-weight: 800;">FleetRent <span style="color: #7c3aed; font-size: 0.9rem; vertical-align: super; font-weight: 500;">Yönetici</span></span>
      </router-link>

      <h2 style="font-size: 1.5rem; text-align: center; margin-bottom: 8px;">Yönetici Girişi</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; margin-bottom: 25px;">
        Filo taleplerini ve kiralama tekliflerini yönetmek için giriş yapın.
      </p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="admin-email" class="form-label">Yönetici E-posta Adresi</label>
          <input 
            id="admin-email"
            name="email"
            type="email" 
            v-model="email" 
            autocomplete="username"
            required 
            class="form-input" 
            placeholder="admin@fleetrent.com"
          >
        </div>

        <div class="form-group" style="margin-bottom: 25px;">
          <label for="admin-password" class="form-label">Şifre</label>
          <input 
            id="admin-password"
            name="password"
            type="password" 
            v-model="password" 
            autocomplete="current-password"
            required 
            class="form-input" 
            placeholder="••••••••"
          >
        </div>

        <button type="submit" class="btn btn-accent btn-block" :disabled="loading" style="background: linear-gradient(135deg, #7c3aed, #db2777); border: none; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);">
          {{ loading ? 'Giriş Yapılıyor...' : 'Yönetici Paneline Giriş Yap' }}
        </button>
      </form>

      <div style="margin-top: 25px; text-align: center;">
        <router-link to="/login" style="color: var(--text-muted); font-size: 0.85rem; text-decoration: none;" class="hover-underline">
          ← Müşteri Portalı Girişine Dön
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!email.value || !password.value) return
  
  loading.value = true
  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value
      })
    })

    if (res.ok) {
      const data = await res.json()
      localStorage.setItem('fleetcar_admin_token', data.token)
      localStorage.setItem('fleetcar_admin_user', data.email)
      router.push('/admin-portal')
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || `Giriş yapılamadı (Hata Kodu: ${res.status}). Lütfen kullanıcı bilgilerinizi ve sunucu durumunu kontrol edin.`)
    }
  } catch (err) {
    console.error('Admin login error:', err)
    alert('Sunucuya bağlanılamadı. Lütfen internet bağlantınızı ve backend servisini kontrol edin.')
  } finally {
    loading.value = false
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

.django-info-box {
  background: rgba(124, 58, 237, 0.05);
  border: 1px solid rgba(124, 58, 237, 0.15);
  padding: 12px 15px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text-muted);
}

.django-info-box code {
  background: rgba(124, 58, 237, 0.1);
  color: #7c3aed;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-weight: bold;
}
</style>
