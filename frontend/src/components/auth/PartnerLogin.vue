<template>
  <div class="partner-login" :class="`partner-login--${account}`">
    <header class="hero-dark-bg partner-login__header">
      <router-link to="/" class="nav-logo">
        <img
          class="brand-logo-image brand-logo-image--dark"
          src="/fleetrent-logo.jpeg"
          alt="FleetRent"
        />
        <span class="brand-logo-role">{{ profile.label }}</span>
      </router-link>
    </header>
    <main>
      <section class="glass-panel partner-login__card">
        <div class="nav-logo partner-login__brand">
          <img class="brand-logo-image" src="/fleetrent-logo.jpeg" alt="FleetRent" />
          <span class="brand-logo-role">{{ profile.label }}</span>
        </div>
        <h1>{{ profile.label }} Girişi</h1>
        <p class="partner-login__description">
          <strong>{{ profile.description }}</strong> için e-posta ve şifre ile portal girişi.
        </p>

        <UiAlert v-if="error" class="partner-login__error">{{ error }}</UiAlert>
        <section v-if="verificationRequired" class="partner-login__verification">
          <p>E-posta adresinizin doğrulanması gerekiyor.</p>
          <UiButton
            type="button"
            variant="secondary"
            :loading="resendLoading"
            @click="resendVerification"
            >Doğrulama E-postasını Tekrar Gönder</UiButton
          >
          <UiAlert v-if="resendMessage" tone="info">{{ resendMessage }}</UiAlert>
        </section>

        <form v-if="!showForgot" @submit.prevent="handleLogin">
          <UiField :label="`${profile.label} E-posta Adresi`" input-id="partner-email">
            <input
              id="partner-email"
              v-model="email"
              type="email"
              autocomplete="username"
              required
              :placeholder="profile.placeholder"
            />
          </UiField>
          <UiField label="Şifre" input-id="partner-password">
            <input
              id="partner-password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
            />
          </UiField>
          <UiButton type="button" variant="ghost" class="partner-login__forgot" @click="openForgot"
            >Şifremi Unuttum?</UiButton
          >
          <UiButton
            type="submit"
            variant="primary"
            :loading="loading"
            class="partner-login__submit"
            >{{ loading ? 'Giriş Yapılıyor…' : `${profile.label} Portalına Giriş Yap ➔` }}</UiButton
          >
        </form>

        <section v-else>
          <h2>Şifremi Unuttum</h2>
          <UiAlert v-if="forgotSuccess" tone="success">{{ forgotSuccess }}</UiAlert>
          <form v-else @submit.prevent="handleForgotPassword">
            <UiField label="E-posta Adresi" input-id="partner-forgot-email">
              <input
                id="partner-forgot-email"
                v-model="forgotEmail"
                type="email"
                autocomplete="email"
                required
                :placeholder="profile.placeholder"
              />
            </UiField>
            <UiButton type="submit" variant="primary" :loading="forgotLoading"
              >Sıfırlama Bağlantısı Gönder</UiButton
            >
          </form>
          <UiButton type="button" variant="ghost" @click="showForgot = false"
            >← Girişe Dön</UiButton
          >
        </section>

        <nav aria-label="Diğer giriş seçenekleri" class="partner-login__links">
          <router-link to="/login">← Müşteri Portalı Girişine Dön</router-link>
          <router-link :to="profile.alternativePath">{{ profile.alternativeLabel }}</router-link>
          <router-link :to="`/register/${account}`"
            >{{ profile.label }} hesabı oluştur →</router-link
          >
        </nav>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../../api/http.js'
import { savePartnerSession } from '../../api/partnerSession.js'
import { UiAlert, UiButton, UiField } from '../ui/index.js'

const props = defineProps({
  account: {
    type: String,
    required: true,
    validator: (value) => ['supplier', 'service'].includes(value),
  },
})
const profiles = {
  supplier: {
    label: 'Tedarikçi',
    description: 'Araba sağlayıcı ve kiralama firmaları',
    placeholder: 'tedarikci@sirket.com',
    portal: '/supplier-portal',
    alternativePath: '/service-login',
    alternativeLabel: 'Servis Girişine Git (Bakım, Lastik & Oto Kurtarma) →',
  },
  service: {
    label: 'Servis',
    description: 'Bakım/Onarım, Lastik Hizmetleri & Oto Kurtarma noktaları',
    placeholder: 'servis@sirket.com',
    portal: '/service-portal',
    alternativePath: '/supplier-login',
    alternativeLabel: 'Tedarikçi Girişine Git (Araba Sağlayıcı & Kiralama) →',
  },
}
const profile = computed(() => profiles[props.account])
const router = useRouter()
const email = ref(''),
  password = ref(''),
  loading = ref(false),
  error = ref('')
