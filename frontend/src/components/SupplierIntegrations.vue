<template>
  <section class="sw-card">
    <h2>Entegrasyon Kütüphanesi</h2>
    <p class="sw-muted">Araç takip ve yakıt servislerinizi tek yerden yönetin.</p>
    <div class="integration-library">
      <article v-for="item in providers" :key="item.id" class="integration-card">
        <span class="integration-icon" aria-hidden="true">{{ item.icon }}</span>
        <div>
          <small>{{ item.category }}</small>
          <h3>{{ item.name }}</h3>
        </div>
        <p class="sw-muted">{{ item.description }}</p>
        <UiButton
          class="sw-button"
          :class="{ primary: selected === item.id }"
          :aria-expanded="selected === item.id"
          :aria-controls="`integration-${item.id}`"
          @click="selected = selected === item.id ? '' : item.id"
          >{{ selected === item.id ? 'Ayarları Gizle' : 'Bağlantıyı Yönet' }}</UiButton
        >
      </article>
    </div>
  </section>
  <div v-if="selected === 'arvento'" id="integration-arvento">
    <SupplierArvento :vehicles="vehicles" :role="role" @updated="$emit('updated')" />
  </div>
  <div v-if="selected === 'shell'" id="integration-shell">
    <SupplierShell :vehicles="vehicles" :role="role" @updated="$emit('updated')" />
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { UiButton } from './ui/index.js'
import SupplierArvento from './SupplierArvento.vue'
import SupplierShell from './SupplierShell.vue'
defineProps({
  vehicles: { type: Array, default: () => [] },
  role: { type: String, default: 'viewer' },
})
defineEmits(['updated'])
const selected = ref('')
const providers = [
  {
    id: 'arvento',
    icon: '📡',
    category: 'Araç Takip',
    name: 'Arvento',
    description: 'GPS konumlarını ve kilometre verilerini cihaz eşlemesiyle filonuza aktarın.',
  },
  {
    id: 'shell',
    icon: '⛽',
    category: 'Yakıt Yönetimi',
    name: 'Shell Taşıt Tanıma',
    description: 'Gün sonu onaylı yakıt alımlarını Shell TTS üzerinden araç giderlerinize aktarın.',
  },
]
</script>
<style scoped>
.integration-library {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 20px;
  margin-top: 20px;
}
.integration-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  padding: 24px;
  border: 1px solid var(--sw-border, #e2e8f0);
  border-radius: 16px;
}
.integration-card h3 {
  margin: 4px 0 0;
}
.integration-card small {
  color: #64748b;
}
.integration-card p,
.integration-card button {
  grid-column: 1 / -1;
}
.integration-card button {
  justify-self: start;
}
.integration-icon {
  font-size: 1.8rem;
}
</style>
