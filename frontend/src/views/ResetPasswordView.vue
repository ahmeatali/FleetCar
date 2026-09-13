<template>
  <div style="min-height: 100vh; background: #f8fafc; display: flex; flex-direction: column;">
    <!-- Top Header Bar -->
    <header class="hero-dark-bg" style="padding: 16px 8%; text-align: left; height: 60px; display: flex; align-items: center;">
      <router-link to="/" class="nav-logo" style="text-decoration: none;">
        <div class="nav-logo-icon" style="background: #2563eb; border-radius: 8px;">⇄</div>
        <span style="font-weight: 800; font-size: 1.4rem; color: #ffffff;">FleetRent</span>
      </router-link>
    </header>

    <!-- Main Container -->
    <main style="flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px;">
      <div class="glass-panel reset-card fade-in-up" style="max-width: 440px; width: 100%; padding: 36px; border-radius: 20px; background: #ffffff;">
        <div style="text-align: center; margin-bottom: 24px;">
          <div style="width: 60px; height: 60px; background: #eff6ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; font-size: 28px; border: 2px solid #bfdbfe;">
            🔑
          </div>
          <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 6px;">Yeni Şifre Oluştur</h2>
          <p style="color: #64748b; font-size: 0.88rem;">
            Hesabınız için lütfen yeni bir şifre belirleyin.
          </p>
        </div>

        <div v-if="success" class="alert alert-success" style="padding: 16px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; color: #065f46; margin-bottom: 20px; text-align: center;">
          <p style="font-weight: 700; margin-bottom: 8px;">✅ Şifreniz Değiştirildi!</p>
          <p style="font-size: 0.88rem; margin-bottom: 16px;">Yeni şifrenizle hemen giriş yapabilirsiniz.</p>
          <router-link to="/login" class="btn btn-blue" style="display: block; text-decoration: none; padding: 12px; text-align: center;">
            Giriş Yap ➔
          </router-link>
        </div>

        <form v-else @submit.prevent="handleReset">
          <div v-if="errorMsg" class="alert alert-error" style="padding: 12px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px; color: #991b1b; font-size: 0.88rem; margin-bottom: 20px;">
            ⚠️ {{ errorMsg }}
          </div>

          <div class="form-group" style="margin-bottom: 16px;">
            <label class="form-label">Yeni Şifre * (En az 6 karakter)</label>
            <input type="password" v-model="password" required minlength="6" class="form-input" placeholder="••••••••">
          </div>

          <div class="form-group" style="margin-bottom: 25px;">
            <label class="form-label">Yeni Şifre (Tekrar) *</label>
            <input type="password" v-model="passwordConfirm" required minlength="6" class="form-input" placeholder="••••••••">
          </div>

          <button type="submit" class="btn btn-blue" style="width: 100%; padding: 14px;" :disabled="loading">
            {{ loading ? 'Şifre Güncelleniyor...' : 'Şifremi Güncelle ve Kaydet' }}
          </button>
        </form>

        <div style="margin-top: 24px; text-align: center;">
          <router-link to="/login" style="color: #64748b; text-decoration: none; font-size: 0.88rem; font-weight: 500;">
            ← Giriş Ekranına Dön
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const token = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const success = ref(false)
const errorMsg = ref('')

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    errorMsg.value = 'Geçersiz veya eksik şifre sıfırlama bağlantısı.'
  }
})

const handleReset = async () => {
  if (password.value !== passwordConfirm.value) {
    errorMsg.value = 'Şifreler birbiriyle eşleşmiyor!'
    return
  }

  if (password.value.length < 6) {
    errorMsg.value = 'Şifre en az 6 karakter olmalıdır.'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: token.value,
        password: password.value
      })
    })

    const data = await res.json()

    if (res.ok) {
      success.value = true
    } else {
      errorMsg.value = data.detail || 'Şifre sıfırlanırken bir hata oluştu.'
    }
  } catch (err) {
    console.error('Reset password error:', err)
    errorMsg.value = 'Sunucuya bağlanılamadı. Lütfen tekrar deneyin.'
  } finally {
    loading.value = false
  }
}
</script>
