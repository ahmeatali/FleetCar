<template>
  <div class="app-bg-glow"></div>
  
  <!-- Navbar -->
  <nav class="navbar">
    <router-link to="/" class="nav-logo">
      <div class="nav-logo-icon">F</div>
      <span>FleetCar</span>
    </router-link>
    <ul class="nav-links">
      <li><a href="#features" class="nav-link">Özellikler</a></li>
      <li><a href="#calculator" class="nav-link">Teklif Al</a></li>
      <li>
        <router-link to="/supplier-login" class="nav-link" style="margin-right: 15px;">
          Tedarikçi Girişi
        </router-link>
      </li>
      <li>
        <router-link to="/login" class="btn btn-secondary" style="padding: 8px 18px;">
          Müşteri Girişi
        </router-link>
      </li>
    </ul>
  </nav>

  <!-- Hero Section -->
  <header class="container hero-section fade-in-up">
    <div class="hero-content">
      <span class="hero-badge">YENİ NESİL FİLO YÖNETİMİ</span>
      <h1 class="hero-title">
        Şirketinizin Filosunu <br>
        <span class="gradient-brand">Akıllıca Yönetin</span>
      </h1>
      <p class="hero-subtitle">
        FleetCar ile dakikalar içinde kiralama teklifi alın. Satın alım sonrasında ise tüm araçlarınızı tek bir panelden takip edin, tedarikçilerinizle entegre çalışın.
      </p>
      <div class="hero-actions">
        <a href="#calculator" class="btn btn-accent btn-lg">Hemen Teklif Al</a>
        <a href="#features" class="btn btn-secondary btn-lg">Keşfet</a>
      </div>
    </div>
  </header>

  <!-- Features Section -->
  <section id="features" class="container features-section">
    <h2 class="section-title text-center">
      Tüm Operasyon <span class="gradient-brand">Tek Ekran</span> Entegrasyonu
    </h2>
    <p class="section-subtitle text-center">
      Filo yönetiminin en karmaşık aşamalarını dijitalleştiriyoruz. İşte entegre tedarikçi ağlarımız:
    </p>

    <div class="grid-4" style="margin-top: 40px;">
      <div class="glass-panel feature-card">
        <div class="feature-icon service-icon">⚙️</div>
        <h3>Yetkili Servis</h3>
        <p>Bakım ve onarım randevularını kolayca oluşturun. Araçlarınızın servis sürecini anlık izleyin.</p>
      </div>

      <div class="glass-panel feature-card">
        <div class="feature-icon tire-icon">🛞</div>
        <h3>Lastik Yönetimi</h3>
        <p>Mevsimsel lastik değişim randevuları ve lastik oteli hizmetlerini tek tıkla koordine edin.</p>
      </div>

      <div class="glass-panel feature-card">
        <div class="feature-icon roadside-icon">🚨</div>
        <h3>7/24 Yol Yardım</h3>
        <p>Arıza veya kaza anında konum bazlı hızlı çekici ve yol yardım ekiplerini anında yönlendirin.</p>
      </div>

      <div class="glass-panel feature-card">
        <div class="feature-icon replacement-icon">🚗</div>
        <h3>İkame Araç Tedariği</h3>
        <p>Serviste kalan araçlarınız yerine iş kaybını önleyecek ikame araçları dakikalar içinde organize edin.</p>
      </div>
    </div>
  </section>

  <!-- Calculator Section -->
  <section id="calculator" class="container calculator-section">
    <div class="glass-panel calc-container pulse-card">
      <div class="grid-2">
        <div class="calc-form-side">
          <h2 class="gradient-brand" style="font-size: 2rem; margin-bottom: 10px;">Dinamik Filo Teklif Motoru</h2>
          <p style="color: var(--text-muted); margin-bottom: 25px; font-size: 0.95rem;">
            Aşağıdaki parametreleri şirketinize göre ayarlayın. Teklifiniz anlık olarak hesaplanacaktır.
          </p>

          <form @submit.prevent="submitQuote">
            <div class="form-group">
              <label class="form-label">Şirket Adı</label>
              <input type="text" v-model="form.company_name" required class="form-input" placeholder="Örn: Tekno A.Ş.">
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
              <div class="form-group">
                <label class="form-label">E-posta</label>
                <input type="email" v-model="form.email" required class="form-input" placeholder="isim@sirket.com">
              </div>
              <div class="form-group">
                <label class="form-label">Telefon</label>
                <input type="tel" v-model="form.phone" required class="form-input" placeholder="05XX XXX XX XX">
              </div>
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 20px;">
              <div class="form-group">
                <label class="form-label">Araç Segmenti</label>
                <select v-model="form.vehicle_segment" class="form-select">
                  <option value="A">A Segmenti</option>
                  <option value="B">B Segmenti</option>
                  <option value="C">C Segmenti</option>
                  <option value="D">D Segmenti</option>
                  <option value="E">E Segmenti</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Araç Tipi</label>
                <select v-model="form.vehicle_type" class="form-select">
                  <option value="Sedan">Sedan</option>
                  <option value="SUV">SUV</option>
                  <option value="Hatchback">Hatchback</option>
                  <option value="Hafif Ticari">Hafif Ticari</option>
                  <option value="Station Wagon">Station Wagon</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <div class="slider-header">
                <label class="form-label">Araç Adedi</label>
                <span class="slider-value">{{ form.vehicle_count }} Adet</span>
              </div>
              <input type="range" min="1" max="100" v-model.number="form.vehicle_count" class="range-slider">
            </div>

            <div class="grid-2" style="gap: 15px;">
              <div class="form-group">
                <label class="form-label">Kiralama Süresi</label>
                <select v-model.number="form.duration_months" class="form-select">
                  <option :value="12">12 Ay</option>
                  <option :value="24">24 Ay</option>
                  <option :value="36">36 Ay</option>
                  <option :value="48">48 Ay</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">Yıllık Tahmini KM</label>
                <select v-model.number="form.estimated_annual_mileage" class="form-select">
                  <option :value="10000">10,000 KM</option>
                  <option :value="20000">20,000 KM</option>
                  <option :value="30000">30,000 KM</option>
                  <option :value="40000">40,000 KM</option>
                  <option :value="50000">50,000 KM</option>
                </select>
              </div>
            </div>

            <button type="submit" class="btn btn-accent btn-block" style="width: 100%; margin-top: 15px;" :disabled="submitting">
              {{ submitting ? 'Teklif Kaydediliyor...' : 'Teklifi Kaydet ve Portalı Aç' }}
            </button>
          </form>
        </div>

        <!-- Calculated Output Display -->
        <div class="calc-result-side">
          <div class="result-glass">
            <h3 style="font-size: 1.2rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted);">Aylık Kiralama Bedeli</h3>
            <div class="price-display">
              <span class="currency">₺</span>
              <span class="amount">{{ calculatedPriceFormatted }}</span>
              <span class="period">/ay</span>
            </div>
            <p class="price-info">
              * Bu teklif tahmini olup, KDV hariç hesaplanmıştır. Kiralama süresince tüm <b>servis, lastik, 7/24 yol yardım</b> ve <b>ikame araç</b> hizmetleri fiyata dahildir.
            </p>
            <div class="divider"></div>
            <div class="spec-list">
              <div class="spec-item">
                <span>Araç Adedi:</span>
                <strong>{{ form.vehicle_count }} Adet</strong>
              </div>
              <div class="spec-item">
                <span>Kiralama Süresi:</span>
                <strong>{{ form.duration_months }} Ay</strong>
              </div>
              <div class="spec-item">
                <span>Yıllık Kilometre Limiti:</span>
                <strong>{{ form.estimated_annual_mileage.toLocaleString() }} KM</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Success Modal -->
  <div v-if="showSuccessModal" class="modal-overlay">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 500px; padding: 40px; text-align: center;">
      <div class="modal-success-icon">🎉</div>
      <h2 class="gradient-brand" style="margin: 20px 0 10px;">Teklifiniz Oluşturuldu!</h2>
      <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.95rem; line-height: 1.6;">
        Tebrikler! <b>{{ submittedQuoteDetails?.company_name }}</b> adına aylık <b>₺{{ submittedQuoteDetails?.monthly_price_try?.toLocaleString() }}</b> tutarında teklif kaydı başarıyla oluşturuldu.
      </p>
      <div class="auth-helper-box">
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          🔑 Portala giriş yapabilmeniz için geçici şifreniz tanımlandı:<br>
          <span style="font-family: monospace; font-size: 1rem; color: var(--primary); background: rgba(79, 70, 229, 0.08); padding: 4px 8px; border-radius: 4px; display: inline-block; margin-top: 5px; font-weight: bold;">admin123</span>
        </p>
      </div>
      <div style="display: flex; gap: 15px; margin-top: 25px; justify-content: center;">
        <button @click="goToLogin" class="btn btn-primary">Yönetim Paneline Git</button>
        <button @click="showSuccessModal = false" class="btn btn-secondary">Kapat</button>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer class="footer text-center">
    <p>© 2026 FleetCar Filo Yönetim ve Kiralama Teknolojileri A.Ş. Tüm Hakları Saklıdır.</p>
  </footer>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const submitting = ref(false)
