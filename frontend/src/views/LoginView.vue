<template>
  <div style="min-height: 100vh; background: #f8fafc; display: flex; flex-direction: column;">
    <!-- Top Header Bar matching screenshot -->
    <header class="hero-dark-bg" style="padding: 16px 8%; text-align: left; height: 60px; display: flex; align-items: center;">
      <router-link to="/" class="nav-logo" style="text-decoration: none;">
        <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
        <span style="font-weight: 800; font-size: 1.4rem; color: #ffffff;">FleetRent</span>
      </router-link>
    </header>

    <!-- Main Container -->
    <main style="flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px;">
      <!-- Step 1: Role Selection Screen (matching screenshot with 3 tiles) -->
      <div v-if="selectedRole === null" class="login-selection-card fade-in-up">
        <div class="nav-logo" style="justify-content: center; margin-bottom: 12px;">
          <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
          <span style="font-weight: 800; font-size: 1.6rem; color: #0f172a;">FleetRent</span>
        </div>
        <p style="color: #64748b; font-size: 0.95rem; font-weight: 500;">Giriş tipini seçin</p>

        <div class="login-role-grid">
          <!-- 1. Müşteri Girişi -->
          <div @click="selectedRole = 'customer'" class="login-role-tile tile-customer">
            <span class="tile-icon">🏢</span>
            <span class="tile-title">Müşteri Girişi</span>
            <span style="font-size: 0.75rem; color: #64748b; margin-top: 4px; font-weight: 500;">Filo Yönetim Paneli</span>
          </div>

          <!-- 2. Tedarikçi Girişi (Araba Sağlayıcı Kiralama Firmaları) -->
          <router-link to="/supplier-login" class="login-role-tile tile-supplier">
            <span class="tile-icon">🏭</span>
            <span class="tile-title">Tedarikçi Girişi</span>
            <span style="font-size: 0.75rem; color: #10b981; margin-top: 4px; font-weight: 600;">Araba Sağlayıcı & Kiralama</span>
          </router-link>

          <!-- 3. Servis Girişi (Bakım, Lastik & Oto Kurtarma) -->
          <router-link to="/service-login" class="login-role-tile tile-service">
            <span class="tile-icon">🔧</span>
            <span class="tile-title">Servis Girişi</span>
            <span style="font-size: 0.75rem; color: #2563eb; margin-top: 4px; font-weight: 600;">Bakım, Lastik & Oto Kurtarma</span>
          </router-link>
        </div>

        <div style="margin-top: 30px;">
          <router-link to="/" style="color: #64748b; text-decoration: none; font-size: 0.88rem;">
            ← Anasayfaya Geri Dön
          </router-link>
        </div>
      </div>

      <!-- Step 2: Customer Credentials / Register Form -->
      <div v-else class="glass-panel login-card fade-in-up" style="max-width: 460px; width: 100%; padding: 36px; border-radius: 20px; background: #ffffff;">
        <button @click="selectedRole = null" style="background: none; border: none; cursor: pointer; color: #2563eb; font-size: 0.88rem; margin-bottom: 20px; font-weight: 600;">
          ← Giriş Tipini Değiştir
        </button>

        <div style="display: flex; gap: 10px; background: #f1f5f9; padding: 4px; border-radius: 12px; margin-bottom: 20px;">
          <button @click="authMode = 'login'" :style="{ background: authMode === 'login' ? '#ffffff' : 'transparent', color: authMode === 'login' ? '#0f172a' : '#64748b', fontWeight: authMode === 'login' ? '700' : '500' }" style="flex: 1; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.95rem; transition: all 0.2s;">
            Giriş Yap
          </button>
          <button @click="authMode = 'register'" :style="{ background: authMode === 'register' ? '#ffffff' : 'transparent', color: authMode === 'register' ? '#0f172a' : '#64748b', fontWeight: authMode === 'register' ? '700' : '500' }" style="flex: 1; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 0.95rem; transition: all 0.2s;">
            Kayıt Ol
          </button>
        </div>

        <div v-if="authMode === 'login'">
          <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">Müşteri Girişi</h2>
          <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 20px;">
            Filo yönetim panelinize erişmek için bilgilerinizi girin.
          </p>

          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="form-label">E-posta Adresi</label>
              <input type="email" v-model="email" required class="form-input" placeholder="isim@sirket.com">
            </div>

            <div class="form-group" style="margin-bottom: 25px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <label class="form-label" style="margin-bottom: 0;">Şifre</label>
                <a href="#" style="font-size: 0.8rem; color: #2563eb; text-decoration: none;">Şifremi Unuttum?</a>
              </div>
              <input type="password" v-model="password" required class="form-input" placeholder="••••••••">
            </div>

            <button type="submit" class="btn btn-blue" style="width: 100%; padding: 14px;" :disabled="loading">
              {{ loading ? 'Giriş Yapılıyor...' : 'Giriş Yap' }}
            </button>
          </form>
        </div>

        <div v-else>
          <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">Yeni Müşteri Kaydı</h2>
          <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 20px;">
            Teklif almak ve filo yönetim sistemine erişmek için hesabınızı oluşturun.
          </p>

          <form @submit.prevent="handleRegister">
            <div class="form-group">
              <label class="form-label">Şirket / Firma Adı</label>
              <input type="text" v-model="companyName" class="form-input" placeholder="Örn: Tekno Lojistik A.Ş.">
            </div>

            <div class="form-group">
              <label class="form-label">E-posta Adresi *</label>
              <input type="email" v-model="email" required class="form-input" placeholder="isim@sirket.com">
            </div>

            <div class="form-group">
              <label class="form-label">Telefon Numarası</label>
              <input type="tel" v-model="phone" class="form-input" placeholder="05XX XXX XX XX">
            </div>

            <div class="form-group" style="margin-bottom: 25px;">
              <label class="form-label">Şifre * (En az 6 karakter)</label>
              <input type="password" v-model="password" required minlength="6" class="form-input" placeholder="••••••••">
            </div>

            <button type="submit" class="btn btn-blue" style="width: 100%; padding: 14px;" :disabled="loading">
              {{ loading ? 'Kaydediliyor...' : 'Hesap Oluştur ve Devam Et' }}
            </button>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const selectedRole = ref(route.query.role || null)
