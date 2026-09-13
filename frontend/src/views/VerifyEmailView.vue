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
      <div class="glass-panel verify-card fade-in-up" style="max-width: 480px; width: 100%; padding: 40px 30px; border-radius: 24px; background: #ffffff; text-align: center;">
        
        <div v-if="loading" style="padding: 30px 0;">
          <div style="width: 50px; height: 50px; border: 4px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px auto;"></div>
          <h3 style="font-weight: 700; color: #0f172a;">E-posta Adresiniz Doğrulanıyor...</h3>
          <p style="color: #64748b; font-size: 0.9rem;">Lütfen bekleyiniz, işleminiz tamamlanıyor.</p>
        </div>

        <div v-else-if="success">
          <div style="width: 72px; height: 72px; background: #ecfdf5; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto; font-size: 36px; border: 2px solid #a7f3d0;">
            🎉
          </div>
          <h2 style="font-size: 1.5rem; font-weight: 800; color: #065f46; margin-bottom: 12px;">E-posta Adresiniz Doğrulanmıştır!</h2>
          <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px;">
            Tebrikler! FleetRent hesabınız başarıyla doğrulandı. Artık araç kiralama, teklif oluşturma ve filo yönetimi işlemlerinize kesintisiz devam edebilirsiniz.
          </p>

          <button @click="goToDashboard" class="btn btn-blue" style="width: 100%; padding: 14px; font-weight: 700; border-radius: 12px;">
            Filo Yönetim Paneline Git ➔
          </button>
        </div>

        <div v-else>
          <div style="width: 72px; height: 72px; background: #fef2f2; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto; font-size: 36px; border: 2px solid #fecaca;">
            ❌
          </div>
          <h2 style="font-size: 1.4rem; font-weight: 800; color: #991b1b; margin-bottom: 12px;">Doğrulama Başarısız</h2>
          <p style="color: #64748b; font-size: 0.92rem; margin-bottom: 24px;">
            {{ errorMsg || 'Geçersiz veya süresi dolmuş e-posta doğrulama bağlantısı.' }}
          </p>

          <router-link to="/login" class="btn btn-blue" style="display: block; text-decoration: none; padding: 14px; font-weight: 700; border-radius: 12px; text-align: center;">
            Giriş Ekranına Dön
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

const loading = ref(true)
const success = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  const token = route.query.token || ''
  if (!token) {
    loading.value = false
    errorMsg.value = 'Doğrulama kodu bulunamadı.'
    return
  }

  try {
    const res = await fetch(`/api/auth/verify-email/${token}`, {
      method: 'GET'
    })

    const data = await res.json()

    if (res.ok) {
      success.value = true
      localStorage.setItem('fleetcar_user_verified', 'true')
      
      const custStr = localStorage.getItem('fleet_customer')
      if (custStr) {
        try {
          const cust = JSON.parse(custStr)
          cust.is_email_verified = true
          localStorage.setItem('fleet_customer', JSON.stringify(cust))
        } catch (e) {}
      }
    } else {
      errorMsg.value = data.detail || 'Doğrulama başarısız oldu.'
    }
  } catch (err) {
    console.error('Verify email error:', err)
    errorMsg.value = 'Sunucuya bağlanılamadı.'
  } finally {
    loading.value = false
  }
})

const goToDashboard = () => {
  const token = localStorage.getItem('fleetcar_token')
  if (token) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