const showSuccessModal = ref(false)
const submittedQuoteDetails = ref(null)

const form = reactive({
  company_name: '',
  email: '',
  phone: '',
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  vehicle_count: 5,
  duration_months: 36,
  estimated_annual_mileage: 20000
})

// Client-side instant pricing formula (matching backend helper)
const calculatedPrice = computed(() => {
  const basePrice = 12000
  
  const segmentMultipliers = {
    "A": 0.70,
    "B": 0.85,
    "C": 1.0,
    "D": 1.30,
    "E": 1.70
  }
  const segMult = segmentMultipliers[form.vehicle_segment] || 1.0
  
  const typeMultipliers = {
    "Sedan": 1.0,
    "SUV": 1.20,
    "Hatchback": 0.95,
    "Hafif Ticari": 1.15,
    "Station Wagon": 1.05
  }
  const typeMult = typeMultipliers[form.vehicle_type] || 1.0
  
  const durationMultipliers = {
    12: 1.0,
    24: 0.90,
    36: 0.82,
    48: 0.75
  }
  const durMult = durationMultipliers[form.duration_months] || 0.90
  
  const mileageMultipliers = {
    10000: 0.95,
    20000: 1.0,
    30000: 1.12,
    40000: 1.25,
    50000: 1.40
  }
  const kmMult = mileageMultipliers[form.estimated_annual_mileage] || 1.0
  
  const pricePerVehicle = basePrice * segMult * typeMult * durMult * kmMult
  return Math.round(pricePerVehicle * form.vehicle_count)
})

