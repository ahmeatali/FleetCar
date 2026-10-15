<template>
  <section class="glass-panel incoming-offers">
    <h2>Tedarikçilerden Gelen Teklifler</h2>
    <p>
      Güncel teklif sürümünü kabul edin, revizyon isteyin veya reddedin. Kararınız tedarikçi
      ekranına aynı kayıt üzerinden yansır.
    </p>
    <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert
    ><UiAlert v-if="notice" as="p" tone="info">{{ notice }}</UiAlert>
    <details>
      <summary>Bir Kiralama Tedarikçisine Firma Erişimi Ver</summary>
      <p>
        Seçtiğiniz tedarikçi firmanızı müşteri listesine alabilir, iletişim bilgilerinizi görebilir
        ve size teklif hazırlayabilir.
      </p>
      <form @submit.prevent="authorize">
        <UiField
          >Tedarikçi<select v-model="supplierId" required>
            <option value="">Tedarikçi seçin</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
              {{ supplier.name }}
            </option>
          </select></UiField
        ><UiButton class="btn" :disabled="busy">Tedarikçi Bağlantısını Onayla</UiButton>
      </form>
    </details>
    <p v-if="!offers.length && !loading">Henüz gönderilmiş tedarikçi teklifi yok.</p>
    <article v-for="offer in offers" :key="offer.id">
      <header>
        <strong>{{ offer.number }} · {{ offer.title }}</strong
        ><span>{{ offer.status }} · Sürüm {{ offer.version }}</span>
      </header>
      <p>
        {{ offer.supplier_name }} · {{ offer.details.quantity || 1 }} araç ·
        {{ offer.details.months }} ay · Araç başına aylık {{ money(offer.amount) }}
      </p>
      <p>
        Yıllık km: {{ offer.details.annual_km || '—' }} · Geçerlilik: {{ offer.end_date || '—' }}
      </p>
      <details>
        <summary>Teklif Şartları</summary>
        <dl>
          <template v-for="field in offerFields" :key="field.key"
            ><dt>{{ field.label }}</dt>
            <dd>{{ offer.details[field.key] ?? '—' }}</dd></template
          >
        </dl>
      </details>
      <template v-if="offer.raw_status === 'Beklemede'">
        <UiField :for="`offer-note-${offer.id}`">Karar / Revizyon Açıklaması</UiField
        ><textarea
          :id="`offer-note-${offer.id}`"
          v-model="notes[offer.id]"
          maxlength="3000"
          rows="2"
        />
        <div>
          <UiButton class="btn btn-primary" :disabled="busy" @click="decide(offer, 'accept')"
            >Teklifi Kabul Et</UiButton
          ><UiButton class="btn" :disabled="busy" @click="decide(offer, 'revise')"
            >Revizyon İste</UiButton
          ><UiButton class="btn" :disabled="busy" @click="decide(offer, 'reject')"
            >Teklifi Reddet</UiButton
          >
        </div>
      </template>
      <p v-if="offer.details.customer_decision_note">
        Karar açıklaması: {{ offer.details.customer_decision_note }}
      </p>
      <UiButton class="btn" :disabled="busy" @click="history(offer)"
        >Gönderilen Sürümleri Gör</UiButton
      >
      <div v-if="histories[offer.id]">
        <p v-for="version in histories[offer.id]" :key="version.version">
          Sürüm {{ version.version }} · {{ version.snapshot.status }} ·
          {{ money(version.snapshot.amount) }} ·
          {{ new Date(version.created_at).toLocaleString('tr-TR') }}
        </p>
      </div>
    </article>
  </section>
</template>
<script setup>
import { customerClient as api } from '../api/clients.js'
import { formatMoney } from '../utils/formatters.js'

import { UiAlert, UiButton, UiField } from './ui/index.js'

import { onMounted, reactive, ref } from 'vue'
import { supplierModules } from '../utils/supplierModules'
const offerFields = supplierModules.offers.fields
const suppliers = ref([]),
  supplierId = ref('')
const offers = ref([]),
  notes = reactive({}),
  histories = reactive({}),
  loading = ref(true),
  busy = ref(false),
  error = ref(''),
  notice = ref('')
const money = (value) => formatMoney(value ?? 0)
async function load() {
  loading.value = true
  try {
    offers.value = await api('/offers')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
async function decide(offer, decision) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api(`/offers/${offer.id}/decision`, {
      method: 'POST',
      body: { version: offer.version, decision, note: notes[offer.id] || '' },
    })
    delete histories[offer.id]
    await load()
    notice.value = 'Kararınız kaydedildi.'
  } catch (e) {
    error.value = e.message
    if (e.message.includes('Yenileyin')) await load()
  } finally {
    busy.value = false
  }
}
async function authorize() {
  busy.value = true
  error.value = ''
  try {
    await api(`/suppliers/${supplierId.value}/authorize`, { method: 'POST' })
    notice.value = 'Tedarikçi firma bağlantısı onaylandı.'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
async function history(offer) {
  try {
    histories[offer.id] = await api(`/offers/${offer.id}/versions`)
  } catch (e) {
    error.value = e.message
  }
}
onMounted(async () => {
  await load()
  try {
    suppliers.value = await api('/rental-suppliers')
  } catch (e) {
    error.value = e.message
  }
})
</script>
<style scoped>
.incoming-offers {
  padding: 24px;
  margin: 24px 0;
}
.incoming-offers article {
  padding: 18px;
  border: 1px solid var(--border-color, #dce5f2);
  border-radius: 12px;
  margin: 12px 0;
}
.incoming-offers header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.incoming-offers textarea {
  display: block;
  width: 100%;
  margin: 8px 0 12px;
  background: var(--bg-input, #fff);
  color: inherit;
  border: 1px solid var(--border-color, #dce5f2);
  border-radius: 6px;
  padding: 10px;
}
.incoming-offers button {
  margin: 8px 8px 0 0;
}
.incoming-offers dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.incoming-offers dd {
  margin: 0;
  overflow-wrap: anywhere;
}
</style>
