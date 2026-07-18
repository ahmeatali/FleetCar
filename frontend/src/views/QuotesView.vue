<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header">
        <div>
          <h1>Kiralama Teklifleri</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Şirketiniz adına yapılan kiralama teklif taleplerini inceleyin ve sözleşmenizi onaylayın.</p>
        </div>
      </header>

      <!-- Quotes List -->
      <div v-if="loading" class="text-center" style="padding: 60px 0; font-size: 1.1rem; color: var(--text-muted);">
        Yükleniyor...
      </div>

      <div v-else-if="filteredQuotes.length === 0" class="empty-state glass-panel" style="margin-top: 30px; padding: 40px; text-align: center;">
        <span style="font-size: 3rem; display: block; margin-bottom: 15px;">📑</span>
        <h3>Aktif Teklif Talebi Bulunmuyor</h3>
        <p style="color: var(--text-muted); margin-top: 5px;">Anasayfadan yeni bir araç filosu için kiralama teklifi oluşturabilirsiniz.</p>
      </div>

      <div v-else style="margin-top: 30px; display: flex; flex-direction: column; gap: 25px;">
        <div v-for="quote in filteredQuotes" :key="quote.id" class="glass-panel quote-card" style="padding: 25px; border-left: 5px solid #7c3aed;">
          <!-- Card Header Info -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
            <div>
              <span style="font-size: 0.8rem; text-transform: uppercase; font-weight: 700; color: #a78bfa; letter-spacing: 0.05em;">TALEP ID: #{{ quote.id }}</span>
              <h2 style="font-size: 1.25rem; font-weight: 700; margin-top: 2px;">{{ quote.vehicle_count }} Adet {{ quote.vehicle_brand_model || (quote.vehicle_segment + ' Segment ' + quote.vehicle_type) }}</h2>
              <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 3px;">Talep Tarihi: {{ quote.created_at }}</p>
            </div>
            
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 5px;">
              <span class="badge" :class="getStatusBadgeClass(quote.status)" style="font-size: 0.85rem; padding: 6px 12px;">
                {{ quote.status }}
              </span>
              <span v-if="quote.contract_amount" style="font-size: 0.75rem; color: #10b981; font-weight: 600;">
                Kesinleşen Bedel: ₺{{ quote.contract_amount.toLocaleString() }}/Ay
              </span>
            </div>
          </div>

          <!-- Specs Info Grid -->
          <div class="grid-4" style="gap: 15px; margin-bottom: 25px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
            <div class="spec-box">
              <span class="spec-label">Araç Segmenti</span>
              <span class="spec-val">{{ quote.vehicle_segment }} Segment</span>
            </div>
            <div class="spec-box">
              <span class="spec-label">Gövde Tipi</span>
              <span class="spec-val">{{ quote.vehicle_type }}</span>
            </div>
            <div class="spec-box">
              <span class="spec-label">Kiralama Süresi</span>
              <span class="spec-val">{{ quote.duration_months }} Ay</span>
            </div>
            <div class="spec-box">
              <span class="spec-label">Yıllık Tahmini KM</span>
              <span class="spec-val">{{ quote.estimated_annual_mileage?.toLocaleString() }} km/yıl</span>
            </div>
          </div>

          <!-- Price & Timeline row -->
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
            <div>
              <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Aylık Toplam Teklif Bedeli</span>
              <div style="font-size: 1.8rem; font-weight: 800; color: #a78bfa; margin-top: 5px;">
                ₺{{ quote.monthly_price_try?.toLocaleString() }} <span style="font-size: 0.9rem; font-weight: 500; color: var(--text-muted);">+ KDV</span>
              </div>
            </div>

            <!-- Steps timeline -->
            <div class="timeline-steps" style="display: flex; gap: 25px; align-items: center;">
              <div class="step-item active-step">
                <span class="step-icon">✔</span>
                <span class="step-text">Talep Alındı</span>
              </div>
              <div class="step-line" :class="{ 'active-line': ['Teklif Verildi', 'Değerlendirmede', 'Sözleşme İmzalandı'].includes(quote.status) }"></div>
              <div class="step-item" :class="{ 'active-step': ['Teklif Verildi', 'Değerlendirmede', 'Sözleşme İmzalandı'].includes(quote.status) }">
                <span class="step-icon">📄</span>
                <span class="step-text">Teklif Hazır</span>
              </div>
              <div class="step-line" :class="{ 'active-line': quote.status === 'Sözleşme İmzalandı' }"></div>
              <div class="step-item" :class="{ 'active-step': quote.status === 'Sözleşme İmzalandı' }">
                <span class="step-icon">🖋️</span>
                <span class="step-text">Sözleşme</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div style="display: flex; justify-content: flex-end; gap: 15px; border-top: 1px solid var(--border-color); padding-top: 20px;">
            <div v-if="['Teklif Verildi', 'Değerlendirmede'].includes(quote.status)" style="display: flex; gap: 12px;">
              <button @click="rejectQuote(quote.id)" class="btn btn-secondary" style="border-color: rgba(239, 68, 68, 0.2); color: #ef4444; background: rgba(239, 68, 68, 0.02);">
                Teklifi Reddet
              </button>
              <button @click="openConfirmModal(quote)" class="btn btn-primary" style="background: linear-gradient(135deg, #10b981, #059669); border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
                Sözleşmeyi İmzala & Onayla
              </button>
            </div>
            
            <div v-else-if="quote.status === 'Sözleşme İmzalandı'" style="display: flex; align-items: center; gap: 10px; color: #10b981; font-weight: 600; font-size: 0.95rem;">
              <span>🛡️ Bu kiralama sözleşmesi imzalanmış ve filonuz aktifleşmiştir.</span>
            </div>

            <div v-else-if="quote.status === 'Reddedildi'" style="display: flex; align-items: center; gap: 10px; color: var(--text-muted); font-weight: 500; font-size: 0.95rem;">
              <span>❌ Bu teklif talebi iptal edilmiş/reddedilmiştir.</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- Client Signing Confirmation Modal -->
  <div v-if="showConfirmModal" class="modal-overlay" @click.self="showConfirmModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 480px; padding: 30px;">
      <h2 style="margin-bottom: 10px; color: #10b981; display: flex; align-items: center; gap: 10px;">
        <span>📝</span> Sözleşmeyi İmzala & Onayla
      </h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px;">
        <strong>Talep #{{ selectedQuote?.id }}</strong> için sunulan kiralama teklifini onaylamak üzeresiniz. Onay verdiğinizde sözleşme imzalanmış sayılacak ve araçlar filonuza tahsis edilecektir.
      </p>

      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); padding: 15px; border-radius: 8px; margin-bottom: 25px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 8px;">
          <span>Araç Adedi:</span> <strong>{{ selectedQuote?.vehicle_count }} Araç</strong>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 8px;">
          <span>Kiralama Süresi:</span> <strong>{{ selectedQuote?.duration_months }} Ay</strong>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 8px;">
          <span>Yıllık KM Limiti:</span> <strong>{{ selectedQuote?.estimated_annual_mileage?.toLocaleString() }} km</strong>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.95rem; border-top: 1px solid var(--border-color); padding-top: 8px; font-weight: bold; color: #10b981;">
          <span>Aylık Bedel (KDV Hariç):</span> <span>₺{{ selectedQuote?.monthly_price_try?.toLocaleString() }}</span>
        </div>
      </div>

      <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
        <button type="button" @click="showConfirmModal = false" class="btn btn-secondary">Vazgeç</button>
        <button type="button" @click="confirmSign" class="btn btn-primary" style="background: #10b981; color: #fff; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
          ✓ İmzala & Filonu Başlat
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const loading = ref(true)
const quotes = ref([])
const showConfirmModal = ref(false)
const selectedQuote = ref(null)