const showForgot = ref(false),
  forgotEmail = ref(''),
  forgotLoading = ref(false),
  forgotSuccess = ref('')
const verificationRequired = ref(false),
  resendLoading = ref(false),
  resendMessage = ref('')
const post = (path, body) => apiRequest(path, { method: 'POST', body })

function openForgot() {
  error.value = ''
  forgotEmail.value = email.value
  showForgot.value = true
}

async function handleLogin() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  verificationRequired.value = false
  try {
    const data = await post(`/api/${props.account}/login`, {
      email: email.value,
      password: password.value,
    })
    savePartnerSession(data, email.value)
    await router.push(profile.value.portal)
  } catch (cause) {
    verificationRequired.value = cause.status === 403 && cause.message.includes('doğrulanmadı')
    error.value = cause.status ? cause.message : 'Sunucuya bağlanılamadı. Lütfen tekrar deneyin.'
  } finally {
    loading.value = false
  }
}

async function handleForgotPassword() {
  if (forgotLoading.value) return
  forgotLoading.value = true
  error.value = ''
  try {
    const data = await post('/api/auth/forgot-password', { email: forgotEmail.value })
    forgotSuccess.value =
      data.message || 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.'
  } catch (cause) {
    error.value = cause.status ? cause.message : 'Sunucuya bağlanılamadı.'
  } finally {
    forgotLoading.value = false
  }
}

async function resendVerification() {
  if (resendLoading.value) return
  resendLoading.value = true
  resendMessage.value = ''
  try {
    const data = await post('/api/auth/resend-verification', {
      email: email.value,
      account_type: props.account,
    })
    resendMessage.value = data.message || 'Doğrulama e-postası gönderildi.'
  } catch (cause) {
    resendMessage.value = cause.status ? cause.message : 'Sunucuya bağlanılamadı.'
  } finally {
    resendLoading.value = false
  }
}
</script>

<style scoped>
.partner-login {
  --primary: #10b981;
  --partner-border: #a7f3d0;
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  color: #0f172a;
}
.partner-login--service {
  --primary: #2563eb;
  --partner-border: #bfdbfe;
}
.partner-login__header {
  padding: 16px 8%;
  min-height: 60px;
  display: flex;
  align-items: center;
}
.partner-login main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}
.partner-login__card {
  max-width: 480px;
  width: 100%;
  padding: 40px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgb(0 0 0 / 6%);
  border: 1px solid #e2e8f0;
}
.partner-login__brand {
  justify-content: center;
  margin-bottom: 25px;
}
.partner-login h1 {
  font-size: 24px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 8px;
}
.partner-login h2 {
  font-size: 18px;
  margin-bottom: 16px;
}
.partner-login__description {
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
  margin-bottom: 25px;
}
.partner-login form {
  display: grid;
  gap: 18px;
}
.partner-login label {
  display: grid;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.partner-login input {
  width: 100%;
  height: 48px;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font: inherit;
  box-sizing: border-box;
}
.partner-login__submit {
  width: 100%;
}
.partner-login__forgot {
  justify-self: end;
  padding: 0;
  font-size: 13px;
}
.partner-login__error {
  padding: 12px;
  background: #fff1f2;
  color: #be123c;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow-wrap: anywhere;
}
.partner-login__verification {
  padding: 12px;
  border: 1px solid var(--partner-border);
  border-radius: 8px;
  margin-bottom: 18px;
  font-size: 13px;
}
.partner-login__links {
  display: grid;
  gap: 12px;
  text-align: center;
  margin-top: 25px;
  font-size: 13px;
}
.partner-login__links a {
  color: var(--primary);
  text-decoration: none;
}
@media (max-width: 520px) {
  .partner-login__card {
    padding: 24px;
  }
  .partner-login main {
    padding: 24px 14px;
  }
}
</style>
