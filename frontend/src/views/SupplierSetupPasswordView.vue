<template>
  <div style="min-height: 100vh; background: #f8fafc; display: flex; flex-direction: column;">
    <!-- Header -->
    <header class="hero-dark-bg" style="padding: 16px 8%; text-align: left; height: 60px; display: flex; align-items: center;">
      <router-link to="/" class="nav-logo" style="text-decoration: none;">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #7c3aed, #db2777); border-radius: 8px;">F</div>
        <span style="font-weight: 800; font-size: 1.4rem; color: #ffffff;">FleetCar <span style="color: #c084fc; font-size: 0.85rem; font-weight: 600;">Tedarikçi & Servis Portalı</span></span>
      </router-link>
    </header>

    <!-- Main Content -->
    <main style="flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px;">
      <!-- Loading State -->
      <div v-if="verifying" class="glass-panel auth-card fade-in-up text-center" style="max-width: 480px; width: 100%; padding: 40px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.06);">
        <div style="font-size: 2.5rem; margin-bottom: 15px;">⏳</div>
        <h3 style="color: #0f172a; margin-bottom: 8px;">Davetiye Kontrol Ediliyor...</h3>
        <p style="color: #64748b; font-size: 0.9rem;">Lütfen bekleyin, davet bağlantınız doğrulanıyor.</p>
      </div>

      <!-- Invalid Token / Error State -->
      <div v-else-if="tokenError" class="glass-panel auth-card fade-in-up text-center" style="max-width: 480px; width: 100%; padding: 40px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border-top: 4px solid #ef4444;">
        <div style="font-size: 3rem; margin-bottom: 15px;">❌</div>
        <h2 style="font-size: 1.4rem; color: #0f172a; font-weight: 800; margin-bottom: 10px;">Geçersiz Davet Bağlantısı</h2>
        <p style="color: #64748b; font-size: 0.95rem; line-height: 1.5; margin-bottom: 25px;">
          {{ tokenError }}
        </p>
        <router-link to="/supplier-login" class="btn btn-block" style="background: linear-gradient(135deg, #7c3aed, #db2777); color: #fff; padding: 12px; text-decoration: none; border-radius: 10px; font-weight: 700; display: inline-block;">
          Tedarikçi Giriş Sayfasına Git
        </router-link>
      </div>

      <!-- Success State -->
      <div v-else-if="success" class="glass-panel auth-card fade-in-up text-center" style="max-width: 480px; width: 100%; padding: 40px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border-top: 4px solid #10b981;">
        <div style="font-size: 3.5rem; margin-bottom: 15px;">🎉</div>
        <h2 style="font-size: 1.5rem; color: #0f172a; font-weight: 800; margin-bottom: 10px;">Şifreniz Başarıyla Oluşturuldu!</h2>
        <p style="color: #64748b; font-size: 0.95rem; line-height: 1.5; margin-bottom: 25px;">
          Tedarikçi / servis portalı hesabınız aktifleştirildi. Belirlediğiniz şifre ile hemen portalınıza giriş yapabilirsiniz.
        </p>
        
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <router-link to="/supplier-login" class="btn btn-block" style="background: linear-gradient(135deg, #10b981, #059669); color: #fff; padding: 14px; text-decoration: none; border-radius: 10px; font-weight: 700; display: block; text-align: center; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
            🔑 Tedarikçi Girişi Yap ➔
          </router-link>
          
          <router-link to="/service-login" class="btn btn-block" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; padding: 12px; text-decoration: none; border-radius: 10px; font-weight: 700; display: block; text-align: center;">
            🔧 Servis Girişi Yap (Bakım & Lastik) ➔
          </router-link>
        </div>
      </div>

      <!-- Form Setup State -->
      <div v-else class="glass-panel auth-card fade-in-up" style="max-width: 480px; width: 100%; padding: 40px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
        <div class="nav-logo" style="justify-content: center; margin-bottom: 20px;">
          <div class="nav-logo-icon" style="background: linear-gradient(135deg, #7c3aed, #db2777); border-radius: 8px;">F</div>
          <span style="font-size: 1.6rem; font-weight: 800; color: #0f172a;">FleetCar</span>
        </div>

        <div style="background: rgba(124, 58, 237, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(124, 58, 237, 0.15); margin-bottom: 25px; text-align: center;">
          <div style="font-size: 0.8rem; color: #7c3aed; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Davetli Firma</div>
          <h3 style="font-size: 1.2rem; color: #0f172a; margin: 0; font-weight: 800;">{{ supplierName }}</h3>
          <div style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">✉️ {{ supplierEmail }}</div>
        </div>

        <h2 style="font-size: 1.4rem; text-align: center; margin-bottom: 6px; color: #0f172a; font-weight: 800;">Şifrenizi Oluşturun</h2>
        <p style="color: #64748b; font-size: 0.88rem; text-align: center; margin-bottom: 25px;">
          Portala güvenle giriş yapabilmek için lütfen yeni bir şifre belirleyin.
        </p>

        <form @submit.prevent="handleSetPassword">
          <div class="form-group" style="margin-bottom: 18px;">
            <label for="new-password" class="form-label" style="font-weight: 600; color: #334155; font-size: 0.88rem;">Yeni Şifre *</label>
            <input 
              id="new-password"
              name="new-password"
              type="password" 
              v-model="password" 
              required 
              minlength="6"
              class="form-input" 
              placeholder="En az 6 karakter"
              style="height: 48px;"
            >
          </div>

          <div class="form-group" style="margin-bottom: 25px;">
            <label for="confirm-password" class="form-label" style="font-weight: 600; color: #334155; font-size: 0.88rem;">Şifre Tekrarı *</label>
            <input 
              id="confirm-password"
              name="confirm-password"
              type="password" 
              v-model="confirmPassword" 
              required 
              minlength="6"
              class="form-input" 
              placeholder="Şifrenizi tekrar girin"
              style="height: 48px;"
            >
          </div>

          <button type="submit" class="btn btn-block" :disabled="submitting" style="background: linear-gradient(135deg, #7c3aed, #db2777); color: #ffffff; padding: 14px; font-size: 1rem; font-weight: 700; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3); width: 100%;">
            {{ submitting ? 'Şifre Kaydediliyor...' : 'Şifreyi Kaydet ve Aktifleştir ➔' }}
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const token = ref(route.query.token || '')

