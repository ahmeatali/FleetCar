<template>
  <section class="business-history">
    <h2>Ticari İşlem Geçmişi</h2>
    <p>
      Teklif, sözleşme, teslimat, iade, poliçe, hasar, ceza ve faturalar ortak kayıtlardan
      gösterilir.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>
    <p v-else-if="loading">Kayıtlar yükleniyor…</p>
    <p v-else-if="!rows.length">Bu araç için görüntülenebilir ticari kayıt yok.</p>
    <article v-for="row in rows" :key="row.id">
      <strong>{{ labels[row.kind] || row.kind }} · {{ row.number }}</strong>
      <p>{{ row.title }} · {{ row.status }}</p>
      <small
        >{{ row.date }}<template v-if="row.end_date"> — {{ row.end_date }}</template> ·
        {{ money(row.amount)
        }}<template v-if="row.balance != null"> · Bakiye: {{ money(row.balance) }}</template></small
      >
    </article>
  </section>
</template>
<script setup>
import { customerClient } from '../api/clients.js'
import { formatMoney } from '../utils/formatters.js'

import { UiAlert } from './ui/index.js'

import { ref, onMounted, watch } from 'vue'
import { supplierApi } from '../utils/supplierApi'
const props = defineProps({ vehicleId: { type: String, required: true }, supplier: Boolean })
const rows = ref([]),
  error = ref(''),
  loading = ref(false)
const labels = {
  offer: 'Teklif',
  contract: 'Sözleşme',
  delivery: 'Teslimat',
  return: 'İade',
  policy: 'Poliçe',
  damage: 'Hasar',
  fine: 'Ceza',
  invoice: 'Fatura',
  payment: 'Ödeme',
  sale: 'Satış',
  maintenance: 'Bakım',
}
const money = (value) => formatMoney(value ?? 0)
async function load() {
  loading.value = true
  error.value = ''
  try {
    const path = '/vehicles/' + encodeURIComponent(props.vehicleId) + '/business-history'
    if (props.supplier) rows.value = await supplierApi(path)
    else rows.value = await customerClient(path)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.vehicleId, load)
</script>
<style scoped>
.business-history {
  padding: 18px;
  background: white;
  border: 1px solid #e1e8f2;
  border-radius: 12px;
  color: #254566;
}
.business-history p {
  font-size: 12px;
  line-height: 1.6;
}
.business-history article {
  padding: 14px 0;
  border-bottom: 1px solid #edf1f7;
  overflow-wrap: anywhere;
}
.business-history strong {
  font-size: 13px;
}
.business-history small {
  font-size: 11px;
}
</style>