const calculatedPriceFormatted = computed(() => {
  return calculatedPrice.value.toLocaleString('tr-TR')
})

const submitQuote = async () => {
  submitting.value = true
  try {
    const response = await fetch('/api/quotes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form)
    })
    
    if (response.ok) {
      const data = await response.json()
      submittedQuoteDetails.value = data
      showSuccessModal.value = true
    } else {
      alert('Teklif oluşturulurken bir sorun oluştu. Lütfen tekrar deneyin.')
    }
  } catch (error) {
    console.error('API Error:', error)
    alert('Backend bağlantı hatası oluştu.')
  } finally {
    submitting.value = false
  }
}

const goToLogin = () => {
  showSuccessModal.value = false
  router.push('/login')
}
</script>

<style scoped>
/* Scoped views-specific styling for Home page */
.hero-section {
  padding: 120px 20px 80px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-badge {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--secondary);
  margin-bottom: 25px;
  text-transform: uppercase;
}

.hero-title {
  font-size: 3.5rem;
  line-height: 1.15;
  margin-bottom: 25px;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: var(--text-muted);
  max-width: 650px;
  margin-bottom: 40px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 20px;
}

.hero-actions .btn {
  padding: 14px 32px;
  font-size: 1.05rem;
}

.features-section {
  padding: 80px 20px;
}

.section-title {
  font-size: 2.25rem;
  margin-bottom: 15px;
}

.section-subtitle {
  color: var(--text-muted);
  font-size: 1.05rem;
  max-width: 600px;
  margin: 0 auto 30px;
}

.feature-card {
  padding: 30px 24px;
  text-align: center;
  height: 100%;
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 20px;
  display: inline-block;
  padding: 15px;
  background: #f1f5f9;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.feature-card h3 {
  font-size: 1.25rem;
  margin-bottom: 12px;
}

.feature-card p {
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.6;
}

.calculator-section {
  padding: 80px 20px;
}

.calc-container {
  padding: 40px;
}

.calc-form-side {
  padding-right: 20px;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-value {
  font-weight: 700;
  color: var(--secondary);
}

.range-slider {
  width: 100%;
  height: 6px;
  background: #e2e8f0;
  border-radius: 5px;
  outline: none;
  -webkit-appearance: none;
  margin: 10px 0;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--secondary);
  cursor: pointer;
  box-shadow: 0 0 10px var(--secondary-glow);
  transition: transform 0.1s ease;
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.calc-result-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 20px;
}

.result-glass {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 35px;
  width: 100%;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
}

.price-display {
  display: flex;
  align-items: baseline;
  margin: 20px 0 15px;
}

.price-display .currency {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--secondary);
  margin-right: 5px;
}

.price-display .amount {
  font-size: 3.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-main);
}

.price-display .period {
  font-size: 1.1rem;
  color: var(--text-muted);
  margin-left: 8px;
}

.price-info {
  font-size: 0.8rem;
  color: var(--text-dark);
  line-height: 1.5;
}

.divider {
  height: 1px;
  background: var(--border-color);
  margin: 25px 0;
}

.spec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.spec-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.spec-item span {
  color: var(--text-muted);
}

.spec-item strong {
  color: var(--text-main);
}

/* Modal Styling */
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

.modal-success-icon {
  font-size: 4rem;
  line-height: 1;
}

.auth-helper-box {
  background: rgba(79, 70, 229, 0.05);
  border: 1px solid rgba(79, 70, 229, 0.15);
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.footer {
  padding: 40px 20px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.85rem;
  background: #ffffff;
}

.text-center { text-align: center; }
.btn-block { width: 100%; }

@media (max-width: 768px) {
  .hero-title { font-size: 2.25rem; }
  .calc-form-side, .calc-result-side { padding: 0; }
  .calc-container { padding: 25px 15px; }
  .calc-result-side { margin-top: 30px; }
  .price-display .amount { font-size: 2.5rem; }
}
</style>
