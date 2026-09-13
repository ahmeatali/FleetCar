<template>
  <div v-if="showModal" class="verification-overlay">
    <div class="verification-card fade-in-up">
      <div class="icon-wrapper">
        <span class="warning-icon">✉️</span>
      </div>

      <h2 class="title">E-posta Adresinizi Doğrulayın</h2>
      
      <p class="description">
        FleetRent platformundaki tüm özellikleri kullanabilmek ve işlemlerinizi tamamlayabilmek için
        <strong style="color: #2563eb;">{{ userEmail }}</strong> adresinize gönderdiğimiz doğrulama bağlantısına tıklamanız gerekmektedir.
      </p>

      <div class="info-box">
        <span>⚠️ E-posta adresiniz doğrulanana kadar sistemdeki diğer bölümlere erişiminiz kısıtlanmıştır.</span>
      </div>

      <div v-if="successMsg" class="status-alert success-alert">
        ✅ {{ successMsg }}
      </div>
      <div v-if="errMsg" class="status-alert error-alert">
        ❌ {{ errMsg }}
      </div>

      <div v-if="verifyUrl" class="direct-link-box" style="margin-bottom: 20px; background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px; border-radius: 12px; text-align: center;">
        <p style="font-size: 0.82rem; color: #1e40af; margin-bottom: 6px; font-weight: 600;">E-posta beklemek istemiyorsanız doğrudan aşağıdaki butonla doğrulayabilirsiniz:</p>
        <a :href="verifyUrl" class="btn btn-primary" style="display: block; text-decoration: none; padding: 10px; font-size: 0.88rem; font-weight: 700;">
          ⚡ Hemen Doğrula ve Devam Et ➔
        </a>
      </div>

      <div class="action-buttons">
        <button @click="handleResendEmail" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Gönderiliyor...' : 'Doğrulama E-postasını Tekrar Gönder' }}
        </button>
        <button @click="handleLogout" class="btn btn-secondary">
          Çıkış Yap
        </button>
      </div>

      <p class="spam-hint">
        E-posta kutunuzda göremiyorsanız lütfen <strong>Spam / Önemsiz</strong> klasörünü de kontrol ediniz.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const showModal = ref(false)
const userEmail = ref('')
const loading = ref(false)
const successMsg = ref('')
const errMsg = ref('')
const verifyUrl = ref('')

const checkVerificationStatus = () => {
  // Exclude auth/public routes from blocking modal
  const publicRoutes = ['/', '/login', '/admin-login', '/supplier-login', '/service-login', '/setup-password', '/reset-password', '/verify-email']
  if (publicRoutes.includes(route.path)) {
    showModal.value = false
    return
  }

  const token = localStorage.getItem('fleetcar_token') || localStorage.getItem('fleetcar_supplier_token')
  const email = localStorage.getItem('fleetcar_user_email') || localStorage.getItem('fleetcar_supplier_email')
  const customerStr = localStorage.getItem('fleet_customer')
  const supplierStr = localStorage.getItem('fleet_supplier')

  if (!token || !email) {
    showModal.value = false
    return
  }

  userEmail.value = email

  try {
    if (customerStr) {
      const cust = JSON.parse(customerStr)
      if (cust && (cust.is_email_verified === false || cust.is_email_verified === 0)) {
        showModal.value = true
        return
      }
    }

    if (supplierStr) {
      const supp = JSON.parse(supplierStr)
      if (supp && (supp.is_email_verified === false || supp.is_email_verified === 0)) {
        showModal.value = true
        return
      }
    }
  } catch (e) {
    console.error('Failed parsing user data', e)
  }

  // Check explicit item
  const isVerifiedItem = localStorage.getItem('fleetcar_user_verified')
  if (isVerifiedItem === 'false') {
    showModal.value = true
  } else {
    showModal.value = false
  }
}

const handleResendEmail = async () => {
  if (!userEmail.value) return
  loading.value = true
  successMsg.value = ''
  errMsg.value = ''

  try {
    const res = await fetch('/api/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: userEmail.value })
    })

    const data = await res.json()
    if (res.ok) {
      if (data.status === 'warning') {
        errMsg.value = data.message
      } else {
        successMsg.value = data.message || 'Doğrulama e-postası başarıyla gönderildi!'
      }
      if (data.verify_url) {
        verifyUrl.value = data.verify_url
      }
    } else {
      errMsg.value = data.detail || 'E-posta gönderilirken bir hata oluştu.'
    }
  } catch (err) {
    console.error('Resend verification error:', err)
    errMsg.value = 'Sunucuya bağlanılamadı.'
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  localStorage.removeItem('fleetcar_token')
  localStorage.removeItem('fleetcar_customer_id')
  localStorage.removeItem('fleetcar_customer_name')
  localStorage.removeItem('fleetcar_supplier_token')
  localStorage.removeItem('fleetcar_supplier_id')
  localStorage.removeItem('fleetcar_supplier_name')
  localStorage.removeItem('fleetcar_supplier_type')
  localStorage.removeItem('fleetcar_supplier_email')
  localStorage.removeItem('fleetcar_user_email')
  localStorage.removeItem('fleetcar_user_verified')
  localStorage.removeItem('fleet_customer')
  localStorage.removeItem('fleet_supplier')
  showModal.value = false
  router.push('/login')
}

onMounted(() => {
  checkVerificationStatus()
})

watch(() => route.path, () => {
  checkVerificationStatus()
})
</script>

<style scoped>
.verification-overlay {
  position: fixed;
  inset: 0;
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(12px);
  padding: 20px;
  pointer-events: auto;
}

.verification-card {
  max-width: 480px;
  width: 100%;
  background: #ffffff;
  border-radius: 24px;
  padding: 36px 30px;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
  border: 1px solid #e2e8f0;
}

.icon-wrapper {
  width: 72px;
  height: 72px;
  background: #eff6ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px auto;
  border: 2px solid #bfdbfe;
}

.warning-icon {
  font-size: 34px;
}

.title {
  font-size: 1.45rem;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 12px;
}

.description {
  color: #475569;
  font-size: 0.93rem;
  line-height: 1.6;
  margin-bottom: 20px;
}

.info-box {
  background: #fffbeb;
  border: 1px solid #fef08a;
  color: #b45309;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 0.82rem;
  font-weight: 600;
  margin-bottom: 20px;
  text-align: left;
}

.status-alert {
  padding: 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  margin-bottom: 16px;
}

.success-alert {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.error-alert {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.btn {
  padding: 14px 20px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45);
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.spam-hint {
  font-size: 0.78rem;
  color: #94a3b8;
  margin: 0;
}

.fade-in-up {
  animation: fadeInUp 0.3s ease-out forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
