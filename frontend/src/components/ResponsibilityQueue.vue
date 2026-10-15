<template>
  <section v-if="items.length" class="sw-card sw-report-ledger">
    <h2>Mali Eşleştirme Kuyruğu</h2>
    <p class="sw-muted">
      Olay tarihindeki müşteri kesin değil. Güncel plaka atamasına göre otomatik fatura
      oluşturulmaz.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>
    <UiTable class="sw-table-scroll"
      ><table class="sw-table">
        <thead>
          <tr>
            <th>Kaynak</th>
            <th>Plaka / Tarih</th>
            <th>Tutar</th>
            <th>Durum</th>
            <th>Müşteri Sorumluluğu</th>
            <th>İnceleme Gerekçesi</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="`${row.kind}-${row.id}`">
            <td>{{ row.number }}</td>
            <td>{{ row.plate }}<br />{{ row.date }}</td>
            <td>{{ row.amount }}</td>
            <td>{{ row.responsibility_status || row.details?.responsibility_status }}</td>
            <td>
              <select v-model="customersByRow[row.id]" :disabled="!canResolve">
                <option value="">Tedarikçi gideri / müşteri yok</option>
                <option v-for="customer in customers" :key="customer.id" :value="customer.id">
                  {{ customer.title }}
                </option>
              </select>
            </td>
            <td>
              <input
                v-model="reasons[row.id]"
                :disabled="!canResolve"
                placeholder="Olay belgesi ve tahsis incelemesi"
                minlength="10"
              />
            </td>
            <td>
              <UiButton v-if="canResolve" class="sw-button" :disabled="busy" @click="resolve(row)"
                >Eşlemeyi Onayla</UiButton
              >
            </td>
          </tr>
        </tbody>
      </table></UiTable
    >
  </section>
</template>
<script setup>
import { UiAlert, UiButton, UiTable } from './ui/index.js'

import { computed, reactive, ref } from 'vue'
import { supplierApi } from '../utils/supplierApi'
const props = defineProps({
    items: { type: Array, default: () => [] },
    customers: { type: Array, default: () => [] },
    role: { type: String, default: 'viewer' },
  }),
  emit = defineEmits(['updated'])
const customersByRow = reactive({}),
  reasons = reactive({}),
  error = ref(''),
  busy = ref(false)
const canResolve = computed(() => ['owner', 'finance', 'fleet_manager'].includes(props.role))
async function resolve(row) {
  busy.value = true
  error.value = ''
  try {
    const id = row.source_id || row.id
    await supplierApi(`/responsibility/${row.kind}/${id}`, {
      method: 'PUT',
      body: {
        customer_id: customersByRow[row.id] ? Number(customersByRow[row.id]) : null,
        reason: reasons[row.id] || '',
      },
    })
    emit('updated')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>
