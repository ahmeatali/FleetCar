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

        <div v-if="!showForgot">
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
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <label for="admin-password" class="form-label" style="margin: 0;">Şifre</label>
                <a href="#" @click.prevent="showForgot = true" style="font-size: 0.8rem; color: #7c3aed; text-decoration: none; font-weight: 600;">Şifremi Unuttum?</a>
              </div>
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

            <button type="submit" class="btn btn-accent btn-block" :disabled="loading" style="background: linear-gradient(135deg, #7c3aed, #db2777); border: none; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3); width: 100%;">
              {{ loading ? 'Giriş Yapılıyor...' : 'Yönetici Paneline Giriş Yap' }}
            </button>
          </form>
        </div>

        <div v-else>
          <div v-if="forgotSuccess" style="padding: 14px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; color: #065f46; font-size: 0.88rem; margin-bottom: 20px;">
            ✅ {{ forgotSuccess }}
          </div>

          <form v-else @submit.prevent="handleForgotPassword">
            <div class="form-group" style="margin-bottom: 25px;">
              <label class="form-label">Yönetici E-posta Adresi *</label>
              <input type="email" v-model="forgotEmail" required class="form-input" placeholder="admin@fleetrent.com">
            </div>

            <button type="submit" class="btn btn-accent btn-block" style="background: linear-gradient(135deg, #7c3aed, #db2777); border: none; width: 100%;" :disabled="forgotLoading">
              {{ forgotLoading ? 'Gönderiliyor...' : 'Şifre Sıfırlama Bağlantısı Gönder' }}
            </button>
          </form>

          <div style="margin-top: 20px; text-align: center;">
            <button @click="showForgot = false" style="background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 0.88rem; font-weight: 600;">
              ← Giriş Ekranına Dön
            </button>
          </div>
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

const showForgot = ref(false)
const forgotEmail = ref('')
const forgotLoading = ref(false)
const forgotSuccess = ref('')

const handleForgotPassword = async () => {
  if (!forgotEmail.value) return
  forgotLoading.value = true
  forgotSuccess.value = ''

  try {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: forgotEmail.value })
    })

    const data = await res.json()
    if (res.ok) {
      forgotSuccess.value = data.message || 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.'
    } else {
      alert(data.detail || 'Bir hata oluştu.')
    }
  } catch (err) {
    console.error('Forgot password error:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    forgotLoading.value = false
  }
}

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
