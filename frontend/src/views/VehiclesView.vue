<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header">
        <div>
          <h1>Araç Yönetimi</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Filodaki araçları yönetin, canlı GPS haritadan takip edin, durum ve muayene bilgilerini izleyin.</p>
        </div>
        <button @click="showAddModal = true" class="btn btn-primary">
          ➕ Yeni Araç Ekle
        </button>
      </header>

      <!-- Tabs Section (FleetRent Premium Tab Pill Bar) -->
      <div class="category-tabs-bar">
        <button @click="activeTab = 'active'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'active' }">
          <span>🚗</span> Aktif Araçlar ({{ activeVehiclesCount }})
        </button>
        <button @click="activeTab = 'old'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'old' }">
          <span>📂</span> Eski Araçlar ({{ oldVehiclesCount }})
        </button>
        <button @click="activeTab = 'tracking'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'tracking' }">
          <span>📍</span> Araç Takibi (GPS Harita)
        </button>
      </div>

      <!-- Filter Panel (For Active & Old Vehicles) -->
      <div v-if="activeTab === 'active' || activeTab === 'old'" class="glass-panel filters-panel" style="margin-top: 20px; padding: 20px; display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
        <div style="flex: 1; min-width: 250px;">
          <input type="text" v-model="filters.search" class="form-input" placeholder="Plaka, marka, model veya şase no ara...">
        </div>
        <div style="width: 200px;" v-if="activeTab === 'active'">
          <select v-model="filters.status" class="form-select">
            <option value="">Tüm Durumlar</option>
            <option value="Aktif">Aktif</option>
            <option value="Serviste">Serviste</option>
            <option value="Lastik Değişiminde">Lastik Değişiminde</option>
            <option value="Yol Yardımında">Yol Yardımında</option>
            <option value="İkame Araç Bekliyor">İkame Araç Bekliyor</option>
          </select>
        </div>
        <div style="width: 160px;">
          <select v-model="filters.vehicle_segment" class="form-select">
            <option value="">Tüm Segmentler</option>
            <option value="A">A Segmenti</option>
            <option value="B">B Segmenti</option>
            <option value="C">C Segmenti</option>
            <option value="D">D Segmenti</option>
            <option value="E">E Segmenti</option>
          </select>
        </div>
        <div style="width: 160px;">
          <select v-model="filters.vehicle_type" class="form-select">
            <option value="">Tüm Tipler</option>
            <option value="Sedan">Sedan</option>
            <option value="SUV">SUV</option>
            <option value="Hatchback">Hatchback</option>
            <option value="Hafif Ticari">Hafif Ticari</option>
            <option value="Station Wagon">Station Wagon</option>
          </select>
        </div>
        <div style="width: 150px;">
          <select v-model="filters.fuel" class="form-select">
            <option value="">Tüm Yakıtlar</option>
            <option value="Benzin">Benzin</option>
            <option value="Dizel">Dizel</option>
            <option value="Hibrit">Hibrit</option>
            <option value="Elektrik">Elektrik</option>
          </select>
        </div>
      </div>

      <!-- Vehicles List Table (For Active & Old Vehicles) -->
      <div v-if="activeTab === 'active' || activeTab === 'old'" class="glass-panel" style="margin-top: 20px; padding: 10px;">
        <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>
        
        <div v-else-if="filteredVehicles.length === 0" class="empty-state">
          <p>Kriterlere uygun araç bulunamadı.</p>
        </div>

        <div v-else class="custom-table-container">
          <table class="custom-table">
            <thead>
              <tr>
                <th>Plaka</th>
                <th>Araç Detayı</th>
                <th>Segment</th>
                <th>Tip</th>
                <th>Yakıt</th>
                <th>Mesafe (KM)</th>
                <th>{{ activeTab === 'active' ? 'Durum' : 'Kaldırılma Nedeni' }}</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="vehicle in filteredVehicles" :key="vehicle.id">
                <td class="plate-td">
                  <span class="plate-badge">{{ vehicle.plate }}</span>
                </td>
                <td>
                  <strong style="color: #fff; cursor: pointer;" @click="openDetailsModal(vehicle)" class="hover-underline">
                    {{ vehicle.brand }} {{ vehicle.model }}
                  </strong>
                  <div style="font-size: 0.75rem; color: var(--text-dark); font-family: monospace;">
                    Sicil / Şase No: {{ vehicle.chassis_no }}
                  </div>
                </td>
                <td>{{ vehicle.vehicle_segment }}</td>
                <td>{{ vehicle.vehicle_type }}</td>
                <td>{{ vehicle.fuel }}</td>
                <td>{{ vehicle.mileage?.toLocaleString() }} km</td>
                <td>
                  <template v-if="activeTab === 'active'">
                    <span class="badge" :class="getVehicleBadgeClass(vehicle.status)">{{ vehicle.status }}</span>
                  </template>
                  <template v-else>
                    <span style="font-size: 0.85rem; color: #dc2626; font-weight: bold;">{{ vehicle.removal_reason || 'Kaldırıldı' }}</span>
                  </template>
                </td>
                <td>
                  <div style="display: flex; gap: 8px;">
                    <button @click="openDetailsModal(vehicle)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">
                      Detay
                    </button>
                    <template v-if="activeTab === 'active'">
                      <button @click="openRemoveModal(vehicle)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem; color: #ef4444;">
                        Kaldır
                      </button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 📍 HARİTAYLA ARAÇ TAKİP ALANI (Görseldeki 1'e 1 Tasarım)       -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'tracking'" class="fade-in-up" style="margin-top: 20px;">
        <!-- Breadcrumb -->
        <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <span style="color: #64748b;">← Geri</span>
          <span>/ Araçlarım / Araç Takip</span>
        </div>

        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 25px;">
          <h2 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Takip</h2>

          <!-- Interactive OpenStreetMap / Google Maps Embed Container -->
          <div class="map-tracking-container">
            <a href="https://maps.google.com" target="_blank" class="map-overlay-badge">
              <span>Haritalar'da aç</span> ↗
            </a>
            <iframe 
              class="map-iframe" 
              src="https://www.openstreetmap.org/export/embed.html?bbox=28.8000%2C40.9000%2C29.2500%2C41.1500&amp;layer=mapnik&amp;marker=41.0082%2C28.9784"
              allowfullscreen
            ></iframe>
          </div>

          <!-- Bottom Status Grid Panels matching screenshot -->
          <div class="grid-2" style="gap: 25px; align-items: start;">
            <!-- Left Green Panel: Aktif Araçlar -->
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 16px; padding: 24px;">
              <h3 style="font-size: 1.1rem; font-weight: 800; color: #15803d; margin-bottom: 16px;">Aktif Araçlar</h3>

              <div class="map-vehicle-card-active" v-for="v in activeVehiclesList" :key="v.id">
                <div>
                  <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a;">{{ v.plate }}</div>
                  <div style="font-size: 0.85rem; color: #64748b;">{{ v.brand }} {{ v.model }} - {{ v.model_year || 2024 }}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 0.8rem; font-weight: 700; color: #16a34a; background: #dcfce7; padding: 4px 10px; border-radius: 20px;">
                    🟢 Seyir Halinde
                  </span>
                </div>
              </div>
            </div>

            <!-- Right Orange Panel: Pasif Araçlar / Servisteki -->
            <div style="background: #fff7ed; border: 1px solid #ffedd5; border-radius: 16px; padding: 24px;">
              <h3 style="font-size: 1.1rem; font-weight: 800; color: #c2410c; margin-bottom: 16px;">Pasif Araçlar</h3>

              <div class="map-vehicle-card-active" v-for="v in passiveVehiclesList" :key="v.id" style="border-color: #fed7aa;">
                <div>
                  <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a;">{{ v.plate }}</div>
                  <div style="font-size: 0.85rem; color: #64748b;">{{ v.brand }} {{ v.model }} - {{ v.model_year || 2024 }}</div>
                </div>
                <div>
                  <span style="font-size: 0.8rem; font-weight: 700; color: #ea580c; background: #ffedd5; padding: 4px 10px; border-radius: 20px;">
                    Serviste
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- Add Vehicle Modal -->
  <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 650px; padding: 30px;">
      <h2 class="gradient-brand" style="margin-bottom: 20px;">Yeni Araç Ekle</h2>
      
      <form @submit.prevent="addVehicle">
        <div style="max-height: 65vh; overflow-y: auto; padding-right: 10px;">
          <!-- Section 1: Genel Bilgiler -->
          <h3 class="form-section-title">🚗 Genel Bilgiler</h3>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Plaka</label>
              <input type="text" v-model="newVehicleForm.plate" required class="form-input" placeholder="34 AAA 000" style="text-transform: uppercase;">
            </div>
            <div class="form-group">
              <label class="form-label">Üretim Yılı</label>
              <input type="number" min="2010" max="2027" v-model.number="newVehicleForm.year" required class="form-input" placeholder="2024">
            </div>
          </div>

          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Marka</label>
              <input type="text" v-model="newVehicleForm.brand" required class="form-input" placeholder="Renault">
            </div>
            <div class="form-group">
              <label class="form-label">Model</label>
              <input type="text" v-model="newVehicleForm.model" required class="form-input" placeholder="Clio">
            </div>
          </div>

          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Araç Segmenti</label>
              <select v-model="newVehicleForm.vehicle_segment" class="form-select">
                <option value="A">A Segmenti</option>
                <option value="B">B Segmenti</option>
                <option value="C">C Segmenti</option>
                <option value="D">D Segmenti</option>
                <option value="E">E Segmenti</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Araç Tipi</label>
              <select v-model="newVehicleForm.vehicle_type" class="form-select">
                <option value="Sedan">Sedan</option>
                <option value="SUV">SUV</option>
                <option value="Hatchback">Hatchback</option>
                <option value="Hafif Ticari">Hafif Ticari</option>
                <option value="Station Wagon">Station Wagon</option>
              </select>
            </div>
          </div>

          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
            <div class="form-group">
              <label class="form-label">Yakıt Tipi</label>
              <select v-model="newVehicleForm.fuel" class="form-select">
                <option value="Benzin">Benzin</option>
                <option value="Dizel">Dizel</option>
                <option value="Hibrit">Hibrit</option>
                <option value="Elektrik">Elektrik</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Güncel KM</label>
              <input type="number" min="0" v-model.number="newVehicleForm.mileage" required class="form-input" placeholder="15000">
            </div>
          </div>

          <!-- Section 2: Tescil ve Hukuki -->
          <h3 class="form-section-title">📋 Tescil & Muayene Bilgileri</h3>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
            <div class="form-group">
              <label class="form-label">Şase Numarası (Sicil No / Benzersiz ID)</label>
              <input type="text" v-model="newVehicleForm.chassis_no" required class="form-input" placeholder="VF3RENAULTME..." style="text-transform: uppercase;">
            </div>
            <div class="form-group">
              <label class="form-label">Ruhsat Seri No</label>
              <input type="text" v-model="newVehicleForm.license_serial_no" required class="form-input" placeholder="AA123456" style="text-transform: uppercase;">
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 15px;">
            <label class="form-label">Muayene Tarihi</label>
            <input type="date" v-model="newVehicleForm.inspection_date" required class="form-input">
          </div>

          <!-- Section 3: Bakım ve Lastik -->
          <h3 class="form-section-title">⚙️ Servis & Lastik Durumu</h3>
          <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px;">
            <div class="form-group">
              <label class="form-label">Lastik Değ. Tarihi</label>
              <input type="date" v-model="newVehicleForm.tire_change_date" required class="form-input">
            </div>
            <div class="form-group">
              <label class="form-label">Son Servis Tarihi</label>
              <input type="date" v-model="newVehicleForm.last_service_date" required class="form-input">
            </div>
            <div class="form-group">
              <label class="form-label">Son Servis KM</label>
              <input type="number" min="0" v-model.number="newVehicleForm.last_service_mileage" required class="form-input" placeholder="10000">
            </div>
          </div>

          <!-- Section 4: GPS & UTTS Entegrasyon Bilgileri -->
          <h3 class="form-section-title">📡 GPS & UTTS Entegrasyon Bilgileri</h3>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
            <div class="form-group">
              <label class="form-label">GPS Cihaz Kodu / IMEI (Harita Takip)</label>
              <input type="text" v-model="newVehicleForm.gps_device_id" class="form-input" placeholder="Örn: GPS-TR-884920">
            </div>
            <div class="form-group">
              <label class="form-label">UTTS Kodu (Ulusal Taşıt Tanıma Birimi ID)</label>
              <input type="text" v-model="newVehicleForm.utts_code" class="form-input" placeholder="Örn: UTTS-34-89201">
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showAddModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Kaydediliyor...' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Details / Edit Modal -->
  <div v-if="showDetailsModal" class="modal-overlay" @click.self="showDetailsModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 650px; padding: 30px; background: #ffffff;">
      
      <!-- VIEW MODE -->
      <template v-if="!isEditingVehicle">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
          <div>
            <span class="plate-badge">{{ selectedVehicle.plate }}</span>
            <h2 style="margin-top: 10px; color: #0f172a;">{{ selectedVehicle.brand }} {{ selectedVehicle.model }}</h2>
          </div>
          <div style="display: flex; gap: 10px; align-items: center;">
            <button @click="startEditingVehicle" class="btn btn-secondary" style="padding: 6px 14px; font-size: 0.85rem; font-weight: 700; color: #2563eb; border: 1px solid #bfdbfe; background: #eff6ff;">
              ✏️ Düzenle
            </button>
            <span class="badge" :class="getVehicleBadgeClass(selectedVehicle.status)" style="font-size: 0.85rem; padding: 6px 12px;">{{ selectedVehicle.status }}</span>
          </div>
        </div>

        <div class="grid-2" style="gap: 20px; font-size: 0.95rem;">
          <div>
            <h4 style="color: var(--secondary); margin-bottom: 10px;">📋 Kimlik & Tescil</h4>
            <p style="margin-bottom: 8px;"><strong>Şase / Sicil No:</strong> <span style="font-family: monospace; color: var(--primary); background: rgba(79, 70, 229, 0.08); padding: 2px 6px; border-radius: 4px; font-weight: bold;">{{ selectedVehicle.chassis_no }}</span></p>
            <p style="margin-bottom: 8px;"><strong>Ruhsat Seri No:</strong> <span style="font-family: monospace;">{{ selectedVehicle.license_serial_no }}</span></p>
            <p style="margin-bottom: 8px;"><strong>Araç Segmenti:</strong> {{ selectedVehicle.vehicle_segment }} Segmenti</p>
            <p style="margin-bottom: 8px;"><strong>Araç Tipi:</strong> {{ selectedVehicle.vehicle_type }}</p>
            
            <div v-if="!selectedVehicle.is_active" style="margin-top: 15px; background: #fef2f2; border: 1px solid #fca5a5; padding: 12px; border-radius: 8px;">
              <h5 style="color: #dc2626; margin-bottom: 5px; font-weight: bold; font-size: 0.85rem;">🚫 FİLO DIŞI BIRAKILDI</h5>
              <p style="margin-bottom: 4px; font-size: 0.8rem; color: #7f1d1d; line-height: 1.4;"><strong>Nedeni:</strong> {{ selectedVehicle.removal_reason }}</p>
              <p style="margin-bottom: 0; font-size: 0.8rem; color: #7f1d1d;"><strong>Tarih:</strong> {{ formatDate(selectedVehicle.removed_at) }}</p>
            </div>
            <p style="margin-bottom: 8px;"><strong>Üretim Yılı:</strong> {{ selectedVehicle.year }}</p>
            <p style="margin-bottom: 8px;"><strong>Yakıt Türü:</strong> {{ selectedVehicle.fuel }}</p>
          </div>
          <div>
            <h4 style="color: var(--secondary); margin-bottom: 10px;">⚙️ Durum & Operasyon</h4>
            <p style="margin-bottom: 8px;"><strong>Güncel Kilometre:</strong> {{ selectedVehicle.mileage?.toLocaleString() }} km</p>
            <p style="margin-bottom: 8px;"><strong>Muayene Tarihi:</strong> {{ formatDate(selectedVehicle.inspection_date) }}</p>
            <p style="margin-bottom: 8px;"><strong>Lastik Değişim:</strong> {{ formatDate(selectedVehicle.tire_change_date) }}</p>
            <p style="margin-bottom: 8px;"><strong>Son Servis Tarihi:</strong> {{ formatDate(selectedVehicle.last_service_date) }}</p>
            <p style="margin-bottom: 8px;"><strong>Son Servis KM:</strong> {{ selectedVehicle.last_service_mileage?.toLocaleString() }} km</p>

            <h4 style="color: var(--secondary); margin-bottom: 10px; margin-top: 15px;">📡 GPS & UTTS Entegrasyonu</h4>
            <p style="margin-bottom: 8px;"><strong>GPS Cihaz ID:</strong> <span style="font-family: monospace; color: #2563eb; background: #eff6ff; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{{ selectedVehicle.gps_device_id || 'Tanımlanmadı' }}</span></p>
            <p style="margin-bottom: 8px;"><strong>UTTS Taşıt Tanıma Kodu:</strong> <span style="font-family: monospace; color: #059669; background: #ecfdf5; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{{ selectedVehicle.utts_code || 'Tanımlanmadı' }}</span></p>
          </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; margin-top: 30px; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button @click="startEditingVehicle" class="btn btn-secondary" style="font-size: 0.9rem; color: #2563eb; font-weight: 700;">
            ✏️ Araç Bilgilerini & GPS/UTTS Düzenle
          </button>
          <template v-if="selectedVehicle.is_active">
            <router-link to="/dashboard/requests" class="btn btn-primary" style="font-size: 0.9rem;">Hizmet Talebi Oluştur</router-link>
          </template>
          <template v-else>
            <button @click="reactivateVehicle(selectedVehicle)" class="btn btn-primary" style="font-size: 0.9rem; background: #059669; border: none; box-shadow: 0 4px 15px rgba(5, 150, 105, 0.2);">
              Aracı Tekrar Filoya Ekle
            </button>
          </template>
          <button @click="showDetailsModal = false" class="btn btn-secondary">Kapat</button>
        </div>
      </template>

      <!-- EDIT MODE -->
      <template v-else>
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
          <h2 style="color: #0f172a; font-size: 1.3rem; font-weight: 800;">Araç Bilgilerini & Entegrasyonu Düzenle</h2>
          <span class="plate-badge">{{ editVehicleForm.plate }}</span>
        </div>

        <form @submit.prevent="saveVehicleEdit">
          <div style="max-height: 60vh; overflow-y: auto; padding-right: 10px;">
            <!-- GPS & UTTS Section -->
            <h3 class="form-section-title" style="color: #2563eb;">📡 GPS & UTTS Entegrasyon Bilgileri</h3>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
              <div class="form-group">
                <label class="form-label">GPS Cihaz Kodu / IMEI</label>
                <input type="text" v-model="editVehicleForm.gps_device_id" class="form-input" placeholder="Örn: GPS-TR-884920">
              </div>
              <div class="form-group">
                <label class="form-label">UTTS Taşıt Tanıma Kodu</label>
                <input type="text" v-model="editVehicleForm.utts_code" class="form-input" placeholder="Örn: UTTS-34-89201">
              </div>
            </div>

            <!-- Genel Bilgiler -->
            <h3 class="form-section-title">🚗 Genel Bilgiler</h3>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
              <div class="form-group">
                <label class="form-label">Plaka</label>
                <input type="text" v-model="editVehicleForm.plate" required class="form-input" style="text-transform: uppercase;">
              </div>
              <div class="form-group">
                <label class="form-label">Güncel KM</label>
                <input type="number" min="0" v-model.number="editVehicleForm.mileage" required class="form-input">
              </div>
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
              <div class="form-group">
                <label class="form-label">Marka</label>
                <input type="text" v-model="editVehicleForm.brand" required class="form-input">
              </div>
              <div class="form-group">
                <label class="form-label">Model</label>
                <input type="text" v-model="editVehicleForm.model" required class="form-input">
              </div>
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr;">
              <div class="form-group">
                <label class="form-label">Üretim Yılı</label>
                <input type="number" min="2010" max="2027" v-model.number="editVehicleForm.year" required class="form-input">
              </div>
              <div class="form-group">
                <label class="form-label">Yakıt Tipi</label>
                <select v-model="editVehicleForm.fuel" class="form-select">
                  <option value="Benzin">Benzin</option>
                  <option value="Dizel">Dizel</option>
                  <option value="Hibrit">Hibrit</option>
                  <option value="Elektrik">Elektrik</option>
                </select>
              </div>
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
              <div class="form-group">
                <label class="form-label">Ruhsat Seri No</label>
                <input type="text" v-model="editVehicleForm.license_serial_no" class="form-input">
              </div>
              <div class="form-group">
                <label class="form-label">Muayene Tarihi</label>
                <input type="date" v-model="editVehicleForm.inspection_date" class="form-input">
              </div>
            </div>
          </div>

          <div style="display: flex; gap: 15px; justify-content: flex-end; margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 15px;">
            <button type="button" @click="isEditingVehicle = false" class="btn btn-secondary">Vazgeç</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Kaydediliyor...' : '💾 Değişiklikleri Kaydet' }}
            </button>
          </div>
        </form>
      </template>

    </div>
  </div>

  <!-- Remove Vehicle Reason Modal -->
  <div v-if="showRemoveModal" class="modal-overlay" @click.self="showRemoveModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 450px; padding: 30px;">
      <h2 style="margin-bottom: 10px; color: #dc2626; display: flex; align-items: center; gap: 10px;">
        <span>⚠️</span> Araç Kaldırma Talebi
      </h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px;">
        <strong>{{ vehicleToRemove?.plate }}</strong> plakalı ({{ vehicleToRemove?.brand }} {{ vehicleToRemove?.model }}) aracı filodan kaldırmak istediğinize emin misiniz? Lütfen kaldırma nedenini belirtin:
      </p>

      <form @submit.prevent="confirmRemoveVehicle">
        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Kaldırma Nedeni</label>
          <select v-model="removalReason" required class="form-select">
            <option value="Sözleşme Bitişi">Sözleşme Bitişi</option>
            <option value="Araç Değişimi">Araç Değişimi</option>
            <option value="Pert">Pert</option>
            <option value="Araç Satışı">Araç Satışı</option>
          </select>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showRemoveModal = false" class="btn btn-secondary">Vazgeç</button>
          <button type="submit" class="btn btn-danger" style="background: #dc2626; color: #fff; border: none; box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);">
            Aracı Kaldır
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const vehicles = ref([])
const loading = ref(true)
const saving = ref(false)
const showAddModal = ref(false)
const showDetailsModal = ref(false)
const selectedVehicle = ref({})
const isEditingVehicle = ref(false)

const activeTab = ref('active')
const showRemoveModal = ref(false)
const vehicleToRemove = ref(null)
const removalReason = ref('Sözleşme Bitişi')

const editVehicleForm = reactive({
  plate: '',
  brand: '',
  model: '',
  year: 2024,
  fuel: 'Benzin',
  mileage: 0,
  chassis_no: '',
  license_serial_no: '',
  inspection_date: '',
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  tire_change_date: '',
  last_service_date: '',
  last_service_mileage: 0,
  gps_device_id: '',
  utts_code: ''
})

const activeVehiclesCount = computed(() => vehicles.value.filter(v => v.is_active).length)
const oldVehiclesCount = computed(() => vehicles.value.filter(v => !v.is_active).length)

const activeVehiclesList = computed(() => vehicles.value.filter(v => v.is_active && v.status === 'Aktif'))
const passiveVehiclesList = computed(() => vehicles.value.filter(v => !v.is_active || v.status !== 'Aktif'))

const filters = reactive({
  search: '',
  status: '',
  vehicle_segment: '',
  vehicle_type: '',
  fuel: ''
})

const newVehicleForm = reactive({
  plate: '',
  brand: '',
  model: '',
  year: 2024,
  fuel: 'Benzin',
  mileage: 0,
  chassis_no: '',
  license_serial_no: '',
  inspection_date: '',
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  tire_change_date: '',
  last_service_date: '',
  last_service_mileage: 0,
  gps_device_id: '',
  utts_code: ''
})

const fetchVehicles = async () => {
  try {
    const customerId = localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
    let url = '/api/vehicles'
    if (customerId) {
      url += `?customer_id=${customerId}`
    }
    const response = await fetch(url)
    if (response.ok) {
      vehicles.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching vehicles:', error)
  } finally {
    loading.value = false
  }
}

const addVehicle = async () => {
  saving.value = true
  try {
    const customerId = localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
    const payload = { ...newVehicleForm }
    if (customerId) {
      payload.customer_id = parseInt(customerId)
    }

    const response = await fetch('/api/vehicles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    
    if (response.ok) {
      const addedVehicle = await response.json()
      vehicles.value.push(addedVehicle)
      showAddModal.value = false
      resetForm()
    } else {
      const err = await response.json()
      alert(err.detail || 'Araç eklenirken bir hata oluştu.')
    }
  } catch (error) {
    console.error('Error adding vehicle:', error)
    alert('Sistem bağlantı hatası.')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  newVehicleForm.plate = ''
  newVehicleForm.brand = ''
  newVehicleForm.model = ''
  newVehicleForm.year = 2024
  newVehicleForm.fuel = 'Benzin'
  newVehicleForm.mileage = 0
  newVehicleForm.chassis_no = ''
  newVehicleForm.license_serial_no = ''
  newVehicleForm.inspection_date = ''
  newVehicleForm.vehicle_segment = 'C'
  newVehicleForm.vehicle_type = 'Sedan'
  newVehicleForm.tire_change_date = ''
  newVehicleForm.last_service_date = ''
  newVehicleForm.last_service_mileage = 0
  newVehicleForm.gps_device_id = ''
  newVehicleForm.utts_code = ''
}

const openDetailsModal = (vehicle) => {
  selectedVehicle.value = vehicle
  isEditingVehicle.value = false
  showDetailsModal.value = true
}

const startEditingVehicle = () => {
  if (!selectedVehicle.value) return
  const v = selectedVehicle.value
  editVehicleForm.plate = v.plate || ''
  editVehicleForm.brand = v.brand || ''
  editVehicleForm.model = v.model || ''
  editVehicleForm.year = v.year || 2024
  editVehicleForm.fuel = v.fuel || 'Benzin'
  editVehicleForm.mileage = v.mileage || 0
  editVehicleForm.chassis_no = v.chassis_no || ''
  editVehicleForm.license_serial_no = v.license_serial_no || ''
  editVehicleForm.inspection_date = v.inspection_date || ''
  editVehicleForm.vehicle_segment = v.vehicle_segment || 'C'
  editVehicleForm.vehicle_type = v.vehicle_type || 'Sedan'
  editVehicleForm.tire_change_date = v.tire_change_date || ''
  editVehicleForm.last_service_date = v.last_service_date || ''
  editVehicleForm.last_service_mileage = v.last_service_mileage || 0
  editVehicleForm.gps_device_id = v.gps_device_id || ''
  editVehicleForm.utts_code = v.utts_code || ''
  isEditingVehicle.value = true
}

const saveVehicleEdit = async () => {
  if (!selectedVehicle.value || !selectedVehicle.value.id) return
  saving.value = true
  try {
    const response = await fetch(`/api/vehicles/${selectedVehicle.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editVehicleForm)
    })
    
    if (response.ok) {
      const updatedVehicle = await response.json()
      const idx = vehicles.value.findIndex(v => v.id === updatedVehicle.id)
      if (idx !== -1) {
        vehicles.value[idx] = updatedVehicle
      }
      selectedVehicle.value = updatedVehicle
      isEditingVehicle.value = false
    } else {
      const err = await response.json()
      alert(err.detail || 'Araç bilgileri güncellenirken bir hata oluştu.')
    }
  } catch (error) {
    console.error('Error updating vehicle:', error)
    alert('Sistem bağlantı hatası.')
  } finally {
    saving.value = false
  }
}

const openRemoveModal = (vehicle) => {
  vehicleToRemove.value = vehicle
  removalReason.value = 'Sözleşme Bitişi'
  showRemoveModal.value = true
}

const confirmRemoveVehicle = async () => {
  try {
    const response = await fetch(`/api/vehicles/${vehicleToRemove.value.id}/remove`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reason: removalReason.value })
    })
    
    if (response.ok) {
      // Reload vehicles
      await fetchVehicles()
      showRemoveModal.value = false
    } else {
      alert('Araç kaldırılırken bir hata oluştu.')
    }
  } catch (error) {
    console.error('Error removing vehicle:', error)
    alert('Sistem bağlantı hatası.')
  }
}

const reactivateVehicle = async (vehicle) => {
  try {
    const response = await fetch(`/api/vehicles/${vehicle.id}/reactivate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      await fetchVehicles()
      showDetailsModal.value = false
    } else {
      alert('Araç tekrar filoya eklenirken bir hata oluştu.')
    }
  } catch (error) {
    console.error('Error reactivating vehicle:', error)
    alert('Sistem bağlantı hatası.')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('tr-TR')
  } catch (e) {
    return dateStr
  }
}

const getVehicleBadgeClass = (status) => {
  return {
    'badge-active': status === 'Aktif',
    'badge-service': status === 'Serviste',
    'badge-tire': status === 'Lastik Değişiminde',
    'badge-roadside': status === 'Yol Yardımında',
    'badge-replacement': status === 'İkame Araç Bekliyor'
  }
}

const filteredVehicles = computed(() => {
  return vehicles.value.filter(vehicle => {
    // Filter active tab
    const matchesTab = activeTab.value === 'active' ? vehicle.is_active : !vehicle.is_active
    if (!matchesTab) return false

    const searchVal = filters.search.toLowerCase()
    const matchesSearch = 
      vehicle.plate.toLowerCase().includes(searchVal) ||
      vehicle.brand.toLowerCase().includes(searchVal) ||
      vehicle.model.toLowerCase().includes(searchVal) ||
      vehicle.chassis_no.toLowerCase().includes(searchVal)
      
    const matchesStatus = filters.status === '' || vehicle.status === filters.status
    const matchesSegment = filters.vehicle_segment === '' || vehicle.vehicle_segment === filters.vehicle_segment
    const matchesType = filters.vehicle_type === '' || vehicle.vehicle_type === filters.vehicle_type
    const matchesFuel = filters.fuel === '' || vehicle.fuel === filters.fuel
    
    return matchesSearch && matchesStatus && matchesSegment && matchesType && matchesFuel
  })
})

onMounted(() => {
  fetchVehicles()
})
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}

.plate-td {
  padding-left: 20px !important;
}

.plate-badge {
  background: #1e293b;
  border: 2px solid #fff;
  border-radius: 4px;
  color: #fff;
  font-family: 'Courier New', Courier, monospace;
  font-weight: 800;
  padding: 4px 8px;
  display: inline-block;
  letter-spacing: 0.05em;
  font-size: 0.85rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.5);
  position: relative;
}

/* Blue band for TR on Turkish Plates */
.plate-badge::before {
  content: "TR";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 14px;
  background: #003399;
  color: #fff;
  font-size: 0.5rem;
  font-family: var(--font-sans);
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top-left-radius: 2px;
  border-bottom-left-radius: 2px;
}

.plate-badge {
  padding-left: 18px; /* Offset for TR band */
}

.hover-underline:hover {
  text-decoration: underline;
}

.empty-state {
  padding: 50px 0;
  text-align: center;
  color: var(--text-muted);
}

.form-section-title {
  font-size: 1rem;
  color: var(--secondary);
  margin-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 5px;
  margin-top: 15px;
}

.form-section-title:first-of-type {
  margin-top: 0;
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

.modal-content {
  width: 100%;
}

.tabs-container {
  margin-bottom: 20px;
}
.tab-btn {
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.95rem;
  border: none;
  background: transparent;
  color: var(--text-dark);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
}
.tab-btn:hover {
  color: var(--primary);
}
.active-tab {
  color: var(--primary);
  border-bottom-color: var(--primary);
}
.btn-danger-hover:hover {
  background: #fef2f2 !important;
  border-color: #fca5a5 !important;
  color: #dc2626 !important;
}
.badge-old-reason {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
}
</style>
