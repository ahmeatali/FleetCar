<template>
  <div class="registration-page">
    <header class="hero-dark-bg registration-header">
      <router-link to="/" class="nav-logo"><img class="brand-logo-image brand-logo-image--dark" src="/fleetrent-logo.jpeg" alt="FleetRent" /></router-link>
    </header>
    <main class="registration-main">
      <section class="registration-card">
        <router-link :to="loginPath" class="back-link">← Giriş sayfasına dön</router-link>
        <div class="registration-brand"><img class="brand-logo-image" src="/fleetrent-logo.jpeg" alt="FleetRent" /></div>
        <template v-if="!submitted">
          <h1>{{ isService ? 'Servis hesabı oluştur' : 'Tedarikçi hesabı oluştur' }}</h1>
          <p class="intro">Hesabınızı oluşturun. Giriş yapmadan önce e-posta adresinizi doğrulamanız gerekir.</p>
          <form @submit.prevent="register">
            <label>Firma adı<input v-model.trim="form.name" required autocomplete="organization" /></label>
            <label>E-posta adresi<input v-model.trim="form.email" required type="email" autocomplete="email" /></label>
            <label v-if="isService">Hizmet alanı
              <select v-model="form.service_type" required>
                <option value="servis">Servis / Bakım</option>
                <option value="lastik">Lastik</option>
                <option value="yol_yardim">Yol Yardım</option>
              </select>
            </label>
            <label>Telefon<input v-model.trim="form.phone" type="tel" autocomplete="tel" /></label>
            <label>Şifre <span>(en az 8 karakter)</span><input v-model="form.password" required type="password" minlength="8" autocomplete="new-password" /></label>
            <p v-if="error" class="notice error">{{ error }}</p>
            <button class="primary" :disabled="saving">{{ saving ? 'Hesap oluşturuluyor…' : 'Hesap oluştur' }}</button>
          </form>
        </template>
        <template v-else>
          <h1>E-postanızı doğrulayın</h1>
          <p class="intro">{{ emailMessage }}</p>
          <p class="email-address">{{ form.email }}</p>
          <p v-if="resendMessage" class="notice" :class="resendOk ? 'success' : 'error'">{{ resendMessage }}</p>
          <button class="primary" :disabled="resending" @click="resend">{{ resending ? 'Gönderiliyor…' : 'Doğrulama e-postasını yeniden gönder' }}</button>
          <router-link class="secondary" :to="loginPath">Giriş sayfasına dön</router-link>
        </template>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isService = computed(() => route.params.accountType === 'service')
const accountType = computed(() => isService.value ? 'service' : 'supplier')
const loginPath = computed(() => isService.value ? '/service-login' : '/supplier-login')
const form = reactive({ name: '', email: '', password: '', phone: '', service_type: 'servis' })
const saving = ref(false)
const submitted = ref(false)
const emailMessage = ref('')
const error = ref('')
const resending = ref(false)
const resendMessage = ref('')
const resendOk = ref(false)

async function register() {
  saving.value = true
  error.value = ''
  try {
    const response = await fetch('/api/supplier/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, account_type: accountType.value, service_type: isService.value ? form.service_type : null })
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || 'Kayıt oluşturulamadı.')
    submitted.value = true
    emailMessage.value = data.email_sent
      ? 'Doğrulama bağlantısını e-posta adresinize gönderdik. Bağlantıya tıkladıktan sonra giriş yapabilirsiniz.'
      : 'Hesabınız oluşturuldu ancak doğrulama e-postası gönderilemedi. Aşağıdaki düğmeyle yeniden deneyin.'
  } catch (err) {
    error.value = err.message || 'Sunucuya bağlanılamadı.'
  } finally {
    saving.value = false
  }
}

async function resend() {
  resending.value = true
  resendMessage.value = ''
  try {
    const response = await fetch('/api/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, account_type: accountType.value })
    })
    const data = await response.json().catch(() => ({}))
    resendOk.value = response.ok && data.email_sent !== false
    resendMessage.value = data.message || data.detail || (resendOk.value ? 'Doğrulama e-postası gönderildi.' : 'E-posta gönderilemedi.')
  } catch {
    resendOk.value = false
    resendMessage.value = 'Sunucuya bağlanılamadı.'
  } finally {
    resending.value = false
  }
}
</script>

<style scoped>
.registration-page{min-height:100vh;background:#f8fafc;display:flex;flex-direction:column}.registration-header{padding:16px 8%;height:60px;display:flex;align-items:center}.registration-main{flex:1;display:flex;align-items:center;justify-content:center;padding:36px 20px}.registration-card{width:min(100%,480px);padding:36px;background:#fff;border:1px solid #e2e8f0;border-radius:20px;box-shadow:0 10px 30px #0f172a0f}.back-link{display:inline-block;margin-bottom:20px;color:#2563eb;text-decoration:none;font-size:.88rem;font-weight:600}.registration-brand{display:flex;justify-content:center;margin-bottom:18px}.registration-card h1{text-align:center;color:#0f172a;font-size:1.45rem;margin:0 0 8px}.intro{text-align:center;color:#64748b;font-size:.9rem;line-height:1.55;margin:0 0 22px}.registration-card form{display:grid;gap:14px}.registration-card label{display:grid;gap:6px;color:#334155;font-size:.88rem;font-weight:600}.registration-card label span{color:#64748b;font-weight:400}.registration-card input,.registration-card select{height:46px;padding:0 12px;border:1px solid #cbd5e1;border-radius:9px;font:inherit;color:#0f172a;background:#fff}.primary,.secondary{display:block;width:100%;margin-top:18px;padding:13px;border-radius:10px;text-align:center;font:inherit;font-weight:700;text-decoration:none;cursor:pointer}.primary{border:0;background:#2563eb;color:white}.primary:disabled{opacity:.6;cursor:wait}.secondary{box-sizing:border-box;border:1px solid #cbd5e1;color:#334155}.email-address{text-align:center;font-weight:700;color:#0f172a}.notice{padding:12px;border-radius:9px;font-size:.88rem;line-height:1.5}.success{background:#ecfdf5;color:#065f46}.error{background:#fef2f2;color:#991b1b}
</style>
