<template>
  <main class="invitation-page">
    <section class="invitation-card">
      <router-link to="/"><img src="/fleetrent-logo.jpeg" alt="FleetRent" /></router-link>
      <h1>FleetRent Ekip Daveti</h1>
      <UiAlert v-if="loading" tone="info">Davet kontrol ediliyor…</UiAlert
      ><UiAlert v-if="error" tone="error">{{ error }}</UiAlert
      ><template v-if="details && !success"
        ><p>Merhaba {{ details.name }}, ekibinize katılmak için şifrenizi oluşturun.</p>
        <form @submit.prevent="accept">
          <UiField
            >Şifre<input
              v-model="password"
              type="password"
              autocomplete="new-password"
              minlength="10"
              maxlength="200"
              required /></UiField
          ><UiField
            >Şifre Tekrar<input
              v-model="confirmation"
              type="password"
              autocomplete="new-password"
              minlength="10"
              maxlength="200"
              required /></UiField
          ><UiButton class="btn btn-blue" :disabled="saving">{{
            saving ? 'Kaydediliyor…' : 'Şifremi Oluştur ve Katıl'
          }}</UiButton>
        </form></template
      ><template v-if="success"
        ><UiAlert tone="success"
          >Hesabınız hazır. E-posta adresiniz ve oluşturduğunuz şifreyle giriş
          yapabilirsiniz.</UiAlert
        ><router-link
          :to="details.portal === 'supplier' ? '/supplier-login' : '/login'"
          class="btn btn-blue"
          >Giriş Yap</router-link
        ></template
      >
      <p v-if="!loading && !details" class="invitation-note">
        Yeni davet bağlantısı için şirket hesabı sahibinizle iletişime geçin.
      </p>
    </section>
  </main>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { UiAlert, UiButton, UiField } from '../components/ui/index.js'
import { apiRequest } from '../api/http.js'
const loading = ref(true),
  saving = ref(false),
  error = ref(''),
  details = ref(null),
  success = ref(false),
  password = ref(''),
  confirmation = ref('')
let token = new URLSearchParams(window.location.hash.slice(1)).get('token') || ''
onMounted(async () => {
  try {
    if (!token) throw Error('Davet bağlantısında geçerli bir anahtar bulunamadı.')
    details.value = await apiRequest('/api/team/invitation/inspect', {
      method: 'POST',
      body: { token },
    })
  } catch (failure) {
    error.value = failure.message
  } finally {
    loading.value = false
  }
})
async function accept() {
  error.value = ''
  if (password.value !== confirmation.value) {
    error.value = 'Şifreler eşleşmiyor.'
    return
  }
  saving.value = true
  try {
    await apiRequest('/api/team/invitation/accept', {
      method: 'POST',
      body: { token, password: password.value },
    })
    success.value = true
    token = ''
    password.value = ''
    confirmation.value = ''
    window.history.replaceState(null, '', '/accept-invitation')
  } catch (failure) {
    error.value = failure.message
  } finally {
    saving.value = false
  }
}
</script>
<style scoped>
.invitation-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f7fe;
  padding: 24px;
  box-sizing: border-box;
}
.invitation-card {
  background: white;
  border: 1px solid #e1eaf7;
  border-radius: 18px;
  padding: 35px;
  width: min(460px, 100%);
  box-shadow: 0 20px 60px #16396112;
}
.invitation-card img {
  width: 180px;
  margin-bottom: 24px;
}
.invitation-card h1 {
  font-size: 24px;
  color: #0d284b;
}
.invitation-card p {
  color: #71849f;
  line-height: 1.7;
}
.invitation-card :deep(label) {
  display: grid;
  gap: 8px;
  margin: 18px 0;
}
.invitation-card input {
  width: 100%;
  box-sizing: border-box;
  padding: 13px;
  border: 1px solid #cfdbed;
  border-radius: 8px;
}
.invitation-card .btn {
  width: 100%;
  margin-top: 18px;
  text-align: center;
}
</style>
