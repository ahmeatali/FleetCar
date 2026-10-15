<template>
  <section class="signed-document-box">
    <h4>İmzalı Belge / Manuel Teyit</h4>
    <p>
      Islak imzalı PDF, bu kayıt sürümüne bağlanır. Sözleşmede kiralayan, müşteri ve FleetRent;
      teslimatta kiralayan ve müşteri belgeyi kendi hesaplarından teyit eder.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>
    <template v-if="envelope">
      <strong>{{ envelope.status }} · Belge sürümü {{ envelope.operation_version }}</strong
      ><small>Islak imza tarihi: {{ envelope.signed_date }}</small>
      <p v-for="party in envelope.required_parties" :key="party">
        {{ signaturePartyLabels[party] }}:
        {{ envelope.attestations[party] ? 'Teyit edildi' : 'Bekliyor' }}
      </p>
      <UiButton class="sw-button" :disabled="busy" @click="download">İmzalı PDF İndir</UiButton>
      <UiButton
        v-if="
          role === 'owner' &&
          envelope.status === 'Teyit Bekliyor' &&
          !envelope.attestations.supplier
        "
        class="sw-button primary"
        :disabled="busy"
        @click="confirm"
        >Belgeyi ve Şartları Teyit Et</UiButton
      >
      <UiButton
        v-if="role === 'owner' && envelope.status === 'Teyit Bekliyor'"
        class="sw-button"
        :disabled="busy"
        @click="cancel"
        >Bekleyen Belge Sürecini İptal Et</UiButton
      >
    </template>
    <form
      v-else-if="role === 'owner' && ['Taslak', 'Planlandı'].includes(operation.raw_status)"
      @submit.prevent="upload"
    >
      <UiField
        >Islak İmza Tarihi<input v-model="signedDate" type="date" :max="today" required
      /></UiField>
      <UiField
        >Islak İmzalı PDF<input
          aria-label="Islak İmzalı PDF"
          type="file"
          accept="application/pdf"
          required
          @change="file = $event.target.files[0]"
      /></UiField>
      <UiButton class="sw-button" :disabled="busy || !file">İmzalı PDF'yi Kaydet</UiButton>
    </form>
    <p v-else>Bu kayıt için imzalı belge süreci yok.</p>
    <UiButton class="sw-button" :disabled="busy" @click="load">Belge Durumunu Yenile</UiButton>
  </section>
</template>
<script setup>
import { UiAlert, UiButton, UiField } from './ui/index.js'

import { onMounted, ref, watch } from 'vue'
import { signatureApi, downloadSignedDocument, signaturePartyLabels } from '../utils/signatureApi'
const props = defineProps({
    operation: { type: Object, required: true },
    role: { type: String, required: true },
  }),
  emit = defineEmits(['updated'])
const envelope = ref(null),
  error = ref(''),
  busy = ref(false),
  file = ref(null),
  today = new Date().toLocaleDateString('en-CA'),
  signedDate = ref(today)
async function load() {
  try {
    envelope.value = await signatureApi(
      `/api/supplier-workspace/records/${props.operation.id}/signature`,
    )
  } catch (e) {
    error.value = e.message
  }
}
async function upload() {
  busy.value = true
  error.value = ''
  try {
    const query = new URLSearchParams({
      version: props.operation.version,
      signed_date: signedDate.value,
      filename: file.value.name,
    })
    envelope.value = await signatureApi(
      `/api/supplier-workspace/records/${props.operation.id}/signed-document?${query}`,
      { method: 'POST', body: file.value },
    )
    file.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function confirm() {
  busy.value = true
  error.value = ''
  try {
    envelope.value = await signatureApi(`/api/signature-envelopes/${envelope.value.id}/attest`, {
      method: 'POST',
      body: { version: envelope.value.version, confirm: true },
    })
  } catch (e) {
    error.value = e.message
    await load()
  } finally {
    busy.value = false
  }
}
async function cancel() {
  busy.value = true
  error.value = ''
  try {
    await signatureApi(`/api/supplier-workspace/signature-envelopes/${envelope.value.id}/cancel`, {
      method: 'POST',
      body: { version: envelope.value.version, confirm: true },
    })
    emit('updated')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function download() {
  try {
    await downloadSignedDocument(envelope.value)
  } catch (e) {
    error.value = e.message
  }
}
watch(
  () => props.operation.id,
  () => {
    envelope.value = null
    file.value = null
    error.value = ''
    load()
  },
)
onMounted(load)
</script>
<style scoped>
.signed-document-box {
  padding: 14px 0;
  border-top: 1px solid #dce6f2;
  margin-top: 16px;
  font-size: 11px;
}
.signed-document-box p {
  line-height: 1.6;
}
.signed-document-box small {
  display: block;
  margin: 8px 0;
}
.signed-document-box button {
  margin: 5px 3px 5px 0;
}
.signed-document-box form {
  display: grid;
  gap: 12px;
}
.signed-document-box label {
  display: grid;
  gap: 8px;
}
.signed-document-box input {
  max-width: 100%;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
}
</style>