const authMode = ref(route.query.tab === 'register' ? 'register' : 'login')
const email = ref('')
const password = ref('')
const companyName = ref('')
const phone = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!email.value || !password.value) return
  loading.value = true
  
  try {
    const res = await fetch('/api/customer/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value
      })
    })

    if (res.ok) {
      const data = await res.json()
      const cust = data.customer || {}
      
      localStorage.setItem('fleetcar_token', data.token)
      localStorage.setItem('fleetcar_customer_id', String(cust.id || '1'))
      localStorage.setItem('fleetcar_customer_name', cust.company_name || 'Müşteri Firma')
      localStorage.setItem('fleetcar_user_email', cust.email || email.value)
      localStorage.setItem('fleet_customer', JSON.stringify(cust))
      
      router.push('/dashboard')
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Giriş yapılamadı! Lütfen e-posta ve şifrenizi kontrol edin.')
    }
  } catch (err) {
    console.error('Customer Login error:', err)
    alert('Sunucuya bağlanılamadı. Lütfen backend servisini kontrol edin.')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!email.value || !password.value) return
  loading.value = true
  
  try {
    const res = await fetch('/api/customer/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
        company_name: companyName.value,
        phone: phone.value
      })
    })

    if (res.ok) {
      const data = await res.json()
      const cust = data.customer || {}
      
      localStorage.setItem('fleetcar_token', data.token)
      localStorage.setItem('fleetcar_customer_id', String(cust.id || '1'))
      localStorage.setItem('fleetcar_customer_name', cust.company_name || companyName.value || 'Müşteri Firma')
      localStorage.setItem('fleetcar_user_email', cust.email || email.value)
      localStorage.setItem('fleet_customer', JSON.stringify(cust))
      
      alert('Kaydınız başarıyla oluşturuldu! Şimdi teklifinizi oluşturabilirsiniz.')
      router.push('/')
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Kayıt oluşturulamadı! Lütfen bilgilerinizi kontrol edin.')
    }
  } catch (err) {
    console.error('Customer Register error:', err)
    alert('Sunucuya bağlanılamadı. Lütfen backend servisini kontrol edin.')
  } finally {
    loading.value = false
  }
}
</script>

