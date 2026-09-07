<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Top Breadcrumb / Header -->
      <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <router-link to="/dashboard" style="color: #64748b; text-decoration: none;">← Geri</router-link>
        <span>/ Servis Paneli / {{ activeCategoryTitle }}</span>
      </div>

      <header class="dashboard-header" style="margin-bottom: 25px;">
        <div>
          <h1>Tedarikçi İşlemleri & Hizmet Talepleri</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Servis, lastik, ikame araç ve acil yol yardım taleplerinizi oluşturun ve takip edin.</p>
        </div>
        <button @click="activeTab = 'list'" class="btn btn-secondary" v-if="activeTab !== 'list'">
          📋 Taleplerim Listesi
        </button>
      </header>

      <!-- Category Switcher Tabs (FleetRent Premium Tab Pill Bar) -->
      <div class="category-tabs-bar">
        <button @click="switchTab('servis')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'servis' }">
          <span>🛠️</span> Bakım / Onarım
        </button>
        <button @click="switchTab('lastik')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'lastik' }">
          <span>🛞</span> Lastik Hizmetleri
        </button>
        <button @click="switchTab('ikame_arac')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'ikame_arac' }">
          <span>🚗</span> İkame Araç Tedariği
        </button>
        <button @click="switchTab('yol_yardim')" class="tab-pill-btn tab-danger" :class="{ 'active-tab-pill': activeTab === 'yol_yardim' }">
          <span>🚨</span> 7/24 Yol Yardım
        </button>
        <button @click="switchTab('list')" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'list' }" style="margin-left: auto;">
          <span>📋</span> Tüm Talepler ({{ requests.length }})
        </button>
      </div>

      <!-- ============================================================== -->
      <!-- 1. GÖRSEL: BAKIM / ONARIM TALEBİ FORMU (Servis Talebi Oluştur) -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'servis'" class="fade-in-up">
        <div class="grid-2" style="grid-template-columns: 1.4fr 0.6fr; gap: 30px; align-items: start;">
          <!-- Left Main Form -->
          <div class="glass-panel" style="padding: 32px; background: #ffffff;">
            <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 24px;">Servis Talebi Oluştur</h2>

            <form @submit.prevent="submitRequest('servis')">
              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Plaka *</label>
                  <select v-model="formServis.vehicle_id" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option v-for="v in vehicles" :key="v.id" :value="v.id">
                      {{ v.plate }} ({{ v.brand }} {{ v.model }})
                    </option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Bakım Türü *</label>
                  <select v-model="formServis.details.service_type" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option value="Periyodik Bakım">Periyodik Bakım</option>
                    <option value="Mekanik Onarım">Mekanik Onarım</option>
                    <option value="Hasar Onarım">Hasar Onarım</option>
                    <option value="Genel Kontrol">Genel Kontrol</option>
                  </select>
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">KM (GPS)</label>
                  <input type="text" v-model="formServis.details.mileage_gps" class="form-input" placeholder="45.426 km" readonly>
                  <span style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Otomatik GPS takip sisteminden çekilmektedir</span>
                </div>

                <div class="form-group">
                  <label class="form-label">Tercih Edilen Tarih 1 *</label>
                  <input type="date" v-model="formServis.details.date1" required class="form-input">
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Tercih Edilen Tarih 2 *</label>
                  <input type="date" v-model="formServis.details.date2" required class="form-input">
                </div>

                <div class="form-group">
                  <label class="form-label">İl *</label>
                  <input type="text" v-model="formServis.details.city" required class="form-input" placeholder="örn: İstanbul">
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">İlçe *</label>
                <input type="text" v-model="formServis.details.district" required class="form-input" placeholder="örn: Ümraniye">
              </div>

              <div class="form-group">
                <label class="form-label">Açıklama</label>
                <textarea v-model="formServis.description" class="form-textarea" rows="3" placeholder="Detayları yazın..."></textarea>
              </div>

              <!-- Notice Box from screenshot 1 -->
              <div class="notice-blue-box">
                <strong>Not:</strong> Kaza durumlarında 24 saatin sonunda sistem otomatik olarak ikame araç talebi oluşturur, harici ihtiyaçlarda manuel destek isteyiniz.
              </div>

              <!-- Vale Option Box from screenshot 1 -->
              <label class="vale-option-card">
                <input type="checkbox" v-model="formServis.details.valet_service">
                <span><strong>Vale Hizmeti</strong> - Aracınız bulunduğunuz adresten alınır ve teslim edilir. <strong>2.000 TL</strong> <span style="color: #a16207;">(isteğe bağlı)</span></span>
              </label>

              <button type="submit" class="btn btn-blue" style="padding: 14px 32px;" :disabled="submitting">
                {{ submitting ? 'Oluşturuluyor...' : 'Talep Oluştur' }}
              </button>
            </form>
          </div>

          <!-- Right Side Summary Boxes from screenshot 1 -->
          <div>
            <div class="side-summary-box">
              <h4>Bekleyen Talepler</h4>
              <div class="side-summary-empty">
                {{ pendingServisCount > 0 ? `${pendingServisCount} bekleyen talep mevcut` : 'Bekleyen servis talebi yok' }}
              </div>
            </div>

            <div class="side-blue-box">
              <h4>Servisteki Araçlar</h4>
              <div class="side-blue-empty">
                Serviste araç yok
              </div>
            </div>

            <div class="side-gray-box">
              <h4>Geçmiş Talepler</h4>
              <div style="text-align: center; color: #94a3b8; font-size: 0.88rem; padding: 15px 0;">
                Geçmiş talep yok
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 2. GÖRSEL: LASTİK DEĞİŞİM TALEBİ FORMU                         -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'lastik'" class="fade-in-up">
        <div class="grid-2" style="grid-template-columns: 1.4fr 0.6fr; gap: 30px; align-items: start;">
          <!-- Left Main Form -->
          <div class="glass-panel" style="padding: 32px; background: #ffffff;">
            <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Lastik Değişim Talebi</h2>

            <!-- Notice Box from screenshot 2 -->
            <div class="notice-blue-box" style="display: flex; gap: 12px; align-items: flex-start;">
              <span style="font-size: 1.2rem;">ℹ️</span>
              <div>
                <strong>Kış Lastiği Değişim Bilgilendirmesi:</strong><br>
                Kış lastiği değişim talepleri tedarikçinin belirttiği tarihte ve adreste yapılacaktır. Müsaitliği olmayan müşterilerimiz manuel olarak T.C. kış lastiğine geçiş tarihinden itibaren talep oluşturabilirler.
              </div>
            </div>

            <form @submit.prevent="submitRequest('lastik')">
              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Plaka *</label>
                  <select v-model="formLastik.vehicle_id" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option v-for="v in vehicles" :key="v.id" :value="v.id">
                      {{ v.plate }} ({{ v.brand }} {{ v.model }})
                    </option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Lastik Türü *</label>
                  <select v-model="formLastik.details.tire_type" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option value="Kış Lastiği">Kış Lastiği</option>
                    <option value="Yaz Lastiği">Yaz Lastiği</option>
                    <option value="Dört Mevsim">Dört Mevsim</option>
                  </select>
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Adet *</label>
                  <select v-model="formLastik.details.count" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option value="4">4 Adet (Takım)</option>
                    <option value="2">2 Adet (Ön/Arka)</option>
                    <option value="1">1 Adet</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Lastik Ebadı *</label>
                  <select v-model="formLastik.details.tire_size" required class="form-select">
                    <option value="" disabled>Seçin</option>
                    <option value="205/55 R16">205/55 R16</option>
                    <option value="225/45 R17">225/45 R17</option>
                    <option value="245/45 R18">245/45 R18</option>
                    <option value="195/65 R15">195/65 R15</option>
                  </select>
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">KM (GPS)</label>
                  <input type="text" v-model="formLastik.details.mileage_gps" class="form-input" placeholder="45.426 km" readonly>
                  <span style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">Otomatik GPS takip sisteminden çekilmektedir</span>
                </div>

                <div class="form-group">
                  <label class="form-label">Tercih Edilen Tarih 1 *</label>
                  <input type="date" v-model="formLastik.details.date1" required class="form-input">
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Tercih Edilen Tarih 2 *</label>
                  <input type="date" v-model="formLastik.details.date2" required class="form-input">
                </div>

                <div class="form-group">
                  <label class="form-label">İl *</label>
                  <input type="text" v-model="formLastik.details.city" required class="form-input" placeholder="orn: Istanbul">
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">İlçe *</label>
                <input type="text" v-model="formLastik.details.district" required class="form-input" placeholder="orn: Umraniye">
              </div>

              <div class="form-group">
                <label class="form-label">Açıklama</label>
                <textarea v-model="formLastik.description" class="form-textarea" rows="3" placeholder="Lastik degisim detaylari..."></textarea>
              </div>

              <button type="submit" class="btn btn-blue" style="padding: 14px 32px;" :disabled="submitting">
                {{ submitting ? 'Oluşturuluyor...' : 'Talep Oluştur' }}
              </button>
            </form>
          </div>

          <!-- Right Side Summary Boxes from screenshot 2 -->
          <div>
            <div class="side-summary-box">
              <h4>Bekleyen Talepler</h4>
              <div class="side-summary-empty">
                Bekleyen lastik talebi yok
              </div>
            </div>

            <div class="side-gray-box">
              <h4>Geçmiş Talepler</h4>
              <div style="text-align: center; color: #94a3b8; font-size: 0.88rem; padding: 15px 0;">
                Geçmiş talep yok
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 3. GÖRSEL: İKAME ARAÇ TALEBİ FORMU                            -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'ikame_arac'" class="fade-in-up">
        <div class="grid-2" style="grid-template-columns: 1.4fr 0.6fr; gap: 30px; align-items: start;">
          <!-- Left Main Form -->
          <div class="glass-panel" style="padding: 32px; background: #ffffff;">
            <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 24px;">İkame Araç Talebi</h2>

            <form @submit.prevent="submitRequest('ikame_arac')">
              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Araç Plakası *</label>
                  <select v-model="formIkame.vehicle_id" required class="form-select">
                    <option value="" disabled>Secin</option>
                    <option v-for="v in vehicles" :key="v.id" :value="v.id">
                      {{ v.plate }} ({{ v.brand }} {{ v.model }})
                    </option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">İkame Nedenı *</label>
                  <select v-model="formIkame.details.reason" required class="form-select">
                    <option value="" disabled>Secin</option>
                    <option value="Serviste Kalma">Serviste Kalma</option>
                    <option value="Kaza">Kaza</option>
                    <option value="Arıza">Arıza</option>
                    <option value="Bakım">Bakım</option>
                  </select>
                </div>
              </div>

              <div class="grid-2" style="gap: 16px;">
                <div class="form-group">
                  <label class="form-label">Başlangıç Tarihi *</label>
                  <input type="date" v-model="formIkame.details.start_date" required class="form-input">
                </div>

                <div class="form-group">
                  <label class="form-label">İl *</label>
                  <input type="text" v-model="formIkame.details.city" required class="form-input" placeholder="orn: Istanbul">
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">İlçe *</label>
                <input type="text" v-model="formIkame.details.district" required class="form-input" placeholder="orn: Umraniye">
              </div>

              <div class="form-group">
                <label class="form-label">Açıklama *</label>
                <textarea v-model="formIkame.description" required class="form-textarea" rows="3" placeholder="Ikame arac talebi detaylari..."></textarea>
              </div>

              <!-- Notice Box from screenshot 3 -->
              <div class="notice-blue-box">
                <strong>Not:</strong> Kaza durumlarında 24 saatin sonunda sistem otomatik olarak ikame araç talebi oluşturur, harici ihtiyaçlarda manuel destek isteyiniz.
              </div>

              <!-- Vale Option Box from screenshot 3 -->
              <label class="vale-option-card">
                <input type="checkbox" v-model="formIkame.details.valet_service">
                <span><strong>Vale Hizmeti</strong> - Aracınız bulunduğunuz adresten alınır ve teslim edilir. <strong>2.000 TL</strong> <span style="color: #a16207;">(isteğe bağlı)</span></span>
              </label>

              <button type="submit" class="btn btn-blue" style="padding: 14px 32px;" :disabled="submitting">
                {{ submitting ? 'Oluşturuluyor...' : 'Talep Oluştur' }}
              </button>
            </form>
          </div>

          <!-- Right Side Summary Box from screenshot 3 -->
          <div>
            <div class="side-summary-box">
              <h4>Bekleyen Talepler</h4>
              <div class="side-summary-empty">
                Bekleyen ikame talebi yok
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 4. GÖRSEL: YOL YARDIM (7/24 Acil Destek Formu)                 -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'yol_yardim'" class="fade-in-up">
        <div style="max-width: 680px; margin: 0 auto;">
          <!-- Highlight Red Call Box from screenshot 4 -->
          <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 18px 24px; text-align: center; margin-bottom: 30px;">
            <span style="font-weight: 700; color: #dc2626; font-size: 1.05rem;">7/24 Yol Yardım: <strong>0850 532 12 34</strong></span>
          </div>

          <div class="glass-panel" style="padding: 36px; background: #ffffff;">
            <form @submit.prevent="submitRequest('yol_yardim')">
              <!-- Vehicle Plate Selector (Pills) -->
              <div class="form-group" style="margin-bottom: 24px;">
                <label class="form-label">Araç Plakası</label>
                <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px;">
                  <button type="button" 
                    v-for="v in vehicles" 
                    :key="v.id"
                    @click="formYolYardim.vehicle_id = v.id"
                    class="filter-pill"
                    :class="{ 'active': formYolYardim.vehicle_id === v.id }"
                    style="font-family: monospace; font-size: 1rem; padding: 10px 20px;">
                    {{ v.plate }}
                  </button>
                </div>
              </div>

              <!-- Incident Selectors (Tiles) from screenshot 4 -->
              <div class="form-group" style="margin-bottom: 24px;">
                <label class="form-label">Ne oldu? (birden fazla seçilebilir)</label>
                <div class="incident-tiles-grid" style="margin-top: 8px;">
                  <!-- Kaza -->
                  <div class="incident-tile" 
                    :class="{ 'selected': formYolYardim.incidents.includes('Kaza') }"
                    @click="toggleIncident('Kaza')">
                    <span style="font-size: 2rem;">💥</span>
                    <span>Kaza</span>
                  </div>

                  <!-- Lastik Patladı -->
                  <div class="incident-tile" 
                    :class="{ 'selected': formYolYardim.incidents.includes('Lastik Patladı') }"
                    @click="toggleIncident('Lastik Patladı')">
                    <span style="font-size: 2rem;">🛞</span>
                    <span>Lastik Patladı</span>
                  </div>

                  <!-- Arıza -->
                  <div class="incident-tile" 
                    :class="{ 'selected': formYolYardim.incidents.includes('Arıza') }"
                    @click="toggleIncident('Arıza')">
                    <span style="font-size: 2rem;">🔧</span>
                    <span>Arıza</span>
                  </div>
                </div>
              </div>

              <!-- Photo Upload Dropzone from screenshot 4 -->
              <div class="form-group" style="margin-bottom: 24px;">
                <label class="form-label">Fotoğraf Yükle * <span style="color: #94a3b8; font-weight: normal;">(zorunlu)</span></label>
                
                <div class="upload-dropzone" @click="triggerPhotoUpload">
                  <div style="font-size: 2.2rem; margin-bottom: 8px;">📷</div>
                  <div style="font-weight: 600; color: #0f172a; font-size: 0.95rem;">Fotoğraf seçmek için tıklayın</div>
                  <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">veya sürükleyip bırakın</div>
                  <div v-if="formYolYardim.photo_name" style="margin-top: 10px; font-weight: 700; color: #2563eb;">
                    ✅ Yüklendi: {{ formYolYardim.photo_name }}
                  </div>
                </div>
                <input type="file" ref="photoInput" style="display: none;" @change="handlePhotoSelected">
                <span style="font-size: 0.8rem; color: #dc2626; font-weight: 600;">⚠️ En az bir fotoğraf yüklemelisiniz</span>
              </div>

              <!-- Submit Big Button -->
              <button type="submit" class="btn btn-blue" style="width: 100%; padding: 16px; font-size: 1.1rem; border-radius: 12px;" :disabled="submitting">
                🚨 {{ submitting ? 'Yol Yardım Ekibi Çağrılıyor...' : 'Yol Yardım İste !' }}
              </button>

              <p style="text-align: center; font-size: 0.8rem; color: #94a3b8; margin-top: 12px;">
                Plaka bilginize bağlı konum otomatik olarak yol yardım ekibine iletilir.
              </p>
            </form>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- LIST TAB: TÜM TALEPLER VE DURUM ZAMAN ÇİZELGESİ               -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'list'" class="fade-in-up">
        <div class="glass-panel" style="padding: 24px; background: #ffffff;">
          <div v-if="loading" class="text-center" style="padding: 40px 0;">Yükleniyor...</div>

          <div v-else-if="requests.length === 0" class="empty-state">
            <p>Henüz oluşturulmuş bir talep bulunmamaktadır.</p>
          </div>

          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Talep ID</th>
                  <th>Araç Plaka</th>
                  <th>Hizmet Türü</th>
                  <th>Tedarikçi</th>
                  <th>Açıklama / Detaylar</th>
                  <th>Tarih</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="req in requests" :key="req.id">
                  <td>#{{ req.id }}</td>
                  <td><strong style="color: #2563eb;">{{ req.vehicle_plate }}</strong></td>
                  <td><span class="badge" :class="getBadgeClass(req.type)">{{ getTypeName(req.type) }}</span></td>
                  <td>{{ req.supplier_name || 'Otomatik Atanıyor' }}</td>
                  <td>
                    {{ req.description }}
                    <div v-if="req.details" style="font-size: 0.78rem; color: #64748b; margin-top: 4px;">
                      <span v-if="req.details.valet_service">🚖 Vale İsteniyor | </span>
                      <span v-if="req.details.city">📍 {{ req.details.city }} / {{ req.details.district }}</span>
                    </div>
                  </td>
                  <td>{{ req.created_at }}</td>
                  <td><span class="badge" :class="getStatusBadgeClass(req.status)">{{ req.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const activeTab = ref('servis')
const vehicles = ref([])
const suppliers = ref([])
const requests = ref([])
const loading = ref(true)
const submitting = ref(false)
const photoInput = ref(null)

const activeCategoryTitle = computed(() => {
  switch (activeTab.value) {
    case 'servis': return 'Bakım Talebi'
    case 'lastik': return 'Lastik Değişim Talebi'
    case 'ikame_arac': return 'İkame Araç Talebi'
    case 'yol_yardim': return 'Yol Yardım'
    default: return 'Talep Listesi'
  }
})

const pendingServisCount = computed(() => {
  return requests.value.filter(r => r.type === 'servis' && r.status === 'Beklemede').length
})

// Forms for each 4 categories matching screenshots 1-4
const formServis = reactive({
  vehicle_id: '',
  description: '',
  details: {
    service_type: 'Periyodik Bakım',
    mileage_gps: '45.426 km',
    date1: '',
    date2: '',
    city: 'İstanbul',
    district: 'Ümraniye',
    valet_service: false
  }
})

const formLastik = reactive({
  vehicle_id: '',
  description: '',
  details: {
    tire_type: 'Kış Lastiği',
    count: '4',
    tire_size: '205/55 R16',
    mileage_gps: '45.426 km',
    date1: '',
    date2: '',
    city: 'İstanbul',
    district: 'Ümraniye'
  }
})

const formIkame = reactive({
  vehicle_id: '',
  description: '',
  details: {
    reason: 'Serviste Kalma',
    start_date: '',
    city: 'İstanbul',
    district: 'Ümraniye',
    valet_service: false
  }
})

const formYolYardim = reactive({
  vehicle_id: '',
  incidents: ['Kaza'],
  photo_name: '',
  description: 'Acil yol yardım talebi'
})

const switchTab = (tabName) => {
  activeTab.value = tabName
}

const toggleIncident = (name) => {
  const idx = formYolYardim.incidents.indexOf(name)
  if (idx > -1) {
    formYolYardim.incidents.splice(idx, 1)
  } else {
    formYolYardim.incidents.push(name)
  }
}

const triggerPhotoUpload = () => {
  if (photoInput.value) {
    photoInput.value.click()
  }
}

const handlePhotoSelected = (e) => {
  if (e.target.files && e.target.files[0]) {
    formYolYardim.photo_name = e.target.files[0].name
  }
}

const fetchData = async () => {
  try {
    const [vRes, sRes, rRes] = await Promise.all([
      fetch('/api/vehicles'),
      fetch('/api/suppliers'),
      fetch('/api/requests')
    ])
    if (vRes.ok && sRes.ok && rRes.ok) {
      vehicles.value = await vRes.json()
      suppliers.value = await sRes.json()
      requests.value = await rRes.json()
      requests.value.reverse()

      if (vehicles.value.length > 0) {
        formServis.vehicle_id = vehicles.value[0].id
        formLastik.vehicle_id = vehicles.value[0].id
        formIkame.vehicle_id = vehicles.value[0].id
        formYolYardim.vehicle_id = vehicles.value[0].id
      }
    }
  } catch (err) {
    console.error('Error fetching request data:', err)
  } finally {
    loading.value = false
  }
}

const submitRequest = async (type) => {
  submitting.value = true
  let payload = {}

  if (type === 'servis') {
    payload = {
      vehicle_id: formServis.vehicle_id,
      supplier_id: suppliers.value.find(s => s.type === 'servis')?.id || 1,
      type: 'servis',
      description: formServis.description || `${formServis.details.service_type} Talebi`,
      details: formServis.details
    }
  } else if (type === 'lastik') {
    payload = {
      vehicle_id: formLastik.vehicle_id,
      supplier_id: suppliers.value.find(s => s.type === 'lastik')?.id || 2,
      type: 'lastik',
      description: formLastik.description || `${formLastik.details.count} Adet ${formLastik.details.tire_type} Değişimi`,
      details: formLastik.details
    }
  } else if (type === 'ikame_arac') {
    payload = {
      vehicle_id: formIkame.vehicle_id,
      supplier_id: suppliers.value.find(s => s.type === 'ikame_arac')?.id || 4,
      type: 'ikame_arac',
      description: formIkame.description || `İkame Araç Talebi (${formIkame.details.reason})`,
      details: formIkame.details
    }
  } else if (type === 'yol_yardim') {
    payload = {
      vehicle_id: formYolYardim.vehicle_id,
      supplier_id: suppliers.value.find(s => s.type === 'yol_yardim')?.id || 3,
      type: 'yol_yardim',
      description: `Yol Yardım Talebi: ${formYolYardim.incidents.join(', ')}`,
      details: { incidents: formYolYardim.incidents, photo: formYolYardim.photo_name }
    }
  }

  try {
    const response = await fetch('/api/requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (response.ok) {
      alert('Talebiniz başarıyla iletildi!')
      await fetchData()
      activeTab.value = 'list'
    } else {
      alert('Talep oluşturulurken bir hata oluştu.')
    }
  } catch (err) {
    console.error('Error submitting request:', err)
  } finally {
    submitting.value = false
  }
}

const getTypeName = (type) => {
  switch (type) {
    case 'servis': return 'Bakım/Onarım'
    case 'lastik': return 'Lastik'
    case 'yol_yardim': return 'Yol Yardım'
    case 'ikame_arac': return 'İkame Araç'
    default: return type
  }
}

const getBadgeClass = (type) => {
  return {
    'badge-service': type === 'servis',
    'badge-tire': type === 'lastik',
    'badge-roadside': type === 'yol_yardim',
    'badge-replacement': type === 'ikame_arac'
  }
}

const getStatusBadgeClass = (status) => {
  return {
    'badge-active': status === 'Tamamlandı',
    'badge-service': status === 'İşlemde',
    'badge-tire': status === 'Onaylandı',
    'badge-roadside': status === 'İptal Edildi',
    'badge-pending': status === 'Beklemede'
  }
}

onMounted(() => {
  fetchData()
})
</script>

