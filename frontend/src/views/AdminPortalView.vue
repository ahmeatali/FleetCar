<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <!-- Admin Sidebar -->
    <aside class="portal-sidebar admin-sidebar">
      <router-link to="/admin-portal" class="nav-logo" style="margin-bottom: 25px;">
        <div class="nav-logo-icon" style="background: linear-gradient(135deg, #7c3aed, #db2777);">F</div>
        <span>FC Yönetici</span>
      </router-link>

      <div class="admin-profile">
        <div class="avatar">⚙️</div>
        <div>
          <h4 style="font-size: 0.85rem; font-weight: 600;">Yönetici Paneli</h4>
          <span style="font-size: 0.7rem; color: #a78bfa;">Django Admin Bağlantılı</span>
        </div>
      </div>

      <ul class="sidebar-menu">
        <li>
          <a href="#" @click.prevent="activeTab = 'quotes'" class="sidebar-link" :class="{ 'active-admin': activeTab === 'quotes' }">
            <span class="icon">📑</span>
            <span>Gelen Teklifler</span>
          </a>
        </li>
        <li>
          <a href="#" @click.prevent="activeTab = 'customers'" class="sidebar-link" :class="{ 'active-admin': activeTab === 'customers' }">
            <span class="icon">👥</span>
            <span>Aktif Müşteriler</span>
          </a>
        </li>
        <li>
          <a href="#" @click.prevent="activeTab = 'suppliers'" class="sidebar-link" :class="{ 'active-admin': activeTab === 'suppliers' }">
            <span class="icon">🏢</span>
            <span>Tedarikçiler</span>
          </a>
        </li>
      </ul>

      <div style="margin-top: auto;">
        <button @click="logout" class="sidebar-link" style="width: 100%; border: none; background: transparent; cursor: pointer; text-align: left; color: #fecdd3;">
          <span class="icon">🚪</span>
          <span>Çıkış Yap</span>
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="portal-main fade-in-up">
      <!-- 1. QUOTES TAB -->
      <div v-if="activeTab === 'quotes'">
        <header class="dashboard-header">
          <div>
            <h1>Müşteri Kiralama Teklifleri</h1>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Anasayfadan gelen dinamik teklif taleplerini inceleyin veya manuel yeni talep oluşturun.</p>
          </div>
          <button @click="showAddQuoteModal = true" class="btn btn-primary" style="background: linear-gradient(135deg, #7c3aed, #db2777); border: none; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);">
            ➕ Yeni Teklif Talebi Ekle
          </button>
        </header>

        <!-- Stats Summary cards -->
        <div class="grid-3" style="margin-top: 30px; gap: 20px;">
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Toplam Teklif Talebi</span>
              <span class="stat-icon">📄</span>
            </div>
            <div class="stat-value">{{ quotes.length }} Adet</div>
          </div>
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Öngörülen Toplam Araç</span>
              <span class="stat-icon">🚗</span>
            </div>
            <div class="stat-value">{{ totalProposedVehicles }} Adet</div>
          </div>
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Tahmini Aylık Toplam Ciro</span>
              <span class="stat-icon">₺</span>
            </div>
            <div class="stat-value" style="color: #7c3aed;">₺{{ totalProposedRevenue.toLocaleString('tr-TR') }}</div>
          </div>
        </div>

        <!-- Proposals Table -->
        <div class="glass-panel" style="margin-top: 30px; padding: 15px;">
          <div v-if="loading" class="text-center" style="padding: 40px 0;">Yükleniyor...</div>
          <div v-else-if="quotes.length === 0" class="empty-state">
            <p>Henüz gelen teklif talebi bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Şirket Adı</th>
                  <th>İletişim</th>
                  <th>Araç Adedi</th>
                  <th>Segment & Tip</th>
                  <th>Süre & Yıllık KM</th>
                  <th>Aylık Bedel</th>
                  <th>Durum</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="quote in quotes" :key="quote.id">
                  <td>#{{ quote.id }}</td>
                  <td><strong>{{ quote.company_name }}</strong></td>
                  <td>
                    <div style="font-size: 0.85rem; font-weight: 500;">{{ quote.email }}</div>
                    <div style="font-size: 0.75rem; color: var(--text-dark);">{{ quote.phone }}</div>
                  </td>
                  <td><span class="plate-badge" style="background: rgba(124, 58, 237, 0.1); color: #7c3aed; font-weight: bold; border: 1px solid rgba(124, 58, 237, 0.2);">{{ quote.vehicle_count }} Araç</span></td>
                  <td>
                    <span style="font-weight: 700;">{{ quote.vehicle_segment }}</span> - {{ quote.vehicle_type }}
                  </td>
                  <td>
                    <div>{{ quote.duration_months }} Ay</div>
                    <div style="font-size: 0.75rem; color: var(--text-dark);">{{ quote.estimated_annual_mileage?.toLocaleString() }} km/yıl</div>
                  </td>
                  <td>
                    <strong style="color: #7c3aed;">₺{{ quote.monthly_price_try?.toLocaleString() }}</strong>
                  </td>
                  <td>
                    <select 
                      v-model="quote.status" 
                      @change="onStatusChange(quote.id, quote.status)" 
                      class="form-select status-select"
                      :class="getStatusClass(quote.status)"
                    >
                      <option value="Teklif Verildi">Teklif Verildi</option>
                      <option value="Değerlendirmede">Değerlendirmede</option>
                      <option value="Sözleşme İmzalandı">Sözleşme İmzalandı</option>
                      <option value="Reddedildi">Reddedildi</option>
                    </select>
                  </td>
                  <td>
                    <div style="display: flex; gap: 8px;">
                      <button @click="openEditQuoteModal(quote)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">
                        ⚙️ Düzenle
                      </button>
                      <button @click="openQuoteBidsModal(quote)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem; background: rgba(124, 58, 237, 0.05); color: #7c3aed; border-color: rgba(124, 58, 237, 0.2);">
                        🏢 Tedarikçi Teklifleri
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 2. CUSTOMERS TAB -->
      <div v-if="activeTab === 'customers' && !showCustomerDetailsModal">
        <header class="dashboard-header">
          <div>
            <h1>Aktif Müşteriler (Sözleşmeli Portföy)</h1>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Sadece kiralama sözleşmesi imzalanmış ve onaylanmış aktif kurumsal müşteriler.</p>
          </div>
        </header>

        <!-- Stats cards for customers -->
        <div class="grid-3" style="margin-top: 30px; gap: 20px;">
          <div class="glass-panel stat-card admin-stat" style="border-left-color: #10b981 !important;">
            <div class="stat-header">
              <span>Aktif Sözleşmeli Şirket</span>
              <span class="stat-icon">🏢</span>
            </div>
            <div class="stat-value">{{ customers.length }} Şirket</div>
          </div>
          <div class="glass-panel stat-card admin-stat" style="border-left-color: #10b981 !important;">
            <div class="stat-header">
              <span>Toplam Filo Aracı</span>
              <span class="stat-icon">🚗</span>
            </div>
            <div class="stat-value">{{ totalCustomerVehicles }} Araç</div>
          </div>
          <div class="glass-panel stat-card admin-stat" style="border-left-color: #10b981 !important;">
            <div class="stat-header">
              <span>Toplam Aktif Ciro</span>
              <span class="stat-icon">₺</span>
            </div>
            <div class="stat-value" style="color: #10b981;">₺{{ totalCustomerRevenue.toLocaleString('tr-TR') }}</div>
          </div>
        </div>

        <!-- Customers Table -->
        <div class="glass-panel" style="margin-top: 30px; padding: 15px;">
          <div v-if="loading" class="text-center" style="padding: 40px 0;">Yükleniyor...</div>
          <div v-else-if="customers.length === 0" class="empty-state">
            <p>Henüz sözleşmesi imzalanmış aktif bir müşteri bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Şirket Adı</th>
                  <th>Ticari Unvan</th>
                  <th>İletişim</th>
                  <th>Filo Durumu</th>
                  <th>Sözleşme Bedeli (Aylık)</th>
                  <th>İmza Tarihi</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in customers" :key="c.id" class="customer-row" @click="openCustomerDetails(c)" style="cursor: pointer;">
                  <td>#{{ c.id }}</td>
                  <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                      <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #10b981, #059669); display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: 700; color: #fff; flex-shrink: 0;">
                        {{ c.company_name?.charAt(0) }}
                      </div>
                      <div>
                        <div style="font-weight: 700; color: var(--text-primary);">{{ c.company_name }}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Detayları gör →</div>
                      </div>
                    </div>
                  </td>
                  <td style="font-size: 0.85rem; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {{ c.legal_title }}
                  </td>
                  <td>
                    <div style="font-size: 0.85rem; font-weight: 500;">{{ c.email }}</div>
                    <div style="font-size: 0.75rem; color: var(--text-dark);">{{ c.phone }}</div>
                  </td>
                  <td>
                    <div style="display: flex; flex-direction: column; gap: 4px; min-width: 140px;">
                      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
                        <span style="color: var(--text-muted);">Sözleşme</span>
                        <span style="font-weight: 700; color: var(--text-primary);">{{ c.registered_vehicles_count }} araç</span>
                      </div>
                      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
                        <span style="color: var(--text-muted);">Tanımlı</span>
                        <span style="font-weight: 700; color: #10b981;">{{ c.actual_vehicle_count }} araç</span>
                      </div>
                      <div v-if="c.vehicle_deficit > 0" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; background: rgba(239,68,68,0.08); border-radius: 6px; padding: 2px 6px;">
                        <span style="color: #f87171;">Eksik</span>
                        <span style="font-weight: 700; color: #f87171;">{{ c.vehicle_deficit }} araç</span>
                      </div>
                      <div v-else style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; background: rgba(16,185,129,0.08); border-radius: 6px; padding: 2px 6px;">
                        <span style="color: #10b981;">✓ Tam</span>
                        <span style="font-weight: 700; color: #10b981;">Eksiksiz</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <strong style="color: #10b981;">₺{{ c.contract_amount?.toLocaleString() }}</strong>
                  </td>
                  <td>{{ formatDate(c.signed_at) }}</td>
                  <td>
                    <button @click.stop="openEditCustomerModal(c)" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">
                      ⚙️ Düzenle
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- CUSTOMER DETAIL DASHBOARD (fullscreen panel) -->
      <div v-if="showCustomerDetailsModal && selectedCustomerDetails" class="customer-detail-dashboard fade-in-up">
        <!-- Back Header -->
        <div class="cd-topbar">
          <button @click="closeCustomerDetails" class="cd-back-btn">
            ← Müşteri Listesine Dön
          </button>
          <div class="cd-topbar-actions">
            <button @click.stop="openEditCustomerModal(selectedCustomerDetails)" class="btn btn-secondary" style="font-size: 0.85rem;">
              ⚙️ Müşteri Düzenle
            </button>
          </div>
        </div>

        <!-- Company Hero -->
        <div class="cd-hero glass-panel">
          <div class="cd-hero-avatar">{{ selectedCustomerDetails.company_name?.charAt(0) }}</div>
          <div class="cd-hero-info">
            <h2 class="cd-company-name">{{ selectedCustomerDetails.company_name }}</h2>
            <p class="cd-legal-title">{{ selectedCustomerDetails.legal_title }}</p>
            <div class="cd-contact-row">
              <span>✉️ {{ selectedCustomerDetails.email }}</span>
              <span>📞 {{ selectedCustomerDetails.phone }}</span>
              <span v-if="selectedCustomerDetails.address">📍 {{ selectedCustomerDetails.address }}</span>
            </div>
          </div>
          <div class="cd-hero-badges">
            <div class="cd-hero-badge cd-badge-green">
              <div class="cd-badge-label">Kayıtlı Araç</div>
              <div class="cd-badge-value">{{ customerVehicles.length }}</div>
            </div>
            <div class="cd-hero-badge cd-badge-purple">
              <div class="cd-badge-label">Aylık Sözleşme</div>
              <div class="cd-badge-value">₺{{ selectedCustomerDetails.contract_amount?.toLocaleString('tr-TR') }}</div>
            </div>
            <div class="cd-hero-badge cd-badge-blue">
              <div class="cd-badge-label">İmza Tarihi</div>
              <div class="cd-badge-value">{{ formatDate(selectedCustomerDetails.signed_at) }}</div>
            </div>
            <div class="cd-hero-badge cd-badge-amber">
              <div class="cd-badge-label">Toplam Servis</div>
              <div class="cd-badge-value">{{ customerServices.length }}</div>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="cd-tabs">
          <button :class="['cd-tab', { 'cd-tab-active': detailTab === 'vehicles' }]" @click="detailTab = 'vehicles'">
            🚗 Araçlar ({{ customerVehicles.length }})
          </button>
          <button :class="['cd-tab', { 'cd-tab-active': detailTab === 'services' }]" @click="detailTab = 'services'">
            🔧 Servis Geçmişi ({{ customerServices.length }})
          </button>
        </div>

        <!-- VEHICLES TAB -->
        <div v-if="detailTab === 'vehicles'" class="cd-tab-content">
          <div v-if="customerVehicles.length === 0" class="empty-state">
            <p>Bu müşteriye ait kayıtlı araç bulunamadı.</p>
          </div>
          <div v-else class="cd-vehicle-grid">
            <div v-for="v in customerVehicles" :key="v.id" class="cd-vehicle-card glass-panel">
              <div class="cd-vehicle-header">
                <div class="cd-plate">{{ v.plate }}</div>
                <span class="badge" :class="v.status === 'Aktif' ? 'badge-active' : v.status === 'Serviste' ? 'badge-service' : 'badge-roadside'" style="font-size: 0.75rem;">{{ v.status }}</span>
              </div>
              <div class="cd-vehicle-title">{{ v.brand }} {{ v.model }} ({{ v.year }})</div>
              <div class="cd-vehicle-details">
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Segment / Tip</span>
                  <span class="cd-vd-val">{{ v.vehicle_segment }} / {{ v.vehicle_type }}</span>
                </div>
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Yakıt</span>
                  <span class="cd-vd-val">{{ v.fuel }}</span>
                </div>
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Kilometre</span>
                  <span class="cd-vd-val" style="color: #7c3aed; font-weight: 700;">{{ v.mileage?.toLocaleString('tr-TR') }} km</span>
                </div>
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Muayene Tarihi</span>
                  <span class="cd-vd-val">{{ v.inspection_date || '—' }}</span>
                </div>
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Son Servis</span>
                  <span class="cd-vd-val">{{ v.last_service_date || '—' }}</span>
                </div>
                <div class="cd-vehicle-row">
                  <span class="cd-vd-label">Şase No</span>
                  <span class="cd-vd-val" style="font-family: monospace; font-size: 0.78rem;">{{ v.chassis_no }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- SERVICES TAB -->
        <div v-if="detailTab === 'services'" class="cd-tab-content">
          <div v-if="customerServices.length === 0" class="empty-state">
            <p>Bu müşteriye ait servis kaydı bulunamadı.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Araç</th>
                  <th>Tedarikçi / Servis</th>
                  <th>Hizmet Türü</th>
                  <th>Açıklama</th>
                  <th>Durum</th>
                  <th>Tarih</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in customerServices" :key="s.id">
                  <td style="color: var(--text-muted);">#{{ s.id }}</td>
                  <td>
                    <div style="font-weight: 600;">{{ s.vehicle_plate }}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">{{ s.vehicle_brand_model }}</div>
                  </td>
                  <td>
                    <div style="font-weight: 600;">{{ s.supplier_name }}</div>
                  </td>
                  <td>
                    <span class="badge" :class="getCategoryBadgeClass(s.type)" style="font-size: 0.78rem; padding: 4px 10px;">
                      {{ getTypeName(s.type) }}
                    </span>
                  </td>
                  <td style="font-size: 0.85rem; max-width: 220px; white-space: normal; line-height: 1.4;">{{ s.description }}</td>
                  <td>
                    <span class="badge" :class="s.status === 'Tamamlandı' ? 'badge-active' : s.status === 'Beklemede' ? 'badge-roadside' : 'badge-service'" style="font-size: 0.75rem;">
                      {{ s.status }}
                    </span>
                  </td>
                  <td style="font-size: 0.82rem;">{{ s.created_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 3. SUPPLIERS TAB -->
      <div v-if="activeTab === 'suppliers'">
        <header class="dashboard-header">
          <div>
            <h1>Entegre Tedarikçiler Listesi</h1>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Sistemde entegre çalışan yetkili/anlaşmalı servis, lastik, yol yardım ve ikame araç sağlayıcıları.</p>
          </div>
          <button @click="showAddSupplierModal = true" class="btn btn-primary" style="background: linear-gradient(135deg, #7c3aed, #3b82f6); border: none; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.25);">
            ➕ Yeni Tedarikçi Ekle
          </button>
        </header>

        <!-- Stats cards for suppliers -->
        <div class="grid-3" style="margin-top: 30px; gap: 20px;">
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Toplam Entegre Tedarikçi</span>
              <span class="stat-icon">🏢</span>
            </div>
            <div class="stat-value">{{ suppliers.length }} Tedarikçi</div>
          </div>
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Yetkili Servisler</span>
              <span class="stat-icon" style="color: #10b981;">🛡️</span>
            </div>
            <div class="stat-value" style="color: #10b981;">{{ authorizedSuppliersCount }} Adet</div>
          </div>
          <div class="glass-panel stat-card admin-stat">
            <div class="stat-header">
              <span>Anlaşmalı Servisler</span>
              <span class="stat-icon" style="color: #3b82f6;">🤝</span>
            </div>
            <div class="stat-value" style="color: #3b82f6;">{{ contractedSuppliersCount }} Adet</div>
          </div>
        </div>

        <!-- Suppliers Table -->
        <div class="glass-panel" style="margin-top: 30px; padding: 15px;">
          <div v-if="loading" class="text-center" style="padding: 40px 0;">Yükleniyor...</div>
          <div v-else-if="suppliers.length === 0" class="empty-state">
            <p>Sistemde kayıtlı tedarikçi bulunmuyor.</p>
          </div>
          <div v-else class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Tedarikçi Adı</th>
                  <th>Kategori</th>
                  <th>Servis Tipi</th>
                  <th>İl / İlçe</th>
                  <th>İletişim</th>
                  <th>Yetenekler / Yapabildiği Hizmetler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in suppliers" :key="s.id">
                  <td>#{{ s.id }}</td>
                  <td><strong>{{ s.name }}</strong></td>
                  <td>
                    <span class="badge" :class="getCategoryBadgeClass(s.type)" style="font-size: 0.8rem; padding: 5px 10px;">
                      {{ getTypeName(s.type) }}
                    </span>
                  </td>
                  <td>
                    <span class="badge" :class="s.contract_type === 'Yetkili' ? 'badge-auth' : 'badge-contracted'">
                      {{ s.contract_type }} Servis
                    </span>
                  </td>
                  <td style="font-size: 0.85rem; font-weight: 500;">
                    {{ s.city }} / {{ s.district }}
                  </td>
                  <td style="font-family: monospace; font-size: 0.85rem;">
                    {{ s.phone }}
                  </td>
                  <td>
                    <div style="display: flex; gap: 4px; flex-wrap: wrap; max-width: 320px;">
                      <span class="service-tag" v-for="serv in s.services" :key="serv">
                        {{ serv }}
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- Add Quote Modal -->
  <div v-if="showAddQuoteModal" class="modal-overlay" @click.self="showAddQuoteModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 550px; padding: 30px;">
      <h2 style="margin-bottom: 20px; color: #7c3aed;">➕ Yeni Teklif Talebi Oluştur</h2>

      <form @submit.prevent="addQuote">
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Şirket Adı</label>
          <input type="text" v-model="newQuoteForm.company_name" required class="form-input" placeholder="Örn: Beta Lojistik Ltd.">
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">E-posta</label>
            <input type="email" v-model="newQuoteForm.email" required class="form-input" placeholder="info@betalojistik.com">
          </div>
          <div class="form-group">
            <label class="form-label">Telefon</label>
            <input type="text" v-model="newQuoteForm.phone" required class="form-input" placeholder="+90 216 444 0222">
          </div>
        </div>

        <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Araç Sayısı</label>
            <input type="number" min="1" v-model.number="newQuoteForm.vehicle_count" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Kiralama Süresi (Ay)</label>
            <select v-model.number="newQuoteForm.duration_months" required class="form-select">
              <option :value="12">12 Ay</option>
              <option :value="24">24 Ay</option>
              <option :value="36">36 Ay</option>
              <option :value="48">48 Ay</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Yıllık KM Sınırı</label>
            <select v-model.number="newQuoteForm.estimated_annual_mileage" required class="form-select">
              <option :value="10000">10,000 km</option>
              <option :value="20000">20,000 km</option>
              <option :value="30000">30,000 km</option>
              <option :value="40000">40,000 km</option>
            </select>
          </div>
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 25px;">
          <div class="form-group">
            <label class="form-label">Araç Segmenti</label>
            <select v-model="newQuoteForm.vehicle_segment" required class="form-select">
              <option value="A">A Segmenti (Mikro/Şehir)</option>
              <option value="B">B Segmenti (Küçük/Hatchback)</option>
              <option value="C">C Segmenti (Orta/Sedan)</option>
              <option value="D">D Segmenti (Üst/Prestij)</option>
              <option value="E">E Segmenti (Premium/Lüks)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Araç Tipi</label>
            <select v-model="newQuoteForm.vehicle_type" required class="form-select">
              <option value="Sedan">Sedan</option>
              <option value="SUV">SUV</option>
              <option value="Hatchback">Hatchback</option>
              <option value="Hafif Ticari">Hafif Ticari</option>
              <option value="Station Wagon">Station Wagon</option>
            </select>
          </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showAddQuoteModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: #7c3aed; color: #fff; border: none;">
            Teklifi Kaydet
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Edit Quote Modal -->
  <div v-if="showEditQuoteModal" class="modal-overlay" @click.self="showEditQuoteModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 550px; padding: 30px;">
      <h2 style="margin-bottom: 20px; color: #7c3aed;">📝 Teklif Talebi Düzenle</h2>

      <form @submit.prevent="submitEditQuote">
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Şirket Adı</label>
          <input type="text" v-model="editQuoteForm.company_name" required class="form-input">
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">E-posta</label>
            <input type="email" v-model="editQuoteForm.email" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Telefon</label>
            <input type="text" v-model="editQuoteForm.phone" required class="form-input">
          </div>
        </div>

        <div class="grid-3" style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Araç Sayısı</label>
            <input type="number" min="1" v-model.number="editQuoteForm.vehicle_count" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Kiralama Süresi (Ay)</label>
            <select v-model.number="editQuoteForm.duration_months" required class="form-select">
              <option :value="12">12 Ay</option>
              <option :value="24">24 Ay</option>
              <option :value="36">36 Ay</option>
              <option :value="48">48 Ay</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Yıllık KM Sınırı</label>
            <select v-model.number="editQuoteForm.estimated_annual_mileage" required class="form-select">
              <option :value="10000">10,000 km</option>
              <option :value="20000">20,000 km</option>
              <option :value="30000">30,000 km</option>
              <option :value="40000">40,000 km</option>
            </select>
          </div>
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Araç Segmenti</label>
            <select v-model="editQuoteForm.vehicle_segment" required class="form-select">
              <option value="A">A Segmenti</option>
              <option value="B">B Segmenti</option>
              <option value="C">C Segmenti</option>
              <option value="D">D Segmenti</option>
              <option value="E">E Segmenti</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Araç Tipi</label>
            <select v-model="editQuoteForm.vehicle_type" required class="form-select">
              <option value="Sedan">Sedan</option>
              <option value="SUV">SUV</option>
              <option value="Hatchback">Hatchback</option>
              <option value="Hafif Ticari">Hafif Ticari</option>
              <option value="Station Wagon">Station Wagon</option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Aylık Toplam Bedel (₺)</label>
          <input type="number" min="0" v-model.number="editQuoteForm.monthly_price_try" required class="form-input">
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showEditQuoteModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: #7c3aed; color: #fff; border: none;">
            Değişiklikleri Kaydet
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Edit Customer Modal -->
  <div v-if="showEditCustomerModal" class="modal-overlay" @click.self="showEditCustomerModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 550px; padding: 30px;">
      <h2 style="margin-bottom: 20px; color: #10b981;">🏢 Müşteri Bilgilerini Düzenle</h2>

      <form @submit.prevent="submitEditCustomer">
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Şirket Adı</label>
          <input type="text" v-model="editCustomerForm.company_name" required class="form-input">
        </div>

        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Ticari Unvan</label>
          <input type="text" v-model="editCustomerForm.legal_title" required class="form-input">
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">E-posta</label>
            <input type="email" v-model="editCustomerForm.email" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Telefon</label>
            <input type="text" v-model="editCustomerForm.phone" required class="form-input">
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Adres</label>
          <input type="text" v-model="editCustomerForm.address" required class="form-input">
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 25px;">
          <div class="form-group">
            <label class="form-label">Kayıtlı Araç Sayısı</label>
            <input type="number" min="0" v-model.number="editCustomerForm.registered_vehicles_count" required class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">Aylık Sözleşme Bedeli (₺)</label>
            <input type="number" min="0" v-model.number="editCustomerForm.contract_amount" required class="form-input">
          </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="showEditCustomerModal = false" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: #10b981; color: #fff; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
            Değişiklikleri Kaydet
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Contract Amount Prompt Modal -->
  <div v-if="showAmountModal" class="modal-overlay" @click.self="cancelContractSigning">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 450px; padding: 30px;">
      <h2 style="margin-bottom: 10px; color: #10b981; display: flex; align-items: center; gap: 10px;">
        <span>📝</span> Sözleşme İmzalama İşlemi
      </h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px;">
        Teklif onaylandı ve sözleşme imzalanma aşamasına geçildi. Lütfen sözleşmenin kesinleşen **Aylık Toplam İmza Tutarını (₺)** giriniz:
      </p>

      <form @submit.prevent="confirmContractSigning">
        <div class="form-group" style="margin-bottom: 25px;">
          <label class="form-label">Sözleşme Aylık Bedeli (₺)</label>
          <input type="number" min="0" v-model.number="contractAmountInput" required class="form-input" placeholder="Örn: 425000">
        </div>

        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="cancelContractSigning" class="btn btn-secondary">Vazgeç</button>
          <button type="submit" class="btn btn-primary" style="background: #10b981; color: #fff; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);">
            Sözleşmeyi İmzala & Müşteriyi Aktifleştir
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Supplier Bids List Modal (Admin view) -->
  <div v-if="showBidsModal" class="modal-overlay" @click.self="showBidsModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 800px; padding: 30px;">
      <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
        <h2 style="color: #7c3aed;">🏢 Tedarikçi Teklifleri (Bids)</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 5px;">
          <strong>{{ selectedQuoteForBids?.company_name }}</strong> firmasının {{ selectedQuoteForBids?.vehicle_count }} adet {{ selectedQuoteForBids?.vehicle_segment }} Segment {{ selectedQuoteForBids?.vehicle_type }} kiralama talebi için tedarikçilerden gelen teklifler.
        </p>
      </div>

      <div v-if="bidsLoading" class="text-center" style="padding: 30px 0;">Yükleniyor...</div>
      <div v-else-if="selectedQuoteBids.length === 0" class="empty-state" style="padding: 30px 0;">
        <p>Bu talep için henüz kiralama tedarikçilerinden teklif gelmedi.</p>
      </div>
      <div v-else class="custom-table-container">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Tedarikçi Adı</th>
              <th>Aylık Teklif Bedeli (₺)</th>
              <th>Teklif Notları</th>
              <th>Tarih</th>
              <th>Durum</th>
              <th style="width: 150px;">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bid in selectedQuoteBids" :key="bid.id">
              <td><strong>{{ bid.supplier_name }}</strong></td>
              <td><strong style="color: #10b981;">₺{{ bid.monthly_price_try?.toLocaleString() }}</strong></td>
              <td style="font-size: 0.8rem; max-width: 250px; white-space: normal;">{{ bid.notes }}</td>
              <td style="font-size: 0.8rem;">{{ formatDate(bid.created_at) }}</td>
              <td>
                <span class="badge" :class="getBidBadgeClass(bid.status)" style="font-size: 0.75rem; padding: 4px 8px;">
                  {{ bid.status }}
                </span>
              </td>
              <td>
                <div v-if="bid.status === 'Beklemede'" style="display: flex; gap: 6px;">
                  <button @click="acceptSupplierBid(bid.id)" class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; background: rgba(16, 185, 129, 0.1); color: #10b981; border-color: rgba(16, 185, 129, 0.2);">
                    ✓ Kabul Et
                  </button>
                  <button @click="rejectSupplierBid(bid.id)" class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: rgba(239, 68, 68, 0.2);">
                    ✕ Reddet
                  </button>
                </div>
                <span v-else style="color: var(--text-muted); font-size: 0.8rem;">İşlem Tamam</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="display: flex; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px; margin-top: 20px;">
        <button @click="showBidsModal = false" class="btn btn-secondary">Kapat</button>
      </div>
    </div>
  </div>

  <!-- Add Supplier Modal -->
  <div v-if="showAddSupplierModal" class="modal-overlay" @click.self="closeAddSupplierModal">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 620px; padding: 30px;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px;">
        <h2 style="color: #7c3aed; margin: 0; display: flex; align-items: center; gap: 10px;">
          🏢 Yeni Tedarikçi Ekle
        </h2>
        <button @click="closeAddSupplierModal" style="background: transparent; border: none; color: var(--text-muted); font-size: 1.4rem; cursor: pointer; line-height: 1;">✕</button>
      </div>

      <form @submit.prevent="submitAddSupplier">
        <!-- Tedarikçi Adı -->
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Tedarikçi Adı *</label>
          <input type="text" v-model="newSupplierForm.name" required class="form-input" placeholder="Örn: OtoPratik Bağcılar">
        </div>

        <!-- Kategori & Servis Tipi -->
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">Kategori *</label>
            <select v-model="newSupplierForm.type" required class="form-select">
              <option value="">Seçiniz...</option>
              <option value="servis">🔧 Yetkili / Anlaşmalı Servis</option>
              <option value="lastik">🛞 Lastik Bayi</option>
              <option value="yol_yardim">🚨 Yol Yardım</option>
              <option value="ikame_arac">🚗 İkame Araç</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Sözleşme Tipi *</label>
            <select v-model="newSupplierForm.contract_type" required class="form-select">
              <option value="">Seçiniz...</option>
              <option value="Yetkili">🛡️ Yetkili Servis</option>
              <option value="Anlaşmalı">🤝 Anlaşmalı Servis</option>
            </select>
          </div>
        </div>

        <!-- İl & İlçe -->
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px;">
          <div class="form-group">
            <label class="form-label">İl *</label>
            <input type="text" v-model="newSupplierForm.city" required class="form-input" placeholder="Örn: İstanbul">
          </div>
          <div class="form-group">
            <label class="form-label">İlçe *</label>
            <input type="text" v-model="newSupplierForm.district" required class="form-input" placeholder="Örn: Bağcılar">
          </div>
        </div>

        <!-- Telefon -->
        <div class="form-group" style="margin-bottom: 15px;">
          <label class="form-label">Telefon *</label>
          <input type="text" v-model="newSupplierForm.phone" required class="form-input" placeholder="+90 212 555 0000">
        </div>

        <!-- Hizmetler (tag input) -->
        <div class="form-group" style="margin-bottom: 22px;">
          <label class="form-label">Sunduğu Hizmetler</label>
          <div class="supplier-tag-input-wrap">
            <div class="supplier-tags">
              <span v-for="(svc, i) in newSupplierForm.services" :key="i" class="supplier-tag-chip">
                {{ svc }}
                <button type="button" @click="removeService(i)" class="chip-remove">✕</button>
              </span>
              <input
                v-model="serviceInput"
                @keydown.enter.prevent="addService"
                @keydown.comma.prevent="addService"
                class="tag-bare-input"
                placeholder="Hizmet yazıp Enter'a basın..."
              >
            </div>
          </div>
          <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 6px;">
            Örn: Periyodik Bakım · Fren Sistemi · Akü Değişimi
          </p>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end; border-top: 1px solid var(--border-color); padding-top: 15px;">
          <button type="button" @click="closeAddSupplierModal" class="btn btn-secondary">İptal</button>
          <button type="submit" class="btn btn-primary" style="background: linear-gradient(135deg, #7c3aed, #3b82f6); border: none; box-shadow: 0 4px 15px rgba(124,58,237,0.2);">
            ✅ Tedarikçiyi Kaydet
          </button>
        </div>
      </form>
    </div>
  </div>

</template>


<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const activeTab = ref('quotes') // 'quotes', 'customers', 'suppliers'
const quotes = ref([])
const customers = ref([])
const suppliers = ref([])
const loading = ref(true)

// Add Quote Modal State
const showAddQuoteModal = ref(false)
const newQuoteForm = reactive({
  company_name: '',
  email: '',
  phone: '',
  vehicle_count: 5,
  duration_months: 24,
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  estimated_annual_mileage: 20000
})

// Edit Quote Modal State
const showEditQuoteModal = ref(false)
const selectedQuoteId = ref(null)
const editQuoteForm = reactive({
  company_name: '',
  email: '',
  phone: '',
  vehicle_count: 1,
  duration_months: 24,
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  estimated_annual_mileage: 20000,
  monthly_price_try: 0,
  status: ''
})

// Edit Customer Modal State
const showEditCustomerModal = ref(false)
const selectedCustomerId = ref(null)
const editCustomerForm = reactive({
  company_name: '',
  legal_title: '',
  email: '',
  phone: '',
  address: '',
  registered_vehicles_count: 0,
  contract_amount: 0
})

// Customer Detail View State
const showCustomerDetailsModal = ref(false)
const selectedCustomerDetails = ref(null)
const customerVehicles = ref([])
const customerServices = ref([])

// Contract signing amount modal state
const showAmountModal = ref(false)
const pendingQuoteId = ref(null)
const contractAmountInput = ref(0)

// Add Supplier Modal State
const showAddSupplierModal = ref(false)
const serviceInput = ref('')
const newSupplierForm = reactive({
  name: '',
  type: '',
  phone: '',
  city: '',
  district: '',
  services: [],
  contract_type: ''
})

const addService = () => {
  const val = serviceInput.value.trim().replace(/,$/, '')
  if (val && !newSupplierForm.services.includes(val)) {
    newSupplierForm.services.push(val)
  }
  serviceInput.value = ''
}

const removeService = (index) => {
  newSupplierForm.services.splice(index, 1)
}

const closeAddSupplierModal = () => {
  showAddSupplierModal.value = false
  Object.assign(newSupplierForm, { name: '', type: '', phone: '', city: '', district: '', services: [], contract_type: '' })
  serviceInput.value = ''
}

const submitAddSupplier = async () => {
  // Commit any pending service input
  if (serviceInput.value.trim()) addService()
  try {
    const res = await fetch('/api/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSupplierForm)
    })
    if (res.ok) {
      await fetchSuppliers()
      closeAddSupplierModal()
    } else {
      alert('Tedarikçi eklenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error adding supplier:', err)
    alert('Bağlantı hatası oluştu.')
  }
}

// Bids modal state

const showBidsModal = ref(false)
const bidsLoading = ref(false)
const selectedQuoteForBids = ref(null)
const selectedQuoteBids = ref([])

// QUOTES COMPUTED
const totalProposedVehicles = computed(() => {
  return quotes.value.reduce((acc, q) => acc + q.vehicle_count, 0)
})

const totalProposedRevenue = computed(() => {
  return quotes.value.reduce((acc, q) => acc + q.monthly_price_try, 0)
})

// CUSTOMERS COMPUTED
const totalCustomerVehicles = computed(() => {
  return customers.value.reduce((acc, c) => acc + c.registered_vehicles_count, 0)
})

const totalCustomerRevenue = computed(() => {
  return customers.value.reduce((acc, c) => acc + c.contract_amount, 0)
})

// SUPPLIERS COMPUTED
const authorizedSuppliersCount = computed(() => {
  return suppliers.value.filter(s => s.contract_type === 'Yetkili').length
})

// Detail Tab state for customer modal
const detailTab = ref('vehicles')

const contractedSuppliersCount = computed(() => {
  return suppliers.value.filter(s => s.contract_type === 'Anlaşmalı').length
})

const fetchQuotes = async () => {
  try {
    const response = await fetch('/api/quotes')
    if (response.ok) {
      quotes.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching quotes:', error)
  }
}

const fetchCustomers = async () => {
  try {
    const response = await fetch('/api/admin/customers')
    if (response.ok) {
      customers.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching customers:', error)
  }
}

const fetchSuppliers = async () => {
  try {
    const response = await fetch('/api/suppliers')
    if (response.ok) {
      suppliers.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching suppliers:', error)
  }
}

const addQuote = async () => {
  try {
    const res = await fetch('/api/quotes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newQuoteForm)
    })
    if (res.ok) {
      await fetchQuotes()
      showAddQuoteModal.value = false
      // Reset form
      newQuoteForm.company_name = ''
      newQuoteForm.email = ''
      newQuoteForm.phone = ''
      newQuoteForm.vehicle_count = 5
      newQuoteForm.duration_months = 24
      newQuoteForm.vehicle_segment = 'C'
      newQuoteForm.vehicle_type = 'Sedan'
      newQuoteForm.estimated_annual_mileage = 20000
    } else {
      alert('Teklif eklenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error adding quote:', err)
  }
}

const openEditQuoteModal = (quote) => {
  selectedQuoteId.value = quote.id
  editQuoteForm.company_name = quote.company_name
  editQuoteForm.email = quote.email
  editQuoteForm.phone = quote.phone
  editQuoteForm.vehicle_count = quote.vehicle_count
  editQuoteForm.duration_months = quote.duration_months
  editQuoteForm.vehicle_segment = quote.vehicle_segment
  editQuoteForm.vehicle_type = quote.vehicle_type
  editQuoteForm.estimated_annual_mileage = quote.estimated_annual_mileage
  editQuoteForm.monthly_price_try = quote.monthly_price_try
  editQuoteForm.status = quote.status
  showEditQuoteModal.value = true
}

const submitEditQuote = async () => {
  try {
    const res = await fetch(`/api/quotes/${selectedQuoteId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editQuoteForm)
    })
    if (res.ok) {
      await fetchQuotes()
      showEditQuoteModal.value = false
    } else {
      alert('Teklif güncellenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error updating quote:', err)
  }
}

const openEditCustomerModal = (customer) => {
  selectedCustomerId.value = customer.id
  editCustomerForm.company_name = customer.company_name
  editCustomerForm.legal_title = customer.legal_title
  editCustomerForm.email = customer.email
  editCustomerForm.phone = customer.phone
  editCustomerForm.address = customer.address
  editCustomerForm.registered_vehicles_count = customer.registered_vehicles_count
  editCustomerForm.contract_amount = customer.contract_amount
  showEditCustomerModal.value = true
}

const submitEditCustomer = async () => {
  try {
    const res = await fetch(`/api/admin/customers/${selectedCustomerId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editCustomerForm)
    })
    if (res.ok) {
      await fetchCustomers()
      showEditCustomerModal.value = false
    } else {
      alert('Müşteri bilgileri güncellenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error updating customer:', err)
  }
}


// Fetch vehicles for a customer
const fetchCustomerVehicles = async (customerId) => {
  try {
    const res = await fetch(`/api/admin/customers/${customerId}/vehicles`)
    if (res.ok) {
      customerVehicles.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching customer vehicles:', error)
  }
}

// Fetch services for a customer
const fetchCustomerServices = async (customerId) => {
  try {
    const res = await fetch(`/api/admin/customers/${customerId}/services`)
    if (res.ok) {
      customerServices.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching customer services:', error)
  }
}

// Open customer detail modal
const openCustomerDetails = async (customer) => {
  selectedCustomerDetails.value = customer
  detailTab.value = 'vehicles'
  customerVehicles.value = []
  customerServices.value = []
  // Ensure customers tab is active
  activeTab.value = 'customers'
  showCustomerDetailsModal.value = true
  // Fetch data in background
  await fetchCustomerVehicles(customer.id)
  await fetchCustomerServices(customer.id)
}

// Close customer detail modal
const closeCustomerDetails = () => {
  showCustomerDetailsModal.value = false
  selectedCustomerDetails.value = null
  customerVehicles.value = []
  customerServices.value = []
}


const onStatusChange = (quoteId, newStatus) => {
  if (newStatus === 'Sözleşme İmzalandı') {
    const quote = quotes.value.find(q => q.id === quoteId)
    contractAmountInput.value = quote ? quote.monthly_price_try : 0
    pendingQuoteId.value = quoteId
    showAmountModal.value = true
  } else {
    updateStatus(quoteId, newStatus, null)
  }
}

const confirmContractSigning = async () => {
  await updateStatus(pendingQuoteId.value, 'Sözleşme İmzalandı', contractAmountInput.value)
  showAmountModal.value = false
  pendingQuoteId.value = null
}

const cancelContractSigning = async () => {
  showAmountModal.value = false
  pendingQuoteId.value = null
  await fetchQuotes() // Revert local state select
}

const openQuoteBidsModal = async (quote) => {
  selectedQuoteForBids.value = quote
  showBidsModal.value = true
  bidsLoading.value = true
  try {
    const res = await fetch(`/api/quotes/${quote.id}/bids`)
    if (res.ok) {
      selectedQuoteBids.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching bids:', error)
  } finally {
    bidsLoading.value = false
  }
}

const acceptSupplierBid = async (bidId) => {
  try {
    const res = await fetch(`/api/bids/${bidId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status: 'Kabul Edildi' })
    })
    if (res.ok) {
      await openQuoteBidsModal(selectedQuoteForBids.value)
      await fetchQuotes()
    } else {
      alert('Teklif kabul edilirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error accepting bid:', err)
  }
}

const rejectSupplierBid = async (bidId) => {
  try {
    const res = await fetch(`/api/bids/${bidId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status: 'Reddedildi' })
    })
    if (res.ok) {
      await openQuoteBidsModal(selectedQuoteForBids.value)
    } else {
      alert('Teklif reddedilirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error rejecting bid:', err)
  }
}

const getBidBadgeClass = (status) => {
  return {
    'badge-active': status === 'Kabul Edildi',
    'badge-roadside': status === 'Beklemede',
    'badge-old-reason': status === 'Reddedildi'
  }
}

const updateStatus = async (quoteId, newStatus, contractAmount) => {
  try {
    const response = await fetch(`/api/quotes/${quoteId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        status: newStatus, 
        contract_amount: contractAmount 
      })
    })
    
    if (response.ok) {
      console.log(`Quote #${quoteId} status set to ${newStatus}`)
      await fetchQuotes()
      await fetchCustomers()
    } else {
      alert('Durum güncellenirken hata oluştu.')
    }
  } catch (error) {
    console.error('Error updating status:', error)
  }
}

const getStatusClass = (status) => {
  return {
    'status-given': status === 'Teklif Verildi',
    'status-reviewing': status === 'Değerlendirmede',
    'status-signed': status === 'Sözleşme İmzalandı',
    'status-rejected': status === 'Reddedildi'
  }
}

const getCategoryBadgeClass = (type) => {
  return {
    'badge-active': type === 'servis',
    'badge-service': type === 'lastik',
    'badge-roadside': type === 'yol_yardim',
    'badge-replacement': type === 'ikame_arac'
  }
}

const getTypeName = (type) => {
  const map = {
    'servis': 'Yetkili Servis',
    'lastik': 'Lastik Bayi',
    'yol_yardim': 'Yol Yardım',
    'ikame_arac': 'İkame Araç'
  }
  return map[type] || type
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

const logout = () => {
  localStorage.removeItem('fleetcar_admin_token')
  localStorage.removeItem('fleetcar_admin_user')
  router.push('/admin-login')
}

onMounted(async () => {
  // Simple check for admin authentication
  if (!localStorage.getItem('fleetcar_admin_token')) {
    router.push('/admin-login')
    return
  }
  
  loading.value = true
  await Promise.all([
    fetchQuotes(),
    fetchCustomers(),
    fetchSuppliers()
  ])
  loading.value = false
})
</script>

<style scoped>
.admin-sidebar {
  background: #0f172a !important; /* Elegant dark slate sidebar specifically for admin to look distinct */
  color: #f8fafc !important;
}

.admin-sidebar .sidebar-link {
  color: #94a3b8;
}

.admin-sidebar .sidebar-link:hover {
  background: rgba(124, 58, 237, 0.1);
  color: #c084fc;
}

.active-admin {
  background: #7c3aed !important;
  color: #ffffff !important;
}

.admin-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 25px;
}

.admin-profile .avatar {
  background: rgba(124, 58, 237, 0.2);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.admin-stat {
  border-left: 4px solid #7c3aed !important;
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

.service-tag {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  display: inline-block;
  margin: 2px;
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

/* ───────── CUSTOMER DETAIL DASHBOARD ───────── */
.customer-detail-dashboard {
  padding: 0 0 40px;
}

.cd-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 0 2px;
}

.cd-back-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 8px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.cd-back-btn:hover {
  background: rgba(255,255,255,0.06);
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.2);
}

/* Hero card */
.cd-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 28px 32px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  border: 1px solid rgba(16, 185, 129, 0.2);
  background: linear-gradient(135deg, rgba(16,185,129,0.05) 0%, rgba(124,58,237,0.05) 100%);
}

.cd-hero-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(16,185,129,0.3);
}

.cd-hero-info {
  flex: 1;
  min-width: 200px;
}

.cd-company-name {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.cd-legal-title {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0 0 12px;
}

.cd-contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 0.83rem;
  color: var(--text-dark);
}

.cd-hero-badges {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.cd-hero-badge {
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
  padding: 14px 20px;
  text-align: center;
  min-width: 110px;
  border: 1px solid rgba(255,255,255,0.08);
}
.cd-badge-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}
.cd-badge-value {
  font-size: 1.1rem;
  font-weight: 800;
}
.cd-badge-green .cd-badge-value  { color: #10b981; }
.cd-badge-purple .cd-badge-value { color: #7c3aed; }
.cd-badge-blue .cd-badge-value   { color: #3b82f6; }
.cd-badge-amber .cd-badge-value  { color: #f59e0b; }

/* Tabs */
.cd-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0;
}
.cd-tab {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 10px 22px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
}
.cd-tab:hover { color: var(--text-primary); }
.cd-tab-active {
  color: #10b981 !important;
  border-bottom-color: #10b981;
}

.cd-tab-content {
  animation: fadeSlide 0.25s ease;
}
@keyframes fadeSlide {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Vehicle grid */
.cd-vehicle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}

.cd-vehicle-card {
  padding: 20px;
  border-radius: 14px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.cd-vehicle-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.cd-vehicle-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.cd-plate {
  background: #0f172a;
  border: 2px solid #334155;
  color: #f8fafc;
  font-family: monospace;
  font-size: 1rem;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 6px;
  letter-spacing: 0.06em;
}

.cd-vehicle-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 14px;
}

.cd-vehicle-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cd-vehicle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.cd-vd-label { color: var(--text-muted); }
.cd-vd-val   { color: var(--text-primary); font-weight: 500; }

/* Hover highlight for customer rows */
.customer-row:hover td {
  background: rgba(16,185,129,0.05);
}

/* Supplier tag input */
.supplier-tag-input-wrap {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--glass-bg, rgba(255,255,255,0.04));
  padding: 8px 10px;
  transition: border-color 0.2s;
}
.supplier-tag-input-wrap:focus-within {
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.12);
}
.supplier-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.supplier-tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(124,58,237,0.15);
  color: #c084fc;
  border: 1px solid rgba(124,58,237,0.25);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 0.8rem;
  font-weight: 500;
}
.chip-remove {
  background: transparent;
  border: none;
  color: #c084fc;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.chip-remove:hover { opacity: 1; }
.tag-bare-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.88rem;
  min-width: 180px;
  flex: 1;
}
.tag-bare-input::placeholder { color: var(--text-muted); }
</style>

