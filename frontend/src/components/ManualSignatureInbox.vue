<template>
  <section class="glass-panel manual-signature-inbox">
    <header>
      <h2>İmzalı Belge Teyitleri</h2>
      <UiButton class="btn" :disabled="busy" @click="load">Yenile</UiButton>
    </header>
    <p>
      Islak imzalı PDF'yi ve bağlı sözleşme/teslim şartlarını inceleyerek firma adına teyit verin.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>
    <p v-if="!items.length">Bekleyen veya tamamlanmış belge kaydı yok.</p>
    <article v-for="item in items" :key="item.id">
      <strong>{{ item.number }} · {{ item.title }}</strong>
      <p>
        {{ item.status }} · Kayıt sürümü {{ item.operation_version }} · İmza tarihi
        {{ item.signed_date }}
      </p>
      <details>
        <summary>Uygulamadaki Kayıt ve Şartlar</summary>
        <p>
          Aylık / kayıt tutarı: {{ item.snapshot.amount }} TL · {{ item.snapshot.date }} -
          {{ item.snapshot.end_date || '—' }}
        </p>
        <p>
          Süre: {{ item.snapshot.details.months || '—' }} ay · Yıllık km:
          {{ item.snapshot.details.annual_km || '—' }}
        </p>
        <p v-for="car in item.snapshot.vehicles" :key="car.id">
          {{ car.plate }} · {{ car.brand }} {{ car.model }} · Şase {{ car.chassis_no }} ·
          {{ car.mileage }} km
        </p>
        <p>{{ item.snapshot.details.terms || item.snapshot.details.notes }}</p>
        <p v-if="item.kind === 'delivery'">
          Teslim alan: {{ item.snapshot.details.receiver }} · Teslim yeri:
          {{ item.snapshot.details.location }} · Km: {{ item.snapshot.details.mileage }}
        </p>
      </details>
      <p v-for="party in item.required_parties" :key="party">
        {{ signaturePartyLabels[party] }}:
        {{ item.attestations[party] ? 'Teyit edildi' : 'Bekliyor' }}
      </p>
      <UiButton class="btn" @click="download(item)">İmzalı PDF İndir</UiButton>
      <UiButton
        v-if="item.status === 'Teyit Bekliyor' && !item.attestations[party]"
        class="btn btn-primary"
        :disabled="busy"
        @click="confirm(item)"
        >Belgeyi ve Şartları Teyit Et</UiButton
      >
    </article>
  </section>
</template>
<script setup>
import { UiAlert, UiButton } from './ui/index.js'

import { computed, onMounted, ref } from 'vue'
import { signatureApi, downloadSignedDocument, signaturePartyLabels } from '../utils/signatureApi'
const props = defineProps({ account: { type: String, default: 'customer' } }),
  items = ref([]),
  busy = ref(false),
  error = ref('')
const party = computed(() => (props.account === 'admin' ? 'platform' : 'customer'))
async function load() {
  error.value = ''
  try {
    items.value = await signatureApi(
      `/api/${props.account === 'admin' ? 'admin' : 'customer-workspace'}/signatures`,
      {},
      props.account,
    )
  } catch (e) {
    error.value = e.message
  }
}
async function confirm(item) {
  busy.value = true
  error.value = ''
  try {
    await signatureApi(
      `/api/signature-envelopes/${item.id}/attest`,
      { method: 'POST', body: { version: item.version, confirm: true } },
      props.account,
    )
    await load()
  } catch (e) {
    error.value = e.message
    await load()
  } finally {
    busy.value = false
  }
}
async function download(item) {
  try {
    await downloadSignedDocument(item, props.account)
  } catch (e) {
    error.value = e.message
  }
}
onMounted(load)
</script>
<style scoped>
.manual-signature-inbox {
  margin: var(--fr-space-4) 0;
  padding: var(--fr-space-4) var(--fr-space-5);
  background: var(--fr-surface) !important;
  border: 1px solid var(--fr-border) !important;
  border-radius: var(--fr-radius-lg) !important;
  box-shadow: var(--fr-shadow-sm) !important;
  color: var(--fr-text);
}
.manual-signature-inbox header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--fr-space-3);
}
.manual-signature-inbox h2 {
  margin: 0;
  font-size: var(--fr-text-lg);
  font-weight: 700;
  color: var(--fr-ink);
}
.manual-signature-inbox > p {
  margin: 4px 0 var(--fr-space-3);
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.manual-signature-inbox article {
  margin: var(--fr-space-3) 0 0;
  padding: var(--fr-space-3) var(--fr-space-4);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius);
  font-size: var(--fr-text-sm);
}
.manual-signature-inbox article strong {
  color: var(--fr-ink);
}
.manual-signature-inbox p {
  margin: 2px 0;
  overflow-wrap: anywhere;
  line-height: 1.55;
}
.manual-signature-inbox summary {
  margin: 4px 0;
  color: var(--fr-primary);
  font-weight: 600;
  cursor: pointer;
}
.manual-signature-inbox button {
  min-height: 34px;
  margin: 10px 8px 0 0;
  padding: 0 12px;
  border: 1px solid var(--fr-border-strong);
  border-radius: var(--fr-radius);
  background: var(--fr-surface);
  color: var(--fr-ink);
  font: inherit;
  font-size: var(--fr-text-sm);
  font-weight: 600;
  cursor: pointer;
}
.manual-signature-inbox header button {
  margin: 0;
}
.manual-signature-inbox button.btn-primary {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
}
.manual-signature-inbox button:disabled {
  opacity: 0.55;
  cursor: default;
}
</style>