const userEmail = localStorage.getItem('fleetcar_user_email') || 'info@teknoholding.com'

const fetchQuotes = async () => {
  try {
    const res = await fetch('/api/quotes')
    if (res.ok) {
      quotes.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching quotes:', error)
  } finally {
    loading.value = false
  }
}

const filteredQuotes = computed(() => {
  // Return quotes belonging to company info@teknoholding.com or company name Tekno Holding
  return quotes.value.filter(q => 
    q.email.toLowerCase() === userEmail.toLowerCase() || 
    q.company_name.toLowerCase() === 'tekno holding'
  )
})

const getStatusBadgeClass = (status) => {
  return {
    'status-given': status === 'Teklif Verildi',
    'status-reviewing': status === 'Değerlendirmede',
    'status-signed': status === 'Sözleşme İmzalandı',
    'status-rejected': status === 'Reddedildi'
  }
}

const openConfirmModal = (quote) => {
  selectedQuote.value = quote
  showConfirmModal.value = true
}

const confirmSign = async () => {
  try {
    const res = await fetch(`/api/quotes/${selectedQuote.value.id}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        status: 'Sözleşme İmzalandı', 
        contract_amount: selectedQuote.value.monthly_price_try 
      })
    })
    if (res.ok) {
      await fetchQuotes()
      showConfirmModal.value = false
    } else {
      alert('Sözleşme imzalanırken hata oluştu.')
    }
  } catch (err) {
    console.error('Error signing quote:', err)
  }
}

const rejectQuote = async (quoteId) => {
  if (!confirm('Bu kiralama teklifini reddetmek istediğinize emin misiniz?')) return
  try {
    const res = await fetch(`/api/quotes/${quoteId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        status: 'Reddedildi'
      })
    })
    if (res.ok) {
      await fetchQuotes()
    } else {
      alert('Teklif güncellenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error rejecting quote:', err)
  }
}

onMounted(() => {
  fetchQuotes()
})
</script>

<style scoped>
.quote-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quote-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(124, 58, 237, 0.08);
}

.spec-box {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.spec-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.spec-val {
  font-size: 0.95rem;
  font-weight: 700;
  margin-top: 4px;
  color: #fff;
}

/* Timeline steps */
.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.step-item.active-step {
  opacity: 1;
}

.step-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  border: 1.5px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: bold;
}

.active-step .step-icon {
  background: rgba(124, 58, 237, 0.1);
  color: #a78bfa;
  border-color: #7c3aed;
}

.active-step:last-child .step-icon {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: #10b981;
}

.step-text {
  font-size: 0.75rem;
  font-weight: 600;
}

.step-line {
  height: 2px;
  width: 50px;
  background: var(--border-color);
}

.step-line.active-line {
  background: #7c3aed;
}

.status-select {
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
}

.status-given {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.status-reviewing {
  background: #fffbeb;
  color: #b45309;
  border-color: #fde68a;
}

.status-signed {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}

.status-rejected {
  background: #fff5f5;
  color: #c53030;
  border-color: #fed7d7;
}

/* Modal overlays and contents */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}

.modal-content {
  width: 100%;
}
</style>
