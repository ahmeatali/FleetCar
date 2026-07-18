<template>
  <div class="app-bg-glow"></div>

  <div class="login-container fade-in-up">
    <router-link to="/" class="nav-logo" style="justify-content: center; margin-bottom: 30px;">
      <div class="nav-logo-icon">F</div>
      <span>FleetCar</span>
    </router-link>

    <div class="glass-panel login-card">
      <h2 class="text-center gradient-brand" style="font-size: 1.75rem; margin-bottom: 10px;">Müşteri Portalı Girişi</h2>
      <p class="text-center" style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">
        Filo yönetim panelinize erişmek için bilgilerinizi girin.
      </p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">E-posta Adresi</label>
          <input type="email" v-model="email" required class="form-input" placeholder="isim@sirket.com">
        </div>

        <div class="form-group" style="margin-bottom: 25px;">
          <div class="label-row">
            <label class="form-label">Şifre</label>
            <a href="#" class="forgot-pass-link">Şifremi Unuttum?</a>
          </div>
          <input type="password" v-model="password" required class="form-input" placeholder="••••••••">
        </div>

        <button type="submit" class="btn btn-primary btn-block" style="width: 100%;" :disabled="loading">
          {{ loading ? 'Giriş Yapılıyor...' : 'Giriş Yap' }}
        </button>
      </form>

      <div class="demo-account-info">
        <h4>💡 Demo Hesap Bilgileri</h4>
        <p>Proje testi için aşağıdaki şifreyi kullanabilirsiniz:</p>
        <div class="demo-credentials">
          <span>Şifre:</span> <strong>admin123</strong>
        </div>
      </div>
    </div>

    <div class="text-center" style="margin-top: 25px;">
      <router-link to="/" style="color: var(--text-muted); text-decoration: none; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 5px;">
        ← Anasayfaya Geri Dön
      </router-link>
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

const handleLogin = () => {
  loading.value = true
  
  // Simulate API authentication call
  setTimeout(() => {
    loading.value = false
    if (password.value === 'admin123') {
      localStorage.setItem('fleetcar_token', 'logged_in')
      localStorage.setItem('fleetcar_user_email', email.value || 'demo@sirket.com')
      router.push('/dashboard')
    } else {
      alert('Hatalı şifre! Lütfen demo şifresini (admin123) kullanın.')
    }
  }, 800)
}
</script>

<style scoped>
.login-container {
  max-width: 420px;
  margin: 100px auto 40px;
  padding: 0 20px;
}

.login-card {
  padding: 35px 30px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-pass-link {
  font-size: 0.8rem;
  color: var(--secondary);
  text-decoration: none;
  font-weight: 500;
}

.forgot-pass-link:hover {
  text-decoration: underline;
}

.demo-account-info {
  margin-top: 25px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 15px;
}

.demo-account-info h4 {
  font-size: 0.85rem;
  margin-bottom: 5px;
  color: var(--secondary);
}

.demo-account-info p {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.demo-credentials {
  margin-top: 8px;
  font-size: 0.8rem;
}

.demo-credentials strong {
  font-family: monospace;
  background: rgba(0,0,0,0.3);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--secondary);
  font-size: 0.9rem;
}

.text-center {
  text-align: center;
}

.btn-block {
  width: 100%;
}
</style>
