<template>
  <div class="app-bg-glow" style="--glow-color: rgba(16, 185, 129, 0.08);"></div>
  
  <div class="supplier-layout">
    <!-- Navbar Header -->
    <header class="supplier-header glass-panel">
      <div class="logo-area">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #10b981, #059669);">F</div>
        <div>
          <span class="portal-title">FleetCar <span class="tag-supplier">Tedarikçi Portalı</span></span>
          <h2 class="supplier-name-display">{{ supplierName }}</h2>
        </div>
      </div>

      <div style="display: flex; gap: 15px; align-items: center;">
        <span class="type-badge">{{ getTypeName(supplierType) }}</span>
        <button @click="handleLogout" class="btn btn-secondary btn-danger-hover">
          Çıkış Yap ➔
        </button>
      </div>
    </header>

    <!-- Supplier Profile Info Bar -->
    <div class="glass-panel profile-bar fade-in-up" style="padding: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
      <div style="display: flex; gap: 30px; flex-wrap: wrap; align-items: center;">
        <div>
          <span class="profile-meta-label">📍 İl / İlçe</span>
          <div class="profile-meta-value" style="font-weight: 600; font-size: 1rem; color: var(--text-main); margin-top: 3px;">
            {{ supplierCity || '-' }} / {{ supplierDistrict || '-' }}
          </div>
        </div>
        <div style="border-left: 1px solid var(--border-color); padding-left: 30px;">
          <span class="profile-meta-label">📄 Servis Tipi</span>
          <div style="margin-top: 5px;">
            <span class="contract-badge" :class="supplierContractType === 'Yetkili' ? 'badge-auth' : 'badge-contracted'">
              {{ supplierContractType || '-' }} Servis
            </span>
          </div>
        </div>
        <div style="border-left: 1px solid var(--border-color); padding-left: 30px;">
          <span class="profile-meta-label">🛠️ Yapabildiği Hizmetler</span>
          <div style="display: flex; gap: 6px; margin-top: 5px; flex-wrap: wrap;">
            <span class="service-tag" v-for="service in supplierServices" :key="service">
              {{ service }}
            </span>
            <span v-if="!supplierServices || supplierServices.length === 0" style="color: var(--text-muted); font-size: 0.85rem;">-</span>
          </div>
        </div>
      </div>
      <div>
        <span class="profile-meta-label">📞 İletişim Telefonu</span>
        <div class="profile-meta-value" style="font-family: monospace; font-weight: 600; color: var(--text-main); margin-top: 3px;">
          {{ supplierPhone || '-' }}
        </div>
      </div>
    </div>


    <!-- Navigation Tabs (Only for vehicle rental suppliers) -->
    <div v-if="supplierType === 'ikame_arac'" class="tab-header-container fade-in-up" style="display: flex; gap: 15px; margin-bottom: 25px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px;">
      <button @click="currentTab = 'requests'" class="tab-btn" :class="{ 'active': currentTab === 'requests' }">
        📋 Atanan Talepler
      </button>
      <button @click="currentTab = 'tenders'" class="tab-btn" :class="{ 'active': currentTab === 'tenders' }">
        🏢 Karşı Teklif & Kiralama İhaleleri
      </button>
      <button @click="currentTab = 'my_vehicles'" class="tab-btn" :class="{ 'active': currentTab === 'my_vehicles' }">
        🚗 Teslim Edilen Araçlar
      </button>
    </div>

    <main class="supplier-main fade-in-up">
      <!-- 1. REQUESTS TAB -->
      <div v-if="currentTab === 'requests'">
        <!-- Stats Dashboard -->
        <div class="grid-4" style="gap: 20px; margin-bottom: 30px;">
          <div class="glass-panel stat-card-new">
            <div class="stat-icon-wrapper quote-purple">
              <span>📥</span>
            </div>
            <div class="stat-info">
              <span class="stat-label">Toplam Hizmet Talebi</span>
              <div class="stat-val-new">{{ filteredRequests.length }}</div>
            </div>
          </div>
          <div class="glass-panel stat-card-new">
            <div class="stat-icon-wrapper quote-red">
              <span>⏳</span>
            </div>
            <div class="stat-info">
              <span class="stat-label">Bekleyen Talepler</span>
              <div class="stat-val-new" style="color: #ef4444;">{{ pendingRequestsCount }}</div>
            </div>
          </div>
          <div class="glass-panel stat-card-new">
            <div class="stat-icon-wrapper quote-blue">
              <span>⚙️</span>
            </div>
            <div class="stat-info">
              <span class="stat-label">İşlemdekiler</span>
              <div class="stat-val-new" style="color: #3b82f6;">{{ activeRequestsCount }}</div>
            </div>
          </div>
          <div class="glass-panel stat-card-new">
            <div class="stat-icon-wrapper quote-green">
              <span>✅</span>
            </div>
            <div class="stat-info">
              <span class="stat-label">Tamamlananlar</span>
              <div class="stat-val-new" style="color: #10b981;">{{ completedRequestsCount }}</div>
            </div>
          </div>
        </div>


        <!-- 🏢 3-COLUMN OPERATIONAL DASHBOARD (From User Screenshots 1 & 2) -->
        <div class="grid-3" style="gap: 20px; margin-bottom: 30px; grid-template-columns: 1fr 1fr 1fr; align-items: start;">
          <!-- COLUMN 1: Kiralamalar & Açık Bakiyeler -->
          <div class="widget-list-card">
            <div class="widget-title-row">
              <h3>Kiralamalar</h3>
            </div>
            <div class="widget-list-items">
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬆️</div><span>Çıkış</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬇️</div><span>Dönüş</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #fef2f2;">🔻</div><span>Uzun Dönem Dönüş <span style="font-size: 0.72rem; color: #94a3b8;">(Önümüzdeki 1 ay)</span></span></div>
                <span class="widget-item-value" style="color: #dc2626; font-weight: 800;">3</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">🚗</div><span>Transfer Bekleyen</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏳</div><span>Dönüş Bekleyen (Bugün)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏳</div><span>Dönüş Bekleyen (Yarın)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏳</div><span>Bekleyen Provizyon İadeleri</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #fef2f2;">⏰</div><span>Zamanaşımı</span></div>
                <span class="widget-item-value" style="color: #dc2626; font-weight: 800;">4</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">ℹ️</div><span>Kabis Bildirimi Yapılmayan</span></div>
                <span class="widget-item-value">0</span>
              </div>
            </div>

            <!-- Açık Bakiyeler section inside Column 1 -->
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #f1f5f9;">
              <h4 style="font-size: 0.95rem; font-weight: 800; color: #0f172a; margin-bottom: 12px;">Açık Bakiyeler</h4>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #eff6ff; color: #2563eb;">₺</div><span>Müşteri</span></div>
                <span class="widget-item-value" style="color: #0f172a; font-weight: bold;">115.493,07 / 9</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #eff6ff; color: #2563eb;">₺</div><span>Firma</span></div>
                <span class="widget-item-value" style="color: #0f172a; font-weight: bold;">3.162.494,46 / 23</span>
              </div>
            </div>
          </div>

          <!-- COLUMN 2: Rezervasyonlar, BAF & Onay Bekleyenler -->
          <div class="widget-list-card">
            <div class="widget-title-row">
              <h3>Rezervasyonlar</h3>
            </div>
            <div class="widget-list-items">
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">📅</div><span>Gelecek Rezervasyonlar</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬆️</div><span>Çıkış Bekleyen (Bugün)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬆️</div><span>Çıkış Bekleyen (Yarın)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">📅</div><span>İptal (Bugün)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">📅</div><span>Sözleşmede (Bugün)</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #fefce8;">⚠️</div><span>Plakasız Rezervasyon</span></div>
                <span class="widget-item-value">0</span>
              </div>
            </div>

            <!-- BAF section inside Column 2 -->
            <div style="margin-top: 18px; padding-top: 15px; border-top: 1px solid #f1f5f9;">
              <h4 style="font-size: 0.95rem; font-weight: 800; color: #0f172a; margin-bottom: 12px;">BAF</h4>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">🚗</div><span>BAF'daki Araçlar</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏰</div><span>Zamanaşımı</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">🚗</div><span>Bugün Bitecek</span></div>
                <span class="widget-item-value">0</span>
              </div>
            </div>

            <!-- Onay Bekleyenler section inside Column 2 -->
            <div style="margin-top: 18px; padding-top: 15px; border-top: 1px solid #f1f5f9;">
              <h4 style="font-size: 0.95rem; font-weight: 800; color: #0f172a; margin-bottom: 12px;">Onay Bekleyenler</h4>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏰</div><span>Bayi Kira</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏰</div><span>Kısa/Uzun Dönem Kiralamalar</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏰</div><span>Kısa/Uzun Dönem Rezervasyon</span></div>
                <span class="widget-item-value">0</span>
              </div>
            </div>
          </div>

          <!-- COLUMN 3: Servis & Araçlar -->
          <div class="widget-list-card">
            <div class="widget-title-row">
              <h3>Servis</h3>
            </div>
            <div class="widget-list-items">
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">🔧</div><span>Servisteki Araçlar</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏳</div><span>Bekleyen Talepler</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">📄</div><span>Açık Servis Dosyası</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬆️</div><span>Servise Teslim Et</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⬇️</div><span>Servisten Al</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">⏰</div><span>Zamanaşımı</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">🚗</div><span>İkame Talep</span></div>
                <span class="widget-item-value">0</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #dcfce7; color: #16a34a;">⏱️</div><span>Ort. Hasar Onarım Süresi</span></div>
                <span class="widget-item-value" style="color: #16a34a;">0.00 Gün</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #dcfce7; color: #16a34a;">⏱️</div><span>Ort. Bakım Süresi</span></div>
                <span class="widget-item-value" style="color: #16a34a;">0.00 Gün</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #dcfce7; color: #16a34a;">⏱️</div><span>Ort. Mekanik Onarım Süresi</span></div>
                <span class="widget-item-value" style="color: #16a34a;">0.00 Gün</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #dcfce7; color: #16a34a;">⏱️</div><span>Ort. Serviste Kalma Süresi</span></div>
                <span class="widget-item-value" style="color: #16a34a;">0.00 Gün</span>
              </div>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon" style="background: #dcfce7; color: #16a34a;">⏱️</div><span>Ort. Onarım Süresi</span></div>
                <span class="widget-item-value" style="color: #16a34a;">0.00 Gün</span>
              </div>
            </div>

            <!-- Araçlar section inside Column 3 -->
            <div style="margin-top: 18px; padding-top: 15px; border-top: 1px solid #f1f5f9;">
              <h4 style="font-size: 0.95rem; font-weight: 800; color: #0f172a; margin-bottom: 12px;">Araçlar</h4>
              <div class="widget-item-row">
                <div class="widget-item-left"><div class="widget-item-icon">→</div><span>Aktif Transferler</span></div>
                <span class="widget-item-value">0</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Request Table -->
        <div class="glass-panel" style="padding: 25px;">
          <h3 style="margin-bottom: 20px; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
            📋 Atanan Hizmet Talepleri Listesi
          </h3>

          <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>
          <div v-else-if="filteredRequests.length === 0" class="empty-state">
            <span style="font-size: 3rem; display: block; margin-bottom: 15px;">📥</span>
            <p style="font-size: 1.05rem; font-weight: 500;">Henüz adınıza atanmış aktif bir hizmet talebi bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Talep ID</th>
                  <th>Araç Plaka & Detay</th>
                  <th>İşlem Detayları & Açıklama</th>
                  <th>Servis Sağlayıcı</th>
                  <th>Oluşturulma</th>
                  <th>Güncel Durum</th>
                  <th style="width: 180px;">Durum Güncelle</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="req in filteredRequests" :key="req.id">
                  <td><strong style="color: var(--primary);">#{{ req.id }}</strong></td>
                  <td>
                    <span class="plate-badge">{{ req.vehicle_plate }}</span>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 5px;">{{ req.vehicle_brand_model }}</div>
                  </td>
                  <td>
                    <div class="req-description-cell">
                      <p style="margin-bottom: 6px; font-weight: 500;">{{ req.description }}</p>
                      
                      <!-- Dynamic Details display -->
                      <div class="details-mini-box" v-if="req.details">
                        <span v-if="req.details.appointment_date">📅 <strong>Randevu:</strong> {{ formatDate(req.details.appointment_date) }}</span>
                        <span v-if="req.details.tire_type">🛞 <strong>Lastik:</strong> {{ req.details.tire_type }}</span>
                        <span v-if="req.details.location">📍 <strong>Konum:</strong> {{ req.details.location }}</span>
                        <span v-if="req.details.vehicle_class">🚗 <strong>Sınıf:</strong> {{ req.details.vehicle_class }}</span>
                      </div>
                    </div>
                  </td>
                  <td>{{ getSupplierName(req.supplier_id) }}</td>
                  <td>{{ formatDate(req.created_at) }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(req.status)">{{ req.status }}</span>
                  </td>
                  <td>
                    <div class="action-dropdown-container">
                      <select 
                        @change="updateStatus(req.id, $event.target.value)" 
                        class="form-select status-select-mini"
                        :value="req.status"
                        :disabled="updatingId === req.id"
                      >
                        <option value="Beklemede">Beklemede</option>
                        <option value="Onaylandı">Onaylandı</option>
                        <option value="İşlemde">İşlemde</option>
                        <option value="Tamamlandı">Tamamlandı</option>
                        <option value="İptal Edildi">İptal Et</option>
                      </select>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 2. TENDERS TAB -->
      <div v-if="currentTab === 'tenders'">
        <div class="glass-panel" style="padding: 25px;">
          <h3 style="margin-bottom: 10px; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
            🏢 Karşı Teklif ve Kiralama İhaleleri
          </h3>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">
            Müşteriler tarafından açılan aktif araç kiralama taleplerini inceleyin ve şirketinize ait karşı fiyat tekliflerini gönderin.
          </p>

          <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>
          <div v-else-if="openQuotes.length === 0" class="empty-state">
            <span style="font-size: 3rem; display: block; margin-bottom: 15px;">🏢</span>
            <p style="font-size: 1.05rem; font-weight: 500;">Şu an teklif toplayan aktif bir kiralama talebi bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Talep ID</th>
                  <th>Segment & Tip</th>
                  <th>Araç Adedi</th>
                  <th>Süre & Yıllık KM Sınırı</th>
                  <th>Müşteri Öngörülen Fiyatı</th>
                  <th>Karşı Teklif Durumunuz</th>
                  <th>İşlem / Teslimat</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in openQuotes" :key="q.id">
                  <td><strong style="color: #10b981;">#{{ q.id }}</strong></td>
                  <td>
                    <strong>{{ q.vehicle_segment }} Segment</strong> - {{ q.vehicle_type }}
                  </td>
                  <td>
                    <span class="plate-badge" style="background: rgba(16, 185, 129, 0.1); color: #10b981; font-weight: bold; border: 1px solid rgba(16, 185, 129, 0.2);">
                      {{ q.vehicle_count }} Araç
                    </span>
                  </td>
                  <td>
                    <div>{{ q.duration_months }} Ay</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">{{ q.estimated_annual_mileage?.toLocaleString() }} km/yıl</div>
                  </td>
                  <td>
                    <strong style="color: var(--text-muted);">₺{{ q.monthly_price_try?.toLocaleString() }}</strong>
                  </td>
                  <td>
                    <div v-if="hasSupplierBid(q.id)">
                      <span class="badge badge-active" style="display: block; margin-bottom: 4px; font-size: 0.8rem; padding: 4px 8px;">
                        Karşı Teklifiniz: ₺{{ getSupplierBidAmount(q.id)?.toLocaleString() }}
                      </span>
                      <span class="badge" :class="getBidBadgeClassForSupplier(getSupplierBidStatus(q.id))" style="font-size: 0.7rem;">
                        {{ getSupplierBidStatus(q.id) }}
                      </span>
                    </div>
                    <span v-else class="badge badge-roadside">Karşı Teklif İletilmedi</span>
                  </td>
                  <td>
                    <div style="display: flex; gap: 8px;">
                      <button @click="openPlaceBidModal(q)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.85rem; background: rgba(16, 185, 129, 0.05); color: #10b981; border-color: rgba(16, 185, 129, 0.2);">
                        {{ hasSupplierBid(q.id) ? '✍ Karşı Teklifi Güncelle' : '➕ Karşı Teklif Ver' }}
                      </button>
                      <button v-if="q.status === 'Sözleşme İmzalandı' || getSupplierBidStatus(q.id) === 'Kabul Edildi'" @click="openDeliveryModal(q)" class="btn btn-primary" style="padding: 6px 12px; font-size: 0.85rem; background: #7c3aed; color: #fff; border: none;">
                        🚚 Araç Teslim Et
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 3. MY VEHICLES TAB -->
      <div v-if="currentTab === 'my_vehicles'">
        <div class="glass-panel" style="padding: 25px;">
          <h3 style="margin-bottom: 10px; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
            🚗 Teslim Edilen Araçlar ve Filo Takibi
          </h3>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 25px;">
            Müşterilere teslim ettiğiniz kiralık araçları takip edin. Araçlara açılmış olan servis, muayene ve diğer talep kayıtlarını inceleyin.
          </p>

          <div v-if="loading" class="text-center" style="padding: 50px 0;">Yükleniyor...</div>
          <div v-else-if="myDeliveredVehicles.length === 0" class="empty-state">
            <span style="font-size: 3rem; display: block; margin-bottom: 15px;">🚗</span>
            <p style="font-size: 1.05rem; font-weight: 500;">Henüz sisteme kayıtlı kiraladığınız bir araç bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Plaka</th>
                  <th>Marka / Model</th>
                  <th>Segment / Tip</th>
                  <th>Kilometre</th>
                  <th>Şasi No</th>
                  <th>Muayene Tarihi</th>
                  <th>Mevcut Durum</th>
                  <th>Aksiyon</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in myDeliveredVehicles" :key="v.id">
                  <td><span class="plate-badge">{{ v.plate }}</span></td>
                  <td><strong>{{ v.brand }} {{ v.model }}</strong> ({{ v.year }})</td>
                  <td>{{ v.vehicle_segment }} - {{ v.vehicle_type }}</td>
                  <td>{{ v.mileage?.toLocaleString() }} km</td>
                  <td style="font-family: monospace; font-size: 0.85rem;">{{ v.chassis_no }}</td>
                  <td>{{ v.inspection_date }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClassForVehicle(v.status)">
                      {{ v.status }}
                    </span>
                  </td>
                  <td>
                    <button @click="openVehicleDetails(v)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">
                      🔍 Detay & Servis Kayıtları
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- Bid Placement Modal -->
  <div v-if="showBidModal" class="modal-overlay" @click.self="showBidModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 480px; padding: 30px;">
      <h2 style="margin-bottom: 10px; color: #10b981; display: flex; align-items: center; gap: 10px;">
        <span>🏢</span> Araç Kiralama Karşı Teklifi İlet
      </h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 20px;">
        Talep #{{ selectedQuoteForBid?.id }} için aylık toplam karşı teklif bedelinizi giriniz. (Firma: {{ selectedQuoteForBid?.company_name }})
      </p>

      <form @submit.prevent="submitBid">
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Aylık Toplam Karşı Fiyat Teklifiniz (₺)</label>
          <input type="number" min="0" v-model.number="bidForm.monthly_price_try" required class="form-input" placeholder="Aylık toplam bedel">
        </div>

        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Karşı Teklif Şartları & Teslimat Notları</label>
          <textarea v-model="bidForm.notes" rows="4" class="form-input" style="resize: none;" placeholder="Araçların teslim süreleri, lastik hizmet detayları ve kasko kapsamı gibi detayları buraya yazabilirsiniz."></textarea>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showBidModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: #10b981; color: #fff; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
            Karşı Teklifi Gönder
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Vehicle Delivery / Registration Modal -->
  <div v-if="showAddVehicleModal" class="modal-overlay" @click.self="showAddVehicleModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 550px; padding: 30px;">
      <h2 style="margin-bottom: 10px; color: #7c3aed; display: flex; align-items: center; gap: 8px;">
        <span>🚚</span> Müşteriye Araç Teslim Et / Sisteme Ekle
      </h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-bottom: 20px;">
        <strong>{{ selectedQuoteForDelivery?.company_name }}</strong> firması için onaylanan kiralama sözleşmesine istinaden teslim edeceğiniz aracın plaka ve tescil bilgilerini giriniz.
      </p>

      <form @submit.prevent="submitAddVehicle">
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Plaka</label>
            <input type="text" v-model="addVehicleForm.plate" required class="form-input" placeholder="Örn: 34 ABC 123">
          </div>
          <div class="form-group">
            <label class="form-label">Şasi No / Registry No</label>
            <input type="text" v-model="addVehicleForm.chassis_no" required class="form-input" placeholder="17 haneli şase no">
          </div>
        </div>

        <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Marka</label>
            <input type="text" v-model="addVehicleForm.brand" required class="form-input" placeholder="Örn: Renault">
          </div>
          <div class="form-group">
            <label class="form-label">Model</label>
            <input type="text" v-model="addVehicleForm.model" required class="form-input" placeholder="Örn: Megane">
          </div>
          <div class="form-group">
            <label class="form-label">Model Yılı</label>
            <input type="number" min="1990" max="2027" v-model.number="addVehicleForm.year" required class="form-input">
          </div>
        </div>

        <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Yakıt Türü</label>
            <select v-model="addVehicleForm.fuel" required class="form-select">
              <option value="Dizel">Dizel</option>
              <option value="Benzin">Benzin</option>
              <option value="Hibrit">Hibrit</option>
              <option value="Elektrik">Elektrik</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Başlangıç KM</label>
            <input type="number" min="0" v-model.number="addVehicleForm.mileage" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Ruhsat Seri No</label>
            <input type="text" v-model="addVehicleForm.license_serial_no" required class="form-input" placeholder="AB123456">
          </div>
        </div>

        <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 25px;">
          <div class="form-group">
            <label class="form-label">Araç Segmenti</label>
            <input type="text" v-model="addVehicleForm.vehicle_segment" readonly class="form-input" style="background: rgba(255,255,255,0.05); cursor: not-allowed;">
          </div>
          <div class="form-group">
            <label class="form-label">Gövde Tipi</label>
            <input type="text" v-model="addVehicleForm.vehicle_type" readonly class="form-input" style="background: rgba(255,255,255,0.05); cursor: not-allowed;">
          </div>
          <div class="form-group">
            <label class="form-label">Muayene Tarihi</label>
            <input type="date" v-model="addVehicleForm.inspection_date" required class="form-input">
          </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showAddVehicleModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: #7c3aed; color: #fff; border: none; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);">
            Aracı Teslim Et & Kaydet
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Vehicle Details & Service History Modal -->
  <div v-if="showVehicleDetailsModal" class="modal-overlay" @click.self="showVehicleDetailsModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 750px; padding: 30px;">
      <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
        <h2 style="color: #10b981; display: flex; align-items: center; gap: 8px;">
          <span>🔍</span> Araç Detayı & Servis Kartı
        </h2>
        <div style="margin-top: 5px; display: flex; gap: 12px; align-items: center;">
          <span class="plate-badge" style="font-size: 1rem;">{{ selectedVehicle?.plate }}</span>
          <span style="font-weight: 600; font-size: 1.1rem; color: var(--text-main);">{{ selectedVehicle?.brand }} {{ selectedVehicle?.model }} ({{ selectedVehicle?.year }})</span>
        </div>
      </div>

      <!-- Specs grid -->
      <div class="grid-4" style="gap: 12px; margin-bottom: 20px; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));">
        <div class="details-spec">
          <span class="d-label">Segment</span>
          <span class="d-val">{{ selectedVehicle?.vehicle_segment }}</span>
        </div>
        <div class="details-spec">
          <span class="d-label">Gövde Tipi</span>
          <span class="d-val">{{ selectedVehicle?.vehicle_type }}</span>
        </div>
        <div class="details-spec">
          <span class="d-label">Kilometre</span>
          <span class="d-val">{{ selectedVehicle?.mileage?.toLocaleString() }} km</span>
        </div>
        <div class="details-spec">
          <span class="d-label">Muayene</span>
          <span class="d-val">{{ selectedVehicle?.inspection_date }}</span>
        </div>
      </div>

      <!-- Service History List -->
      <div style="margin-top: 25px;">
        <h4 style="margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; color: var(--text-main);">🛠️ Araç Servis Kayıtları ve Talep Geçmişi</h4>
        
        <div v-if="getVehicleServiceHistory(selectedVehicle?.id).length === 0" style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.9rem; background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px solid var(--border-color);">
          Bu araç için henüz herhangi bir servis kaydı veya yardım talebi açılmamıştır.
        </div>
        
        <div v-else class="custom-table-container" style="max-height: 250px; overflow-y: auto;">
          <table class="custom-table">
            <thead>
              <tr>
                  <th>Talep ID</th>
                  <th>Hizmet Tipi</th>
                  <th>İşlem Açıklaması</th>
                  <th>Servis Sağlayıcı</th>
                  <th>Tarih</th>
                  <th>Durum</th>
              </tr>
            </thead>
            <tbody>
                  <tr v-for="rec in getVehicleServiceHistory(selectedVehicle?.id)" :key="rec.id">
      <td>#{{ rec.id }}</td>
      <td>
        <span class="badge" :class="getStatusBadgeClass(rec.status)" style="font-size: 0.75rem;">
          {{ getTypeName(rec.type) }}
        </span>
      </td>
      <td style="font-size: 0.8rem; max-width: 250px; white-space: normal;">{{ rec.description }}</td>
      <td>{{ getSupplierName(rec.supplier_id) }}</td>
      <td style="font-size: 0.8rem;">{{ formatDate(rec.created_at) }}</td>
      <td>
        <span class="badge" :class="getStatusBadgeClass(rec.status)" style="font-size: 0.75rem;">
          {{ rec.status }}
        </span>
      </td>
    </tr>


            </tbody>
          </table>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px; margin-top: 20px;">
        <button @click="showVehicleDetailsModal = false" class="btn btn-secondary">Kapat</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentTab = ref('requests') // 'requests', 'tenders', 'my_vehicles'
const supplierId = ref(parseInt(localStorage.getItem('fleetcar_supplier_id') || '0'))
const supplierName = ref(localStorage.getItem('fleetcar_supplier_name') || 'Tedarikçi')
const supplierType = ref(localStorage.getItem('fleetcar_supplier_type') || 'servis')

const supplierCity = ref('')
const supplierDistrict = ref('')
const supplierContractType = ref('')
const supplierServices = ref([])
const supplierPhone = ref('')

const requests = ref([])
const quotes = ref([])
const vehicles = ref([])
const supplierBids = ref([])
const suppliers = ref([])
const loading = ref(true)
const updatingId = ref(null)

// Bidding Modal State
const showBidModal = ref(false)
const selectedQuoteForBid = ref(null)
const bidForm = reactive({
  monthly_price_try: 0,
  notes: ''
})

// Vehicle Delivery / Registration State
const showAddVehicleModal = ref(false)
const selectedQuoteForDelivery = ref(null)
const addVehicleForm = reactive({
  plate: '',
  brand: '',
  model: '',
  year: 2024,
  fuel: 'Hibrit',
  mileage: 0,
  chassis_no: '',
  license_serial_no: '',
  inspection_date: '',
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  tire_change_date: '',
  last_service_date: '',
  last_service_mileage: 0
})

// Vehicle Details & Service History State
const showVehicleDetailsModal = ref(false)
const selectedVehicle = ref(null)

const fetchRequests = async () => {
  try {
    const res = await fetch('/api/requests')
    if (res.ok) {
      requests.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching requests:', error)
  }
}

const fetchQuotes = async () => {
  try {
    const res = await fetch('/api/quotes')
    if (res.ok) {
      quotes.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching quotes:', error)
  }
}

const fetchSupplierBids = async () => {
  try {
    const res = await fetch(`/api/suppliers/${supplierId.value}/bids`)
    if (res.ok) {
      supplierBids.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching supplier bids:', error)
  }
}

const fetchVehicles = async () => {
  try {
    const res = await fetch('/api/vehicles')
    if (res.ok) {
      vehicles.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching vehicles:', error)
  }
}

const filteredRequests = computed(() => {
  return requests.value.filter(r => r.supplier_id === supplierId.value)
})

const openQuotes = computed(() => {
  // Open quote requests or signed quotes where this supplier's bid is accepted
  return quotes.value.filter(q => {
    if (['Teklif Verildi', 'Değerlendirmede'].includes(q.status)) return true
    if (q.status === 'Sözleşme İmzalandı') {
      const bid = supplierBids.value.find(b => b.quote_id === q.id)
      return bid && bid.status === 'Kabul Edildi'
    }
    return false
  })
})

const myDeliveredVehicles = computed(() => {
  return vehicles.value.filter(v => v.supplier_id === supplierId.value)
})

const pendingRequestsCount = computed(() => {
  return filteredRequests.value.filter(r => r.status === 'Beklemede').length
})

const activeRequestsCount = computed(() => {
  return filteredRequests.value.filter(r => ['Onaylandı', 'İşlemde'].includes(r.status)).length
})

const completedRequestsCount = computed(() => {
  return filteredRequests.value.filter(r => r.status === 'Tamamlandı').length
})

const getTypeName = (type) => {
  const map = {
    'servis': 'Yetkili Servis Tedarikçisi',
    'lastik': 'Lastik Tedarikçisi',
    'yol_yardim': 'Yol Yardım & Çekici Hizmeti',
    'ikame_arac': 'Araç Kiralama & İkame Tedarikçisi'
  }
  return map[type] || type
}

const getStatusBadgeClass = (status) => {
  return {
    'badge-active': status === 'Onaylandı',
    'badge-service': status === 'İşlemde',
    'badge-replacement': status === 'Tamamlandı',
    'badge-roadside': status === 'Beklemede',
    'badge-old-reason': status === 'İptal Edildi'
  }
}

const getBidBadgeClassForSupplier = (status) => {
  return {
    'badge-active': status === 'Kabul Edildi',
    'badge-roadside': status === 'Beklemede',
    'badge-old-reason': status === 'Reddedildi'
  }
}

const getStatusBadgeClassForVehicle = (status) => {
  return {
    'badge-active': status === 'Aktif',
    'badge-service': status === 'Serviste',
    'badge-roadside': status === 'Yol Yardımında',
    'badge-old-reason': status === 'İnaktif'
  }
}

// Bidding Helpers
const hasSupplierBid = (quoteId) => {
  return supplierBids.value.some(b => b.quote_id === quoteId)
}

const getSupplierBidAmount = (quoteId) => {
  const bid = supplierBids.value.find(b => b.quote_id === quoteId)
  return bid ? bid.monthly_price_try : 0
}

const getSupplierBidStatus = (quoteId) => {
  const bid = supplierBids.value.find(b => b.quote_id === quoteId)
  return bid ? bid.status : ''
}

const openPlaceBidModal = (quote) => {
  const existing = supplierBids.value.find(b => b.quote_id === quote.id)
  bidForm.monthly_price_try = existing ? existing.monthly_price_try : quote.monthly_price_try
  bidForm.notes = existing ? existing.notes : ''
  selectedQuoteForBid.value = quote
  showBidModal.value = true
}

const submitBid = async () => {
  try {
    const res = await fetch(`/api/quotes/${selectedQuoteForBid.value.id}/bids?supplier_id=${supplierId.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(bidForm)
    })
    if (res.ok) {
      await fetchSupplierBids()
      showBidModal.value = false
    } else {
      alert('Teklif gönderilirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error submitting bid:', err)
  }
}

// Vehicle Delivery / Registration Helpers
const openDeliveryModal = (quote) => {
  selectedQuoteForDelivery.value = quote
  addVehicleForm.plate = ''
  addVehicleForm.chassis_no = ''
  addVehicleForm.brand = ''
  addVehicleForm.model = ''
  addVehicleForm.year = 2024
  addVehicleForm.fuel = 'Hibrit'
  addVehicleForm.mileage = 0
  addVehicleForm.license_serial_no = ''
  addVehicleForm.inspection_date = new Date(Date.now() + 2 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // default 2 years in future
  addVehicleForm.vehicle_segment = quote.vehicle_segment
  addVehicleForm.vehicle_type = quote.vehicle_type
  
  // Set defaults for service metadata
  addVehicleForm.tire_change_date = new Date().toISOString().split('T')[0]
  addVehicleForm.last_service_date = new Date().toISOString().split('T')[0]
  addVehicleForm.last_service_mileage = 0
  
  showAddVehicleModal.value = true
}

const submitAddVehicle = async () => {
  try {
    const payload = {
      ...addVehicleForm,
      supplier_id: supplierId.value
    }
    const res = await fetch('/api/vehicles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      await fetchVehicles()
      showAddVehicleModal.value = false
      alert(`${addVehicleForm.plate} plakalı araç başarıyla sisteme teslim edildi ve müşterinin filosuna kaydedildi.`);
    } else {
      const errData = await res.json()
      alert('Araç kaydedilemedi: ' + (errData.detail || 'Bilinmeyen hata.'))
    }
  } catch (err) {
    console.error('Error registering vehicle:', err)
  }
}

// Vehicle Details & Service History Helpers
const openVehicleDetails = (vehicle) => {
  selectedVehicle.value = vehicle
  showVehicleDetailsModal.value = true
}

const getVehicleServiceHistory = (vehicleId) => {
  if (!vehicleId) return []
  return requests.value.filter(r => r.vehicle_id === vehicleId)
}

const updateStatus = async (requestId, newStatus) => {
  updatingId.value = requestId
  try {
    const response = await fetch(`/api/requests/${requestId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status: newStatus })
    })
    if (response.ok) {
      await fetchRequests()
    } else {
      alert('Durum güncellenirken bir hata oluştu.')
    }
  } catch (error) {
    console.error('Error updating status:', error)
    alert('Sistem bağlantı hatası.')
  } finally {
    updatingId.value = null
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleString('tr-TR')
  } catch (e) {
    return dateStr
  }
}

const getSupplierName = (supplierId) => {
  const sup = suppliers.value.find(s => s.id === supplierId)
  return sup ? sup.name : '-'
}

const handleLogout = () => {
  localStorage.removeItem('fleetcar_supplier_token')
  localStorage.removeItem('fleetcar_supplier_id')
  localStorage.removeItem('fleetcar_supplier_name')
  localStorage.removeItem('fleetcar_supplier_type')
  router.push('/supplier-login')
}

onMounted(async () => {
  if (!supplierId.value) {
    router.push('/supplier-login')
    return
  }
  
  loading.value = true
  // Load supplier details
  try {
    const res = await fetch('/api/suppliers')
    if (res.ok) {
      const suppliersList = await res.json()
      const current = suppliersList.find(s => s.id === supplierId.value)
      if (current) {
        supplierCity.value = current.city
        supplierDistrict.value = current.district
        supplierContractType.value = current.contract_type
        supplierServices.value = current.services
        suppliers.value = suppliersList
        supplierName.value = current.name
        supplierType.value = current.type
      }
    }
  } catch (err) {
    console.error('Error loading supplier info:', err)
  }
  
  await Promise.all([
    fetchRequests(),
    fetchQuotes(),
    fetchSupplierBids(),
    fetchVehicles()
  ])
  loading.value = false
})
</script>

<style scoped>
.supplier-layout {
  min-height: 100vh;
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.supplier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  margin-bottom: 30px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 15px;
}

.portal-title {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-supplier {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
}

.supplier-name-display {
  font-size: 1.35rem;
  font-weight: 700;
  margin-top: 2px;
}

.type-badge {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.profile-bar {
  border-top: 3px solid #10b981 !important; /* Premium top border accent instead of left */
}

/* Stat Cards Styling */
.stat-card-new {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 16px;
  background: #ffffff;
}

.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  flex-shrink: 0;
}

.quote-purple {
  background: rgba(124, 58, 237, 0.1);
  color: #7c3aed;
}

.quote-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.quote-green {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.quote-red {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-label {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-dark);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-val-new {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--text-main);
  line-height: 1.2;
}


.profile-meta-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

.contract-badge {
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.badge-auth {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-contracted {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.service-tag {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.btn-danger-hover:hover {
  background: rgba(239, 68, 68, 0.1) !important;
  color: #ef4444 !important;
  border-color: rgba(239, 68, 68, 0.2) !important;
}

/* Tabs style */
.tab-btn {
  border: none;
  background: transparent;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn.active {
  color: #10b981 !important;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -11px;
  left: 0;
  right: 0;
  height: 2px;
  background: #10b981;
}

/* Spec labels inside details */
.details-spec {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.d-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.d-val {
  font-size: 0.95rem;
  font-weight: 700;
  margin-top: 4px;
  color: var(--text-main);
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
