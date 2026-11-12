<template>
  <div ref="root" class="pm-root">
    <button
      type="button"
      class="sw-profile pm-trigger"
      :aria-expanded="open"
      aria-haspopup="menu"
      @click="open = !open"
    >
      <span>{{ initials }}</span>
      <div>
        <strong>{{ name }}</strong
        ><small>{{ subtitle }}</small>
      </div>
      <i aria-hidden="true">⌄</i>
    </button>
    <div v-if="open" class="pm-menu" role="menu" @keydown.esc="open = false">
      <div class="pm-head">
        <strong>{{ name }}</strong
        ><small>{{ email }}</small>
      </div>
      <button type="button" role="menuitem" @click="openPassword">
        <span>🔒</span>Şifre Değiştir
      </button>
      <router-link
        v-if="role === 'owner'"
        role="menuitem"
        to="/supplier-portal/settings"
        @click="open = false"
        ><span>⚙</span>Ayarlar</router-link
      >
      <router-link
        v-if="role === 'owner'"
        role="menuitem"
        to="/supplier-portal/users"
        @click="open = false"
        ><span>👥</span>Kullanıcılar</router-link
      >
      <button type="button" role="menuitem" class="pm-logout" @click="logout">
        <span>⇥</span>Çıkış Yap
      </button>
    </div>

    <UiModal v-if="showPassword" class="sw-modal-overlay" :busy="saving" @close="closePassword">
      <section class="sw-form-modal pm-modal" aria-labelledby="pm-password-title">
        <h2 id="pm-password-title">Şifre Değiştir</h2>
        <p class="sw-muted">
          Yeni şifre en az 10 karakter olmalı. Şifreniz değişince diğer cihazlardaki oturumlarınız
          kapatılır; bu oturum açık kalır.
        </p>
        <UiAlert v-if="formError" tone="error">{{ formError }}</UiAlert>
        <UiAlert v-if="done" tone="success">Şifreniz güncellendi.</UiAlert>
        <form v-if="!done" @submit.prevent="savePassword">
          <UiField
            >Mevcut Şifre<input
              v-model="form.current"
              type="password"
              autocomplete="current-password"
              required
          /></UiField>
          <UiField
            >Yeni Şifre<input
              v-model="form.next"
              type="password"
              autocomplete="new-password"
              minlength="10"
              required
          /></UiField>
          <UiField
            >Yeni Şifre (Tekrar)<input
              v-model="form.repeat"
              type="password"
              autocomplete="new-password"
              minlength="10"
              required
          /></UiField>
          <div class="pm-actions">
            <button type="button" class="sw-button" :disabled="saving" @click="closePassword">
              Vazgeç</button
            ><button type="submit" class="sw-button primary" :disabled="saving">
              {{ saving ? 'Kaydediliyor…' : 'Şifreyi Güncelle' }}
            </button>
          </div>
        </form>
        <div v-else class="pm-actions">
          <button type="button" class="sw-button primary" @click="closePassword">Kapat</button>
        </div>
      </section>
    </UiModal>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UiAlert, UiField, UiModal } from './ui/index.js'
import { supplierApi } from '../utils/supplierApi'
import { clearSupplierSession } from '../api/partnerSession.js'

const props = defineProps({
  name: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  role: { type: String, default: 'viewer' },
})
const router = useRouter()
const root = ref(null),
  open = ref(false),
  showPassword = ref(false),
  saving = ref(false),
  done = ref(false),
  formError = ref('')
const form = reactive({ current: '', next: '', repeat: '' })
const email = localStorage.getItem('fleetcar_supplier_email') || ''
const initials = computed(() =>
  (props.name || 'T')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0])
    .join('')
    .toUpperCase(),
)

function onDocumentClick(event) {
  if (open.value && root.value && !root.value.contains(event.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

function openPassword() {
  open.value = false
  Object.assign(form, { current: '', next: '', repeat: '' })
  formError.value = ''
  done.value = false
  showPassword.value = true
}
function closePassword() {
  if (!saving.value) showPassword.value = false
}
async function savePassword() {
  formError.value = ''
  if (form.next.length < 10) return (formError.value = 'Yeni şifre en az 10 karakter olmalı.')
  if (form.next !== form.repeat) return (formError.value = 'Yeni şifreler eşleşmiyor.')
  if (form.next === form.current)
    return (formError.value = 'Yeni şifre mevcut şifreden farklı olmalı.')
  saving.value = true
  try {
    await supplierApi('/password', {
      method: 'POST',
      body: { current_password: form.current, new_password: form.next },
    })
    Object.assign(form, { current: '', next: '', repeat: '' })
    done.value = true
  } catch (e) {
    formError.value = e.message
  } finally {
    saving.value = false
  }
}
async function logout() {
  open.value = false
  try {
    await supplierApi('/logout', { method: 'POST' })
  } catch {
    // An expired or unavailable server session must not prevent local logout.
  }
  clearSupplierSession()
  router.push('/supplier-login')
}
</script>

<style scoped>
.pm-root {
  position: relative;
}
.pm-trigger {
  border: 0;
  background: none;
  font: inherit;
  font-size: 12px;
  color: inherit;
  cursor: pointer;
  text-align: left;
  padding: 4px 6px;
  border-radius: 8px;
}
.pm-trigger:hover,
.pm-trigger[aria-expanded='true'] {
  background: #e7f0fc;
}
.pm-trigger i {
  font-style: normal;
  color: #617da6;
}
.pm-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 200;
  min-width: 230px;
  background: white;
  border: 1px solid #e1eaf5;
  border-radius: 8px;
  box-shadow: 0 10px 30px #0b2a5a1f;
  padding: 6px;
  display: grid;
}
.pm-head {
  padding: 8px 10px 10px;
  border-bottom: 1px solid #eef3f9;
  margin-bottom: 4px;
}
.pm-head strong,
.pm-head small {
  display: block;
}
.pm-head strong {
  font-size: 12px;
  color: #061d63;
}
.pm-head small {
  font-size: 11px;
  color: #7587a6;
  overflow-wrap: anywhere;
}
.pm-menu button,
.pm-menu a {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 0;
  background: none;
  font: inherit;
  font-size: 12px;
  color: #1b3f78;
  padding: 9px 10px;
  border-radius: 6px;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}
.pm-menu button:hover,
.pm-menu a:hover {
  background: #f1f6fd;
}
.pm-menu span {
  width: 18px;
  text-align: center;
}
.pm-logout {
  color: #d9374d !important;
  border-top: 1px solid #eef3f9 !important;
  border-radius: 0 0 6px 6px !important;
  margin-top: 4px;
}
.pm-modal {
  max-width: 420px;
}
.pm-modal form {
  display: grid;
  gap: 12px;
}
.pm-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 4px;
}
</style>