const verifying = ref(true)
const tokenError = ref('')
const supplierName = ref('')
const supplierEmail = ref('')

const password = ref('')
const confirmPassword = ref('')
const submitting = ref(false)
const success = ref(false)

onMounted(async () => {
  if (!token.value) {
    verifying.value = false
    tokenError.value = 'Davet bağlantısında eksik veya geçersiz parametre (token) bulunamadı.'
    return
  }

  try {
    const res = await fetch(`/api/supplier/verify-token/${token.value}`)
    if (res.ok) {
      const data = await res.json()
      supplierName.value = data.supplier_name
      supplierEmail.value = data.email
    } else {
      const errData = await res.json().catch(() => ({}))
      tokenError.value = errData.detail || 'Geçersiz veya daha önce kullanılmış davet bağlantısı.'
    }
  } catch (err) {
    console.error('Verify token error:', err)
    tokenError.value = 'Sunucuya bağlanılamadı. Lütfen internet bağlantınızı kontrol edin.'
  } finally {
    verifying.value = false
  }
})

const handleSetPassword = async () => {
  if (!password.value || password.value.length < 6) {
    alert('Lütfen en az 6 karakterden oluşan bir şifre giriniz.')
    return
  }

  if (password.value !== confirmPassword.value) {
    alert('Şifreler birbiriyle uyuşmuyor! Lütfen kontrol edin.')
    return
  }

  submitting.value = true
  try {
    const res = await fetch('/api/supplier/set-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: token.value,
        password: password.value
      })
    })

    if (res.ok) {
      success.value = true
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Şifre kaydedilirken bir hata oluştu.')
    }
  } catch (err) {
    console.error('Set password error:', err)
    alert('Sunucuya bağlanılamadı.')
  } finally {
    submitting.value = false
  }
}
</script>
