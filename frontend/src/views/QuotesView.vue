<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Header -->
      <header class="dashboard-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
          <h1>Kiralama Teklifleri</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Şirketiniz adına yapılan teklif taleplerini inceleyin, gelen tedarikçi tekliflerini onaylayın.</p>
        </div>
        <button @click="openNewQuoteModal" class="btn btn-primary" style="background: linear-gradient(135deg, #4f46e5, #7c3aed); border: none; font-weight: 700; display: flex; align-items: center; gap: 8px; padding: 10px 18px; box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25);">
          <span>➕</span>
          <span>Yeni Teklif İsteyin</span>
        </button>
      </header>

      <!-- ⚠️ Missing Documents Warning Banner -->
      <div v-if="!documentsUploaded" class="glass-panel" style="background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); border: 2px solid #ea580c; border-radius: 16px; padding: 22px; margin-top: 25px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; box-shadow: 0 10px 25px -5px rgba(234, 88, 12, 0.15);">
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="width: 48px; height: 48px; border-radius: 12px; background: #ea580c; color: #ffffff; font-size: 1.6rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            ⚠️
          </div>
          <div>
            <h3 style="font-size: 1.05rem; font-weight: 800; color: #9a3412; margin-bottom: 4px;">
              Şirket Evraklarınız Eksik! Kiralama Teklifi Alamazsınız
            </h3>
            <p style="color: #c2410c; font-size: 0.9rem; margin: 0; line-height: 1.4;">
              Filo kiralama teklif talebinde bulunabilmek için öncelikle Vergi Levhası, İmza Sirküsü ve Faaliyet Belgenizi yüklemeniz gerekmektedir.
            </p>
          </div>
        </div>
        <router-link to="/dashboard/settings?tab=sirket_evraklari" class="btn" style="background: #ea580c; color: #ffffff; font-weight: 800; padding: 12px 22px; border-radius: 10px; text-decoration: none; white-space: nowrap; font-size: 0.92rem; flex-shrink: 0; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.25);">
          📂 Evrakları Tamamla ➔
        </router-link>
      </div>

      <!-- Zero-Vehicle Highlight Banner -->
      <div v-else-if="documentsUploaded && hasNoVehicles" class="glass-panel" style="background: linear-gradient(135deg, rgba(79, 70, 229, 0.12) 0%, rgba(124, 58, 237, 0.12) 100%); border: 1px solid rgba(124, 58, 237, 0.25); border-radius: 16px; padding: 22px; margin-top: 25px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.1rem; color: #a78bfa; margin-bottom: 6px;">
            <span>🚗</span>
            <span>Henüz Şirketinize Kayıtlı Araç Bulunmuyor!</span>
          </div>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0;">
            Şirket evraklarınız yüklenmiştir. İhtiyacınıza uygun ticari veya binek araç filoları için hemen teklif isteyin.
          </p>
        </div>
        <button @click="openNewQuoteModal" class="btn btn-primary" style="background: #4f46e5; border: none; font-weight: 700; padding: 10px 20px; font-size: 0.9rem; white-space: nowrap;">
          ✨ Hemen Teklif Al
        </button>
      </div>

      <!-- Status Filter Bar -->
      <div v-if="!loading && myQuotesList.length > 0" class="filter-bar-container">
        <div class="filter-pills-group">
          <span class="filter-header-label">
            <span>📊</span> FİLTRELE:
          </span>
          <button 
            v-for="opt in statusFilterOptions" 
            :key="opt.value"
            @click="selectedStatusFilter = opt.value"
            :class="['btn-filter-pill', { active: selectedStatusFilter === opt.value }]"
          >
            <span class="pill-icon">{{ opt.icon }}</span>
            <span class="pill-text">{{ opt.label }}</span>
            <span class="count-badge">
              {{ getFilterCount(opt.value) }}
            </span>
          </button>
        </div>
        <div class="filter-counter-text">
          Gösterilen: <strong class="counter-highlight">{{ filteredQuotes.length }}</strong> / {{ myQuotesList.length }} teklif
        </div>
      </div>

      <!-- Quotes List -->
      <div v-if="loading" class="text-center" style="padding: 60px 0; font-size: 1.1rem; color: var(--text-muted);">
        Yükleniyor...
      </div>

      <div v-else-if="filteredQuotes.length === 0" class="empty-state glass-panel" style="margin-top: 20px; padding: 40px; text-align: center;">
        <span style="font-size: 3rem; display: block; margin-bottom: 15px;">📑</span>
        <h3>{{ selectedStatusFilter === 'Tümü' ? 'Aktif Teklif Talebi Bulunmuyor' : `"${selectedStatusFilter}" Durumunda Teklif Bulunmuyor` }}</h3>
        <p style="color: var(--text-muted); margin-top: 5px; margin-bottom: 20px;">
          {{ selectedStatusFilter === 'Tümü' ? 'Hemen şirketiniz için çoklu veya detaylı şartname içeren kiralama teklif talebi oluşturabilirsiniz.' : 'Filtre seçiminizi değiştirerek diğer teklif taleplerinizi görüntüleyebilirsiniz.' }}
        </p>
        <button v-if="selectedStatusFilter !== 'Tümü'" @click="selectedStatusFilter = 'Tümü'" class="btn" style="background: rgba(255,255,255,0.1); color: #fff; margin-right: 12px; font-weight: 600; padding: 10px 20px; border-radius: 8px;">
          🔄 Tüm Teklifleri Göster
        </button>
        <button @click="openNewQuoteModal" class="btn btn-primary" style="background: linear-gradient(135deg, #4f46e5, #7c3aed); border: none; font-weight: 700; padding: 10px 24px;">
          🚀 Hemen Teklif Alın
        </button>
      </div>

      <div v-else style="margin-top: 20px; display: flex; flex-direction: column; gap: 25px;">
        <div v-for="quote in filteredQuotes" :key="quote.id" class="glass-panel quote-card" 
             :style="{ opacity: quote.status === 'İstek Silindi' ? 0.6 : 1 }"
             style="padding: 25px; border-left: 5px solid #7c3aed;">
          
          <!-- Card Header Info -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 20px;">
            <div>
              <span style="font-size: 0.8rem; text-transform: uppercase; font-weight: 700; color: #a78bfa; letter-spacing: 0.05em;">TALEP ID: #{{ quote.id }}</span>
              <h2 style="font-size: 1.25rem; font-weight: 700; margin-top: 2px;">
                {{ quote.vehicle_count }} Adet Araç 
                <span v-if="quote.items && quote.items.length > 1" style="font-size: 0.85rem; background: rgba(124, 58, 237, 0.15); color: #a78bfa; padding: 2px 10px; border-radius: 12px; margin-left: 8px; border: 1px solid rgba(124, 58, 237, 0.3);">
                  {{ quote.items.length }} Farklı Araç Grubu
                </span>
                <span v-if="quote.details && Object.keys(quote.details).length > 0" style="font-size: 0.8rem; background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 2px 10px; border-radius: 12px; margin-left: 6px; border: 1px solid rgba(16, 185, 129, 0.3);">
                  ✨ Detaylı Şartnameli
                </span>
              </h2>
              <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 3px;">Talep Tarihi: {{ quote.created_at }}</p>
            </div>
            
            <div style="display: flex; align-items: center; gap: 12px;">
              <span class="badge" :class="getStatusBadgeClass(quote.status)" style="font-size: 0.85rem; padding: 6px 12px;">
                {{ quote.status }}
              </span>

              <!-- Delete Request Button -->
              <button v-if="quote.status !== 'İstek Silindi'" @click="deleteQuoteRequest(quote.id)" 
                      style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); color: #ef4444; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <span>🗑️</span> İsteği Sil
              </button>
            </div>
          </div>

          <!-- Multi-item Vehicle Groups Breakdown List -->
          <div v-if="quote.items && quote.items.length > 0" style="margin-bottom: 20px;">
            <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 10px; font-weight: 700;">
              Talep Edilen Araç Grupları Detayı ({{ quote.items.length }} Paket)
            </h4>
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div v-for="(item, idx) in quote.items" :key="idx" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px 18px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                  <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="background: rgba(124, 58, 237, 0.2); color: #a78bfa; font-weight: 700; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                      {{ idx + 1 }}
                    </span>
                    <div>
                      <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">
                        {{ item.vehicle_count }} Adet {{ item.vehicle_segment }} Segment {{ item.vehicle_type }}
                      </div>
                      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
                        Süre: <strong>{{ item.duration_months }} Ay</strong> | Yıllık KM Limit: <strong>{{ item.estimated_annual_mileage?.toLocaleString() }} km</strong>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Per-group Detailed Specifications Badge Box -->
                <div v-if="item.details && hasDetails(item.details)" style="margin-top: 4px; padding-top: 8px; border-top: 1px dashed rgba(255, 255, 255, 0.1); font-size: 0.82rem; color: #cbd5e1; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; background: rgba(124, 58, 237, 0.08); padding: 8px 12px; border-radius: 8px;">
                  <span style="font-weight: 800; color: #c084fc;">📋 Gruba Özel Şartlar:</span>
                  <span v-if="getAllBrandsForItem(item).length > 0">Marka: <strong style="color: #fff;">{{ getAllBrandsForItem(item).join(', ') }}</strong></span>
                  <span v-if="getAllModelsForItem(item).length > 0">Model: <strong style="color: #fff;">{{ getAllModelsForItem(item).join(', ') }}</strong></span>
                  <span v-if="item.details.periodic_maintenance">Bakım: <strong style="color: #fff;">{{ item.details.periodic_maintenance }}</strong></span>
                  <span v-if="item.details.imm_limit">İMM: <strong style="color: #10b981;">{{ item.details.imm_limit }}</strong></span>
                  <span v-if="item.details.payment_term">Vade: <strong style="color: #fff;">{{ item.details.payment_term }}</strong></span>
                  <span v-if="item.details.custom_terms">Not: <strong style="color: #fff;">{{ item.details.custom_terms }}</strong></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Detailed Specifications Box (If Customer Filled Detailed Form) -->
          <div v-if="quote.details && Object.keys(quote.details).length > 0" style="margin-bottom: 20px; background: rgba(124, 58, 237, 0.05); border: 1px solid rgba(124, 58, 237, 0.2); border-radius: 12px; padding: 16px;">
            <h4 style="font-size: 0.85rem; text-transform: uppercase; color: #a78bfa; font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
              <span>📋</span> Detaylı Şartname ve Özellikler
            </h4>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; font-size: 0.83rem;">
              <div v-if="quote.details.start_date || quote.details.end_date">
                <span style="color: var(--text-muted);">İstenen Tarih Aralığı:</span>
                <div style="font-weight: 700; color: #fff;">{{ quote.details.start_date || 'Açık' }} - {{ quote.details.end_date || 'Açık' }}</div>
              </div>

              <div v-if="quote.details.selected_brands && quote.details.selected_brands.length > 0">
                <span style="color: var(--text-muted);">Tercih Edilen Markalar:</span>
                <div style="font-weight: 700; color: #fff;">{{ quote.details.selected_brands.join(', ') }} {{ quote.details.custom_brand ? '(' + quote.details.custom_brand + ')' : '' }}</div>
              </div>

              <div v-if="quote.details.selected_models && quote.details.selected_models.length > 0">
                <span style="color: var(--text-muted);">Tercih Edilen Modeller:</span>
                <div style="font-weight: 700; color: #fff;">{{ quote.details.selected_models.join(', ') }} {{ quote.details.custom_model ? '(' + quote.details.custom_model + ')' : '' }}</div>
              </div>

              <div v-if="quote.details.selected_fuel_types && quote.details.selected_fuel_types.length > 0">
                <span style="color: var(--text-muted);">Yakıt / Şanzıman:</span>
                <div style="font-weight: 700; color: #fff;">{{ quote.details.selected_fuel_types.join(', ') }} | {{ (quote.details.selected_transmissions || []).join(', ') }}</div>
              </div>

              <div v-if="quote.details.imm_limit">
                <span style="color: var(--text-muted);">İMM Limiti:</span>
                <div style="font-weight: 700; color: #10b981;">{{ quote.details.imm_limit }}</div>
              </div>

              <div v-if="quote.details.periodic_maintenance">
                <span style="color: var(--text-muted);">Periyodik Bakım:</span>
                <div style="font-weight: 700; color: #fff;">{{ quote.details.periodic_maintenance }}</div>
              </div>
            </div>

            <!-- Custom text note -->
            <div v-if="quote.details.custom_terms" style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(255, 255, 255, 0.1); font-size: 0.82rem;">
              <span style="color: var(--text-muted);">Özel İstenen Şartlar: </span>
              <span style="color: #fff; font-weight: 600;">{{ quote.details.custom_terms }}</span>
            </div>
          </div>

          <!-- Incoming Supplier Bids Section -->
          <div style="margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <h3 style="font-size: 1.05rem; font-weight: 700; color: #a78bfa; display: flex; align-items: center; gap: 8px; margin: 0;">
                <span>📥</span> Gelen Tedarikçi Teklifleri 
                <span style="font-size: 0.8rem; background: rgba(124, 58, 237, 0.2); color: #a78bfa; padding: 2px 8px; border-radius: 12px; font-weight: 600;">
                  {{ quote.bids ? quote.bids.length : 0 }} Teklif Alındı
                </span>
              </h3>
            </div>

            <!-- Deleted Request Banner -->
            <div v-if="quote.status === 'İstek Silindi'" style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); padding: 12px; border-radius: 10px; color: #ef4444; font-weight: 600; font-size: 0.88rem;">
              ⚠️ Bu kiralama talebi silinmiştir / iptal edilmiştir.
            </div>

            <!-- Empty Bids State -->
            <div v-else-if="!quote.bids || quote.bids.length === 0" style="background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--border-color); border-radius: 10px; padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.9rem;">
              <span>⏳</span> Henüz tedarikçilerden fiyat teklifi gelmedi. Tedarikçiler teklif sunduğunda burada listelenecektir.
            </div>

            <!-- Supplier Bids List -->
            <div v-else style="display: flex; flex-direction: column; gap: 12px;">
              <div v-for="bid in quote.bids" :key="bid.id" 
                   style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                
                <!-- Supplier Info -->
                <div style="display: flex; align-items: center; gap: 14px;">
                  <div style="width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, rgba(79, 70, 229, 0.2), rgba(124, 58, 237, 0.2)); border: 1px solid #7c3aed; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                    🏢
                  </div>
                  <div>
                    <div style="font-weight: 700; font-size: 1rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                      <span>{{ bid.supplier_name }}</span>
                      <span v-if="bid.status === 'Onaylandı'" style="font-size: 0.75rem; background: #10b981; color: #fff; padding: 2px 8px; border-radius: 10px; font-weight: 700;">
                        ✓ Kabul Edildi
                      </span>
                      <span v-else-if="bid.status === 'Reddedildi'" style="font-size: 0.75rem; background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 8px; border-radius: 10px; font-weight: 600;">
                        ✕ Reddedildi
                      </span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 3px; max-width: 380px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                      {{ bid.notes }}
                    </div>
                  </div>
                </div>

                <!-- Price & Action Buttons -->
                <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
                  <div style="text-align: right;">
                    <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Aylık Teklif Tutar</span>
                    <div style="font-weight: 800; font-size: 1.3rem; color: #a78bfa;">
                      ₺{{ bid.monthly_price_try?.toLocaleString() }} <span style="font-size: 0.75rem; font-weight: 500; color: var(--text-muted);">+ KDV</span>
                    </div>
                  </div>

                  <div style="display: flex; gap: 8px;">
                    <!-- Examine Bid Details -->
                    <button @click="openBidDetailModal(bid, quote)" class="btn btn-secondary" 
                            style="padding: 8px 14px; font-size: 0.82rem; font-weight: 700; border-color: rgba(124, 58, 237, 0.3); color: #a78bfa; background: rgba(124, 58, 237, 0.08);">
                      🔍 Teklifi İncele
                    </button>

                    <!-- Approve Bid -->
                    <button v-if="bid.status === 'Beklemede' && quote.status !== 'Sözleşme İmzalandı' && quote.status !== 'İstek Silindi'" 
                            @click="approveBid(bid.id, quote)" class="btn btn-primary" 
                            style="padding: 8px 14px; font-size: 0.82rem; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);">
                      ✓ Teklifi Onayla
                    </button>

                    <!-- Reject Bid -->
                    <button v-if="bid.status === 'Beklemede' && quote.status !== 'İstek Silindi'" 
                            @click="rejectBid(bid.id)" class="btn btn-secondary" 
                            style="padding: 8px 12px; font-size: 0.82rem; font-weight: 700; border-color: rgba(239, 68, 68, 0.25); color: #ef4444; background: rgba(239, 68, 68, 0.05);">
                      ✕ Reddet
                    </button>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>
      </div>
    </main>
  </div>

  <!-- Multi-Vehicle Group & Detailed Quote Request Modal -->
  <div v-if="showNewQuoteModal" class="modal-overlay" @click.self="showNewQuoteModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 860px; padding: 30px; max-height: 90vh; overflow-y: auto; background: #ffffff; color: #0f172a; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
      
      <!-- Modal Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px;">
        <div>
          <h2 style="color: #6d28d9; display: flex; align-items: center; gap: 10px; font-size: 1.4rem; font-weight: 800; margin: 0;">
            <span>🚀</span> Yeni Kiralama Teklifi İste
          </h2>
          <p style="color: #64748b; font-size: 0.88rem; margin-top: 5px; margin-bottom: 0;">
            Farklı segmentlerde araç grupları ekleyebilir veya detaylı teklif talebi oluşturabilirsiniz.
          </p>
        </div>
        <button @click="showNewQuoteModal = false" style="background: #f1f5f9; border: none; font-size: 1.2rem; color: #64748b; cursor: pointer; padding: 6px 12px; border-radius: 8px; font-weight: 700; transition: all 0.2s;">✕</button>
      </div>

      <form @submit.prevent="openPreviewModal" style="display: flex; flex-direction: column; gap: 20px;">
        <!-- Vehicle Groups List -->
        <div style="display: flex; flex-direction: column; gap: 20px;">
          <div v-for="(item, index) in quoteItems" :key="item.id" 
               style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 20px; position: relative;">
            
            <!-- Group Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px;">
              <span style="font-weight: 800; color: #475569; font-size: 0.98rem; display: flex; align-items: center; gap: 8px;">
                <span style="background: #7c3aed; color: #ffffff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 800;">
                  {{ index + 1 }}
                </span>
                Araç Grubu #{{ index + 1 }}
              </span>

              <button type="button" v-if="quoteItems.length > 1" @click="removeQuoteItem(index)" 
                      style="background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; border-radius: 8px; padding: 6px 12px; font-size: 0.8rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                <span>🗑️</span> Grubu Sil
              </button>
            </div>

            <!-- Segment & Type Selection -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
              <!-- Vehicle Segment -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 8px; color: #334155;">
                  Araç Segmenti
                </label>
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px;">
                  <button type="button" v-for="seg in ['A', 'B', 'C', 'D', 'E']" :key="seg"
                          @click="item.vehicle_segment = seg"
                          :style="{
                            background: item.vehicle_segment === seg ? '#7c3aed' : '#ffffff',
                            border: item.vehicle_segment === seg ? '2px solid #7c3aed' : '1px solid #cbd5e1',
                            color: item.vehicle_segment === seg ? '#ffffff' : '#334155',
                            fontWeight: item.vehicle_segment === seg ? '800' : '600'
                          }"
                          style="padding: 10px 2px; border-radius: 8px; cursor: pointer; text-align: center; font-size: 0.9rem;">
                    {{ seg }}
                  </button>
                </div>
              </div>

              <!-- Vehicle Type -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 8px; color: #334155;">
                  Gövde Tipi
                </label>
                <select v-model="item.vehicle_type" 
                        style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 10px 12px; border-radius: 8px; width: 100%; font-size: 0.9rem; font-weight: 600; outline: none;">
                  <option value="Sedan">Sedan</option>
                  <option value="SUV">SUV</option>
                  <option value="Hatchback">Hatchback</option>
                  <option value="Hafif Ticari">Hafif Ticari</option>
                  <option value="Station Wagon">Station Wagon</option>
                </select>
              </div>
            </div>

            <!-- Count, Duration & Mileage Grid -->
            <div style="display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 16px; align-items: center;">
              <!-- Vehicle Count Slider -->
              <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label style="font-weight: 700; font-size: 0.83rem; color: #334155;">Araç Adedi</label>
                  <span style="font-weight: 800; color: #6d28d9; font-size: 0.95rem; background: #f3e8ff; padding: 2px 8px; border-radius: 6px; border: 1px solid #d8b4fe;">{{ item.vehicle_count }} Adet</span>
                </div>
                <input type="range" v-model.number="item.vehicle_count" min="1" max="50" style="width: 100%; accent-color: #7c3aed;">
              </div>

              <!-- Duration -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 6px; color: #334155;">
                  Kiralama Süresi
                </label>
                <select v-model.number="item.duration_months" 
                        style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 10px 12px; border-radius: 8px; width: 100%; font-size: 0.9rem; font-weight: 600;">
                  <option :value="12">12 Ay</option>
                  <option :value="24">24 Ay</option>
                  <option :value="36">36 Ay</option>
                  <option :value="48">48 Ay</option>
                </select>
              </div>

              <!-- Mileage -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 6px; color: #334155;">
                  Yıllık KM Limit
                </label>
                <select v-model.number="item.estimated_annual_mileage" 
                        style="background: #ffffff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 10px 12px; border-radius: 8px; width: 100%; font-size: 0.9rem; font-weight: 600;">
                  <option :value="10000">10.000 km</option>
                  <option :value="20000">20.000 km</option>
                  <option :value="30000">30.000 km</option>
                  <option :value="40000">40.000 km</option>
                  <option :value="50000">50.000 km</option>
                </select>
              </div>
            </div>

            <!-- Detailed Request Form Toggle for THIS Specific Group -->
            <div style="margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
              <button type="button" @click="item.show_details = !item.show_details" 
                      :style="{ background: item.show_details ? '#f3e8ff' : '#ffffff', border: item.show_details ? '2px solid #7c3aed' : '1.5px solid #cbd5e1' }"
                      style="width: 100%; padding: 10px 14px; border-radius: 10px; color: #6d28d9; font-weight: 800; font-size: 0.88rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                <span style="display: flex; align-items: center; gap: 8px;">
                  <span>📋</span>
                  <span>Araç Grubu #{{ index + 1 }} İçin Detaylı Şartname / Teklif Şartları Belirle (İsteğe Bağlı)</span>
                </span>
                <span>{{ item.show_details ? '▲ Gizle' : '▼ Detaylı Şartlar Ekle' }}</span>
              </button>
            </div>

            <!-- Detailed Specification Form Panel for THIS Specific Group -->
            <div v-if="item.show_details" style="margin-top: 15px; background: #ffffff; border: 2px solid #c7d2fe; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; gap: 16px;">
              
              <h4 style="font-size: 0.98rem; font-weight: 800; color: #4338ca; margin: 0; display: flex; align-items: center; gap: 8px;">
                <span>📝</span> ARAÇ GRUBU #{{ index + 1 }} DETAYLI ŞARTNAMESİ
              </h4>

              <!-- Tarih Aralığı -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 6px; color: #334155;">
                  📅 Araç İstenilen Tarih Aralığı
                </label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                  <div>
                    <span style="font-size: 0.78rem; color: #64748b;">Başlangıç Tarihi:</span>
                    <input type="date" v-model="item.details.start_date" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px; border-radius: 8px; width: 100%; font-weight: 600;">
                  </div>
                  <div>
                    <span style="font-size: 0.78rem; color: #64748b;">Bitiş / Teslim Tarihi:</span>
                    <input type="date" v-model="item.details.end_date" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px; border-radius: 8px; width: 100%; font-weight: 600;">
                  </div>
                </div>
              </div>

              <!-- Marka Seçenekleri -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 6px; color: #334155;">
                  🚗 Marka Seçenekleri <span style="font-size: 0.75rem; color: #6d28d9; font-weight: 600;">(Birden fazla marka eklenebilir)</span>
                </label>
                <select @change="addBrandFromSelect(item, $event)" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px 12px; border-radius: 8px; width: 100%; font-size: 0.85rem; font-weight: 600; cursor: pointer; margin-bottom: 8px;">
                  <option value="" disabled selected>➕ Listeden marka seçip ekleyin...</option>
                  <option v-for="(models, b) in brandModelMap" :key="b" :value="b" :disabled="item.details.selected_brands.includes(b)">
                    {{ b }} {{ item.details.selected_brands.includes(b) ? '(Eklendi)' : '' }}
                  </option>
                </select>

                <!-- Selected Brands Badges -->
                <div v-if="item.details.selected_brands.length > 0" style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; padding: 6px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px;">
                  <span v-for="b in item.details.selected_brands" :key="b" 
                        style="background: #7c3aed; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-weight: 700; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px;">
                    {{ b }}
                    <button type="button" @click="removeBrand(item, b)" title="Kaldır" style="background: rgba(255,255,255,0.25); border: none; color: #fff; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; cursor: pointer;">✕</button>
                  </span>
                </div>

                <!-- Custom Brand Input with Comma Separation -->
                <div style="margin-top: 6px;">
                  <span style="font-size: 0.76rem; font-weight: 600; color: #64748b; margin-bottom: 3px; display: block;">
                    💡 Listede olmayan markaları yazarken aralarına virgül (,) koyarak birden fazla ekleyebilirsiniz:
                  </span>
                  <input type="text" 
                         v-model="item.details.custom_brand_input"
                         @input="handleCustomBrandInput(item, $event)"
                         @keydown.enter.prevent="addCustomBrandBadge(item)"
                         @blur="addCustomBrandBadge(item)"
                         placeholder="Örn: Alfa Romeo, Subaru, Mini (virgül koyup ekleyin)..." 
                         style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px 12px; border-radius: 8px; width: 100%; font-size: 0.85rem; font-weight: 500;">
                  
                  <!-- Custom Brand Badges -->
                  <div v-if="item.details.custom_brands && item.details.custom_brands.length > 0" 
                       style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; padding: 6px; background: #faf5ff; border: 1px dashed #c084fc; border-radius: 8px;">
                    <span v-for="cb in item.details.custom_brands" :key="cb" 
                          style="background: #9333ea; color: #ffffff; padding: 3px 10px; border-radius: 14px; font-weight: 700; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 6px;">
                      {{ cb }}
                      <button type="button" @click="removeCustomBrandBadge(item, cb)" title="Kaldır" 
                              style="background: rgba(255,255,255,0.25); border: none; color: #fff; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; cursor: pointer;">✕</button>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Model Seçenekleri -->
              <div>
                <label style="display: block; font-weight: 700; font-size: 0.83rem; margin-bottom: 6px; color: #334155;">
                  🚙 Model Seçenekleri <span style="font-size: 0.75rem; color: #6d28d9; font-weight: 600;">(Seçilen markalara bağlıdır)</span>
                </label>
                
                <div v-if="item.details.selected_brands.length === 0" style="background: #f1f5f9; border: 1.5px dashed #cbd5e1; padding: 8px 12px; border-radius: 8px; color: #64748b; font-size: 0.82rem; font-weight: 600; margin-bottom: 8px;">
                  ⚠️ Model seçebilmek için lütfen önce yukarıdan en az bir marka seçiniz.
                </div>

                <select v-else @change="addModelFromSelect(item, $event)" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px 12px; border-radius: 8px; width: 100%; font-size: 0.85rem; font-weight: 600; cursor: pointer; margin-bottom: 8px;">
                  <option value="" disabled selected>➕ Listeden model seçip ekleyin ({{ availableModelsForItem(item).length }} Model)...</option>
                  <optgroup v-for="b in item.details.selected_brands" :key="b" :label="b + ' Modelleri'">
                    <option v-for="m in brandModelMap[b]" :key="m" :value="m" :disabled="item.details.selected_models.includes(m)">
                      {{ b }} {{ m }} {{ item.details.selected_models.includes(m) ? '(Eklendi)' : '' }}
                    </option>
                  </optgroup>
                </select>

                <!-- Selected Models Badges -->
                <div v-if="item.details.selected_models.length > 0" style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; padding: 6px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px;">
                  <span v-for="m in item.details.selected_models" :key="m" 
                        style="background: #4f46e5; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-weight: 700; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px;">
                    {{ m }}
                    <button type="button" @click="removeModel(item, m)" title="Kaldır" style="background: rgba(255,255,255,0.25); border: none; color: #fff; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; cursor: pointer;">✕</button>
                  </span>
                </div>

                <!-- Custom Model Input with Comma Separation -->
                <div style="margin-top: 6px;">
                  <span style="font-size: 0.76rem; font-weight: 600; color: #64748b; margin-bottom: 3px; display: block;">
                    💡 Listede olmayan modelleri yazarken aralarına virgül (,) koyarak birden fazla ekleyebilirsiniz:
                  </span>
                  <input type="text" 
                         v-model="item.details.custom_model_input"
                         @input="handleCustomModelInput(item, $event)"
                         @keydown.enter.prevent="addCustomModelBadge(item)"
                         @blur="addCustomModelBadge(item)"
                         placeholder="Örn: Giulia, Outback, Countryman (virgül koyup ekleyin)..." 
                         style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px 12px; border-radius: 8px; width: 100%; font-size: 0.85rem; font-weight: 500;">
                  
                  <!-- Custom Model Badges -->
                  <div v-if="item.details.custom_models && item.details.custom_models.length > 0" 
                       style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; padding: 6px; background: #eef2ff; border: 1px dashed #818cf8; border-radius: 8px;">
                    <span v-for="cm in item.details.custom_models" :key="cm" 
                          style="background: #4338ca; color: #ffffff; padding: 3px 10px; border-radius: 14px; font-weight: 700; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 6px;">
                      {{ cm }}
                      <button type="button" @click="removeCustomModelBadge(item, cm)" title="Kaldır" 
                              style="background: rgba(255,255,255,0.25); border: none; color: #fff; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: bold; cursor: pointer;">✕</button>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Model Yılı & Plaka & Renk Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px; color: #334155;">Model Yılı</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                    <button type="button" v-for="y in [2023, 2024, 2025, 2026]" :key="y"
                            @click="toggleMultiSelect(item.details.selected_model_years, y)"
                            :style="{
                              background: item.details.selected_model_years.includes(y) ? '#4f46e5' : '#fff',
                              border: item.details.selected_model_years.includes(y) ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                              color: item.details.selected_model_years.includes(y) ? '#fff' : '#334155'
                            }"
                            style="padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; cursor: pointer;">
                      {{ y }}
                    </button>
                  </div>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px; color: #334155;">Plaka Şehri/Talebi</label>
                  <input type="text" v-model="item.details.plate_request" placeholder="Örn: 34 İstanbul" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.8rem; font-weight: 600;">
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px; color: #334155;">Renk Tercihleri</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                    <button type="button" v-for="c in ['Beyaz', 'Siyah', 'Gri', 'Füme', 'Mavi']" :key="c"
                            @click="toggleMultiSelect(item.details.selected_colors, c)"
                            :style="{
                              background: item.details.selected_colors.includes(c) ? '#4f46e5' : '#fff',
                              border: item.details.selected_colors.includes(c) ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                              color: item.details.selected_colors.includes(c) ? '#fff' : '#334155'
                            }"
                            style="padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem; cursor: pointer;">
                      {{ c }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Yakıt Türü & Şanzıman Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px; color: #334155;">Yakıt Türü</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    <button type="button" v-for="f in ['Benzin', 'Dizel', 'Hibrit', 'Elektrik']" :key="f"
                            @click="toggleMultiSelect(item.details.selected_fuel_types, f)"
                            :style="{
                              background: item.details.selected_fuel_types.includes(f) ? '#10b981' : '#fff',
                              border: item.details.selected_fuel_types.includes(f) ? '2px solid #10b981' : '1px solid #cbd5e1',
                              color: item.details.selected_fuel_types.includes(f) ? '#fff' : '#334155'
                            }"
                            style="padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; cursor: pointer;">
                      {{ f }}
                    </button>
                  </div>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px; color: #334155;">Şanzıman</label>
                  <div style="display: flex; gap: 6px;">
                    <button type="button" v-for="t in ['Otomatik', 'Manuel']" :key="t"
                            @click="toggleMultiSelect(item.details.selected_transmissions, t)"
                            :style="{
                              background: item.details.selected_transmissions.includes(t) ? '#10b981' : '#fff',
                              border: item.details.selected_transmissions.includes(t) ? '2px solid #10b981' : '1px solid #cbd5e1',
                              color: item.details.selected_transmissions.includes(t) ? '#fff' : '#334155'
                            }"
                            style="padding: 4px 12px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; cursor: pointer;">
                      {{ t }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- 🛠️ Servis, Muayene, Bakım & Vale Hizmetleri -->
              <div style="background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-top: 6px;">
                <label style="display: block; font-weight: 800; font-size: 0.82rem; margin-bottom: 6px; color: #4338ca;">
                  🛎️ Vale Hizmeti Kapsamı <span style="font-size: 0.75rem; color: #64748b; font-weight: 500;">(Çoklu seçebilirsiniz)</span>
                </label>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                  <button type="button" v-for="v in ['Teslimat', 'Muayene', 'Servis', 'Bakım']" :key="v"
                          @click="toggleMultiSelect(item.details.valet_services, v)"
                          :style="{
                            background: item.details.valet_services.includes(v) ? '#7c3aed' : '#fff',
                            border: item.details.valet_services.includes(v) ? '2px solid #7c3aed' : '1px solid #cbd5e1',
                            color: item.details.valet_services.includes(v) ? '#fff' : '#334155'
                          }"
                          style="padding: 5px 12px; border-radius: 8px; font-weight: 700; font-size: 0.78rem; cursor: pointer;">
                    {{ item.details.valet_services.includes(v) ? '✓ ' + v : '+ ' + v }}
                  </button>
                </div>
              </div>

              <!-- Bakım & Lastik Şartları Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px;">
                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Periyodik Bakım</label>
                  <select v-model="item.details.periodic_maintenance" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Yetkili Servis (Marka Yetkili Bayi)">Yetkili Servis</option>
                    <option value="Yetkilendirilmiş Özel Servis">Özel Servis</option>
                    <option value="Fark Etmez">Fark Etmez</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Periyodik Lastik Değişimi</label>
                  <select v-model="item.details.tire_change_period" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="30.000 km">30.000 km</option>
                    <option value="40.000 km">40.000 km</option>
                    <option value="50.000 km">50.000 km</option>
                    <option value="Her Sezon">Her Sezon</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Kış Lastiği Markası</label>
                  <select v-model="item.details.winter_tire_brand" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Michelin">Michelin</option>
                    <option value="Continental">Continental</option>
                    <option value="Goodyear">Goodyear</option>
                    <option value="Pirelli">Pirelli</option>
                    <option value="Lassa">Lassa</option>
                    <option value="Petlas">Petlas</option>
                    <option value="Tercihsiz / Tedarikçi Seçimi">Tedarikçi Seçimi</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Yaz Lastiği Markası</label>
                  <select v-model="item.details.summer_tire_brand" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Michelin">Michelin</option>
                    <option value="Continental">Continental</option>
                    <option value="Goodyear">Goodyear</option>
                    <option value="Pirelli">Pirelli</option>
                    <option value="Lassa">Lassa</option>
                    <option value="Petlas">Petlas</option>
                    <option value="Tercihsiz / Tedarikçi Seçimi">Tedarikçi Seçimi</option>
                  </select>
                </div>
              </div>

              <!-- Giydirme, Cam Filmi & Şoförlü Kiralama Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px;">
                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Cam Filmi</label>
                  <select v-model="item.details.window_film" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Var - Standart">Var - Standart</option>
                    <option value="Var - 1 Numara">Var - 1 Numara</option>
                    <option value="Var - 2 Numara">Var - 2 Numara</option>
                    <option value="Yok">Yok</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Renk & PPF Kaplama</label>
                  <select v-model="item.details.color_coating_ppf" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Yok">Yok</option>
                    <option value="Şeffaf PPF Kaplama">Şeffaf PPF Kaplama</option>
                    <option value="Tam Renk Kaplama">Tam Renk Kaplama</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Şoförlü Kiralama</label>
                  <select v-model="item.details.chauffeur_service" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option :value="false">Hayır - Şoförsüz</option>
                    <option :value="true">Evet - Şoförlü (Özel Sözleşme)</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Ödeme Vadesi</label>
                  <select v-model="item.details.payment_term" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Peşin / Aynı Ay">Peşin / Aynı Ay</option>
                    <option value="30 Gün Vade">30 Gün Vade</option>
                    <option value="60 Gün Vade">60 Gün Vade</option>
                    <option value="90 Gün Vade">90 Gün Vade</option>
                  </select>
                </div>
              </div>

              <!-- Finans, İMM & Teminatlar Grid -->
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px;">
                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">İMM Limiti</label>
                  <select v-model="item.details.imm_limit" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="10 Milyon ₺">10 Milyon ₺</option>
                    <option value="20 Milyon ₺">20 Milyon ₺</option>
                    <option value="30 Milyon ₺">30 Milyon ₺</option>
                    <option value="40 Milyon ₺">40 Milyon ₺</option>
                    <option value="50 Milyon ₺">50 Milyon ₺</option>
                    <option value="Sınırsız İMM">Sınırsız İMM</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Anahtar Teminat Yükselt</label>
                  <select v-model="item.details.key_coverage_amount" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option value="" disabled selected>Seçiniz...</option>
                    <option value="Standart">Standart</option>
                    <option value="40.000 ₺">40.000 ₺</option>
                    <option value="50.000 ₺">50.000 ₺</option>
                    <option value="60.000 ₺">60.000 ₺</option>
                    <option value="100.000 ₺">100.000 ₺</option>
                    <option value="150.000 ₺">150.000 ₺</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Emniyeti Suistimal</label>
                  <select v-model="item.details.misappropriation_coverage" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option :value="true">Dahil Olsun</option>
                    <option :value="false">Dahil Olmasın</option>
                  </select>
                </div>

                <div>
                  <label style="display: block; font-weight: 700; font-size: 0.78rem; margin-bottom: 4px; color: #334155;">Kasko Tipi</label>
                  <select v-model="item.details.full_casco" style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 6px 8px; border-radius: 6px; width: 100%; font-size: 0.78rem; font-weight: 600;">
                    <option :value="true">Full Muafiyetsiz Kasko</option>
                    <option :value="false">Standart Kasko</option>
                  </select>
                </div>
              </div>

              <!-- Ek Opsiyonel Checkbox'lar -->
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; font-size: 0.8rem; background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #cbd5e1;">
                <label style="display: flex; align-items: center; gap: 6px; font-weight: 700; cursor: pointer; color: #1e293b;">
                  <input type="checkbox" v-model="item.details.special_plate" style="accent-color: #7c3aed;"> Özel Plaka Talebi
                </label>
                <label style="display: flex; align-items: center; gap: 6px; font-weight: 700; cursor: pointer; color: #1e293b;">
                  <input type="checkbox" v-model="item.details.company_logo" style="accent-color: #7c3aed;"> Reklam Logosu / Giydirme
                </label>
              </div>

              <!-- Notlar -->
              <input type="text" v-model="item.details.custom_terms" placeholder="Bu gruba özel diğer şart veya açıklamalar..." style="background: #fff; border: 1.5px solid #cbd5e1; color: #0f172a; padding: 8px 12px; border-radius: 8px; width: 100%; font-size: 0.82rem; font-weight: 500;">

            </div>

          </div>
        </div>

        <!-- Add New Group Button -->
        <button type="button" @click="addQuoteItem" 
                style="background: #f5f3ff; border: 2px dashed #8b5cf6; color: #6d28d9; border-radius: 12px; padding: 12px; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 0.9rem;">
          <span>➕</span>
          <span>Farklı Araç Grubu / Segment Ekle</span>
        </button>

        <!-- Summary & Info Box -->
        <div style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
          <div>
            <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; font-weight: 800; letter-spacing: 0.05em;">
              📋 TALEP ÖZETİ
            </div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a; margin-top: 4px;">
              {{ totalVehiclesCount }} Araç <span style="font-size: 0.95rem; font-weight: 600; color: #6d28d9; background: #f3e8ff; padding: 2px 10px; border-radius: 12px; margin-left: 6px;">({{ quoteItems.length }} Farklı Paket)</span>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; color: #475569; font-size: 0.85rem; font-weight: 600; background: #ffffff; padding: 8px 14px; border-radius: 10px; border: 1px solid #e2e8f0;">
            <span>ℹ️</span>
            <span>Talebiniz tedarikçilere iletilecek ve özel teklifler toplanacaktır.</span>
          </div>
        </div>

        <!-- Form Actions -->
        <div style="display: flex; gap: 15px; justify-content: flex-end; border-top: 1px solid #e2e8f0; padding-top: 20px;">
          <button type="button" @click="showNewQuoteModal = false" class="btn btn-secondary" style="background: #f1f5f9; border: 1px solid #cbd5e1; color: #475569; font-weight: 700; padding: 10px 20px; border-radius: 8px;">Vazgeç</button>
          <button type="submit" class="btn btn-primary" style="background: linear-gradient(135deg, #6d28d9, #4f46e5); color: #ffffff; border: none; font-weight: 800; padding: 12px 28px; border-radius: 10px; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(109, 40, 217, 0.3); cursor: pointer;">
            📋 Teklif Talebini İncele & Önizle ({{ totalVehiclesCount }} Araç)
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Quote Request Summary Preview & Confirmation Modal -->
  <div v-if="showPreviewModal" class="modal-overlay" @click.self="showPreviewModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 760px; padding: 30px; background: #ffffff; color: #0f172a; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); max-height: 90vh; overflow-y: auto;">
      
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px;">
        <div>
          <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 800; color: #6d28d9; letter-spacing: 0.05em;">TEKLİF TALEBİ ÖZETİ VE ÖNİZLEME</span>
          <h2 style="font-weight: 800; font-size: 1.4rem; color: #0f172a; margin-top: 2px;">
            📄 Teklif Talebi Belgeniz
          </h2>
          <p style="color: #64748b; font-size: 0.88rem; margin-top: 4px; margin-bottom: 0;">
            Lütfen tedarikçilere iletilmeden önce teklif talebi bilgilerinizi kontrol ediniz.
          </p>
        </div>
        <button type="button" @click="showPreviewModal = false" style="background: #f1f5f9; border: none; font-size: 1.2rem; color: #64748b; cursor: pointer; padding: 6px 12px; border-radius: 8px; font-weight: 700;">✕</button>
      </div>

      <!-- Company Profile Summary Box -->
      <div style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 18px; margin-bottom: 22px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; font-size: 0.88rem;">
        <div>
          <span style="color: #64748b; font-size: 0.78rem; font-weight: 600;">Talep Eden Şirket:</span>
          <div style="font-weight: 800; color: #0f172a; font-size: 0.95rem;">{{ companyName }}</div>
        </div>
        <div>
          <span style="color: #64748b; font-size: 0.78rem; font-weight: 600;">İletişim E-posta:</span>
          <div style="font-weight: 700; color: #0f172a;">{{ userEmail }}</div>
        </div>
        <div>
          <span style="color: #64748b; font-size: 0.78rem; font-weight: 600;">İletişim Telefon:</span>
          <div style="font-weight: 700; color: #0f172a;">{{ companyPhone }}</div>
        </div>
        <div>
          <span style="color: #64748b; font-size: 0.78rem; font-weight: 600;">Toplam Araç Hacmi:</span>
          <div style="font-weight: 800; color: #6d28d9; font-size: 0.95rem;">{{ totalVehiclesCount }} Araç ({{ quoteItems.length }} Paket)</div>
        </div>
      </div>

      <!-- Vehicle Groups Detailed Breakdown Document -->
      <div style="margin-bottom: 25px; display: flex; flex-direction: column; gap: 16px;">
        <h3 style="font-size: 0.95rem; font-weight: 800; color: #334155; margin: 0; text-transform: uppercase; letter-spacing: 0.04em;">
          🚗 Talep Edilen Araç Grupları & Şartnameler
        </h3>

        <div v-for="(item, idx) in quoteItems" :key="item.id" style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 18px;">
          
          <!-- Group Title -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">
            <span style="font-weight: 800; color: #4338ca; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
              <span style="background: #7c3aed; color: #fff; width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem;">{{ idx + 1 }}</span>
              Araç Grubu #{{ idx + 1 }}: {{ item.vehicle_count }} Adet {{ item.vehicle_segment }} Segment {{ item.vehicle_type }}
            </span>
            <span style="font-size: 0.82rem; background: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 14px; font-weight: 800;">
              {{ item.duration_months }} Ay | {{ item.estimated_annual_mileage?.toLocaleString() }} km/yıl
            </span>
          </div>

          <!-- Group Details Preview (If Present) -->
          <div v-if="item.show_details && hasDetails(item.details)" style="display: flex; flex-direction: column; gap: 8px; font-size: 0.84rem; color: #334155; background: #ffffff; padding: 14px; border-radius: 10px; border: 1px solid #cbd5e1;">
            <div v-if="item.details.start_date || item.details.end_date">
              <strong>📅 Tarih Aralığı:</strong> {{ item.details.start_date || 'Esnek' }} - {{ item.details.end_date || 'Esnek' }}
            </div>
            
            <div v-if="getAllBrandsForItem(item).length > 0">
              <strong>🏷️ Marka Tercihleri:</strong> <span style="color: #7c3aed; font-weight: 700;">{{ getAllBrandsForItem(item).join(', ') }}</span>
            </div>

            <div v-if="getAllModelsForItem(item).length > 0">
              <strong>🚙 Model Tercihleri:</strong> <span style="color: #4f46e5; font-weight: 700;">{{ getAllModelsForItem(item).join(', ') }}</span>
            </div>

            <div v-if="item.details.selected_model_years?.length">
              <strong>📅 Model Yılları:</strong> {{ item.details.selected_model_years.join(', ') }}
            </div>

            <div v-if="item.details.selected_colors?.length || item.details.plate_request || item.details.special_plate">
              <strong>🎨 Renk & Plaka:</strong> {{ item.details.selected_colors.join(', ') }} {{ item.details.plate_request ? '(' + item.details.plate_request + ')' : '' }} {{ item.details.special_plate ? '[Özel Plaka Talebi]' : '' }}
            </div>

            <div v-if="item.details.selected_fuel_types?.length || item.details.selected_transmissions?.length">
              <strong>⛽ Yakıt & Şanzıman:</strong> {{ item.details.selected_fuel_types.join(', ') }} | {{ item.details.selected_transmissions.join(', ') }}
            </div>

            <div v-if="item.details.valet_services?.length">
              <strong>🛎️ Vale Hizmeti Kapsamı:</strong> <span style="color: #7c3aed; font-weight: 700;">{{ item.details.valet_services.join(', ') }}</span>
            </div>

            <div v-if="item.details.periodic_maintenance || item.details.tire_change_period">
              <strong>🔧 Bakım & Lastik Değişimi:</strong> {{ item.details.periodic_maintenance || 'Standart' }} | Lastik: {{ item.details.tire_change_period || 'Standart' }}
            </div>

            <div v-if="item.details.winter_tire_brand || item.details.summer_tire_brand">
              <strong>🛞 Lastik Markaları:</strong> Kış: {{ item.details.winter_tire_brand || 'Standart' }} | Yaz: {{ item.details.summer_tire_brand || 'Standart' }}
            </div>

            <div v-if="item.details.window_film || item.details.color_coating_ppf || item.details.company_logo">
              <strong>✨ Ekipman, Giydirme & Film:</strong> Cam Filmi: {{ item.details.window_film || 'Yok' }} | Kaplama: {{ item.details.color_coating_ppf || 'Yok' }} {{ item.details.company_logo ? '| [Reklam Logosu Giydirme Var]' : '' }}
            </div>

            <div v-if="item.details.chauffeur_service !== undefined">
              <strong>👤 Şoförlü Kiralama:</strong> {{ item.details.chauffeur_service ? 'Evet (Şoför Hizmeti Dahil - Özel Sözleşme)' : 'Hayır (Şoförsüz)' }}
            </div>

            <div v-if="item.details.payment_term || item.details.imm_limit">
              <strong>💳 Ödeme Vadesi & İMM:</strong> Vade: {{ item.details.payment_term || 'Standart' }} | İMM Limiti: {{ item.details.imm_limit || 'Standart' }}
            </div>

            <div v-if="item.details.key_coverage_amount || item.details.misappropriation_coverage || item.details.full_casco">
              <strong>🛡️ Teminatlar & Kasko:</strong> Anahtar Teminatı: {{ item.details.key_coverage_amount || 'Standart' }} | Emniyeti Suistimal: {{ item.details.misappropriation_coverage ? 'Dahil' : 'Haric' }} | Kasko: {{ item.details.full_casco ? 'Full Muafiyetsiz Kasko' : 'Standart Kasko' }}
            </div>

            <div v-if="item.details.custom_terms">
              <strong>📝 Özel Notlar:</strong> {{ item.details.custom_terms }}
            </div>
          </div>
          <div v-else style="font-size: 0.83rem; color: #64748b; font-style: italic;">
            Bu araç grubu için standart kiralama şartları geçerlidir (özel detaylı şartname girilmedi).
          </div>
        </div>
      </div>

      <!-- Action Buttons (Düzenlemeye Dön vs. Onayla & Gönder) -->
      <div style="display: flex; gap: 14px; justify-content: flex-end; border-top: 1px solid #e2e8f0; padding-top: 18px;">
        <button type="button" @click="showPreviewModal = false" class="btn btn-secondary" 
                style="background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 10px 20px; border-radius: 10px; font-size: 0.9rem; cursor: pointer;">
          ✏️ Düzenlemeye Dön
        </button>
        <button type="button" :disabled="submittingQuote" @click="confirmAndSubmitQuote" class="btn btn-primary" 
                style="background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; border: none; font-weight: 800; padding: 12px 24px; border-radius: 10px; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); cursor: pointer;">
          <span v-if="submittingQuote">Talebiniz Alınıyor...</span>
          <span v-else>✓ Teklif Talebini Onayla & Gönder 🚀</span>
        </button>
      </div>

    </div>
  </div>

  <!-- Detailed Bid Inspection Modal (Teklifi İncele Modalı) -->
  <div v-if="showBidDetailModal" class="modal-overlay" @click.self="showBidDetailModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 680px; padding: 28px; background: #ffffff; color: #0f172a; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); max-height: 90vh; overflow-y: auto;">
      
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px;">
        <div style="display: flex; align-items: center; gap: 14px;">
          <div style="width: 50px; height: 50px; border-radius: 50%; background: #f3e8ff; border: 2px solid #c084fc; display: flex; align-items: center; justify-content: center; font-size: 1.4rem;">
            🏢
          </div>
          <div>
            <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 800; color: #6d28d9; letter-spacing: 0.05em;">TEDARİKCİ KİRALAMA TEKLİFİ</span>
            <h2 style="font-weight: 800; font-size: 1.3rem; color: #0f172a; margin-top: 2px;">
              {{ selectedBid?.supplier_name }}
            </h2>
          </div>
        </div>
        <button @click="showBidDetailModal = false" style="background: #f1f5f9; border: none; font-size: 1.2rem; color: #64748b; cursor: pointer; padding: 6px 12px; border-radius: 8px; font-weight: 700;">✕</button>
      </div>

      <!-- Price Box -->
      <div style="background: linear-gradient(135deg, #f3e8ff, #e0e7ff); border: 1.5px solid #c7d2fe; border-radius: 16px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-size: 0.8rem; text-transform: uppercase; font-weight: 800; color: #4338ca;">Aylık Kiralama Bedeli</span>
          <div style="font-size: 1.8rem; font-weight: 900; color: #6d28d9; margin-top: 2px;">
            ₺{{ selectedBid?.monthly_price_try?.toLocaleString() }} <span style="font-size: 0.9rem; font-weight: 600; color: #475569;">+ KDV / Ay</span>
          </div>
        </div>
        <span style="background: #10b981; color: #fff; font-weight: 800; font-size: 0.85rem; padding: 6px 14px; border-radius: 20px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);">
          Resmi Teklif
        </span>
      </div>

      <!-- Supplier Notes & Conditions -->
      <div style="margin-bottom: 20px;">
        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: #64748b; font-weight: 800; margin-bottom: 8px;">
          📝 Teklif Şartları & Tedarikçi Notu
        </h4>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; font-size: 0.92rem; color: #334155; line-height: 1.5;">
          {{ selectedBid?.notes || 'Tüm periyodik bakımlar, 7/24 asistans ve ikame araç hizmeti dahildir.' }}
        </div>
      </div>

      <!-- Included Services Checkbox List -->
      <div style="margin-bottom: 25px;">
        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: #64748b; font-weight: 800; margin-bottom: 10px;">
          🛠️ Teklife Dahil Olan Ücretsiz Hizmetler
        </h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div style="background: #f1f5f9; padding: 10px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 6px;">
            <span style="color: #10b981;">✓</span> 7/24 Yol Yardım ve Asistans
          </div>
          <div style="background: #f1f5f9; padding: 10px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 6px;">
            <span style="color: #10b981;">✓</span> Periyodik Bakım & Onarım
          </div>
          <div style="background: #f1f5f9; padding: 10px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 6px;">
            <span style="color: #10b981;">✓</span> Kış Lastiği Temini & Saklama
          </div>
          <div style="background: #f1f5f9; padding: 10px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 6px;">
            <span style="color: #10b981;">✓</span> Kesintisiz İkame Araç
          </div>
        </div>
      </div>

      <!-- Detailed Customer Specification (If Present) -->
      <div v-if="selectedQuoteForBid?.details && Object.keys(selectedQuoteForBid.details).length > 0" style="margin-bottom: 25px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 14px; padding: 16px;">
        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: #6d28d9; font-weight: 800; margin-bottom: 10px;">
          📋 Karşılanan Müşteri Şartnamesi
        </h4>
        <div style="font-size: 0.83rem; color: #334155; display: flex; flex-direction: column; gap: 6px;">
          <div v-if="selectedQuoteForBid.details.start_date || selectedQuoteForBid.details.end_date">
            <strong>Tarih Aralığı:</strong> {{ selectedQuoteForBid.details.start_date }} - {{ selectedQuoteForBid.details.end_date }}
          </div>
          <div v-if="selectedQuoteForBid.details.selected_brands && selectedQuoteForBid.details.selected_brands.length > 0">
            <strong>Markalar:</strong> {{ selectedQuoteForBid.details.selected_brands.join(', ') }}
          </div>
          <div v-if="selectedQuoteForBid.details.periodic_maintenance">
            <strong>Bakım Şartı:</strong> {{ selectedQuoteForBid.details.periodic_maintenance }}
          </div>
          <div v-if="selectedQuoteForBid.details.imm_limit">
            <strong>İMM Limiti:</strong> {{ selectedQuoteForBid.details.imm_limit }}
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div style="display: flex; gap: 12px; justify-content: flex-end; border-top: 1px solid #e2e8f0; padding-top: 18px;">
        <button type="button" @click="showBidDetailModal = false" class="btn btn-secondary" style="background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; font-weight: 700;">
          Kapat
        </button>
        <button v-if="selectedBid?.status === 'Beklemede'" type="button" @click="rejectBid(selectedBid.id)" class="btn btn-secondary" style="background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; font-weight: 700;">
          ✕ Teklifi Reddet
        </button>
        <button v-if="selectedBid?.status === 'Beklemede'" type="button" @click="approveBid(selectedBid.id, selectedQuoteForBid)" class="btn btn-primary" style="background: linear-gradient(135deg, #10b981, #059669); color: #fff; border: none; font-weight: 800; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
          ✓ Teklifi Onayla & Sözleşmeyi Başlat
        </button>
      </div>

    </div>
  </div>

  <!-- Success Confirmation Custom Modal -->
  <div v-if="showSuccessModal" class="modal-overlay" @click.self="showSuccessModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 480px; padding: 32px; background: #ffffff; color: #0f172a; border-radius: 24px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
      
      <div style="width: 72px; height: 72px; background: #f3e8ff; border: 2px solid #d8b4fe; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 2.2rem; box-shadow: 0 8px 20px rgba(124, 58, 237, 0.15);">
        🎉
      </div>

      <h2 style="font-weight: 800; font-size: 1.35rem; color: #1e293b; margin-bottom: 10px;">
        Teklif Talebiniz Başarıyla Alındı!
      </h2>

      <p style="color: #64748b; font-size: 0.92rem; line-height: 1.55; margin-bottom: 22px;">
        Kiralama teklif talebiniz başarıyla sisteme kaydedildi. Filo uzmanlarımız ve tedarikçilerimiz talebinizi inceleyerek en kısa sürede özel fiyat tekliflerini tarafınıza iletecektir.
      </p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; margin-bottom: 25px; text-align: left;">
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 8px;">
          <span style="color: #64748b;">Talep Edilen Araç:</span>
          <strong style="color: #0f172a;">{{ createdQuoteSummary?.totalVehicles }} Araç ({{ createdQuoteSummary?.groupCount }} Paket)</strong>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem;">
          <span style="color: #64748b;">Durum:</span>
          <span style="color: #7c3aed; font-weight: 700; background: #f3e8ff; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem;">
            ⏳ Tedarikçi Teklifleri Bekleniyor
          </span>
        </div>
      </div>

      <button @click="showSuccessModal = false" class="btn btn-primary" style="width: 100%; background: linear-gradient(135deg, #6d28d9, #4f46e5); color: #ffffff; border: none; font-weight: 800; padding: 14px 0; border-radius: 12px; font-size: 1rem; box-shadow: 0 4px 15px rgba(109, 40, 217, 0.3); cursor: pointer;">
        Harika, Tekliflerime Git ➔
      </button>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const quotes = ref([])

const showNewQuoteModal = ref(false)
const showPreviewModal = ref(false)
const showSuccessModal = ref(false)
const showBidDetailModal = ref(false)

const selectedBid = ref(null)
const selectedQuoteForBid = ref(null)
const createdQuoteSummary = ref(null)

const submittingQuote = ref(false)

const documentsUploaded = ref(true)
const hasNoVehicles = ref(false)
const companyName = ref(localStorage.getItem('fleetcar_customer_name') || 'Tekno Holding')
const userEmail = ref(localStorage.getItem('fleetcar_user_email') || 'info@teknoholding.com')
const companyPhone = ref('0212 555 0000')

// Multi-item Quote Items State with per-group details
const createEmptyDetailedForm = () => ({
  start_date: '',
  end_date: '',
  selected_durations: [],
  selected_brands: [],
  custom_brands: [],
  custom_brand_input: '',
  selected_models: [],
  custom_models: [],
  custom_model_input: '',
  selected_model_years: [],
  selected_annual_mileages: [],
  plate_request: '',
  special_plate: false,
  selected_colors: [],
  custom_color: '',
  selected_fuel_types: [],
  selected_transmissions: [],
  valet_services: [], // ['Teslimat', 'Muayene', 'Servis', 'Bakım']
  tire_change_period: '', // '30.000 km', '40.000 km', '50.000 km', 'Her Sezon'
  periodic_maintenance: '', // 'Yetkili Servis', 'Yetkilendirilmiş Özel Servis'
  window_film: '', // 'Var - Standart', 'Var - 1 Numara', 'Var - 2 Numara', 'Yok'
  winter_tire_brand: '', // 'Michelin', 'Continental', 'Goodyear', 'Pirelli', 'Lassa', 'Petlas'
  summer_tire_brand: '', // 'Michelin', 'Continental', 'Goodyear', 'Pirelli', 'Lassa', 'Petlas'
  company_logo: false, // Reklam logosu
  color_coating_ppf: '', // 'Şeffaf PPF Kaplama', 'Tam Renk Kaplama', 'Yok'
  chauffeur_service: false, // Şoförlü Kiralama (Sözleşmesi Farklı)
  payment_term: '', // 'Peşin', '30 Gün Vade', '60 Gün Vade', '90 Gün Vade'
  imm_limit: '', // '10M ₺', '20M ₺', '30M ₺', '40M ₺', '50M ₺', 'Sınırsız İMM'
  key_coverage_amount: '', // 'Standart', '40.000 ₺', '50.000 ₺', '60.000 ₺', '100.000 ₺', '150.000 ₺'
  misappropriation_coverage: false, // Emniyeti Suistimal Teminatı
  full_casco: false, // Full Kasko (Muafiyetsiz)
  custom_terms: ''
})

const createNewQuoteItem = () => ({
  id: Date.now() + Math.random(),
  vehicle_segment: 'C',
  vehicle_type: 'Sedan',
  vehicle_count: 1,
  duration_months: 12,
  estimated_annual_mileage: 20000,
  show_details: false,
  details: createEmptyDetailedForm()
})

const quoteItems = ref([
  createNewQuoteItem()
])

const brandModelMap = {
  'Renault': ['Clio', 'Megane', 'Taliant', 'Austral', 'Captur', 'Koleos', 'Express', 'Master', 'Rafale'],
  'Fiat': ['Egea Sedan', 'Egea Cross', 'Egea Hatchback', 'Fiorino', 'Doblo', 'Ducato', '600'],
  'Ford': ['Focus', 'Fiesta', 'Puma', 'Kuga', 'Tourneo Courier', 'Tourneo Custom', 'Transit', 'Ranger'],
  'Volkswagen': ['Passat', 'Golf', 'Polo', 'T-Roc', 'Tiguan', 'Taigo', 'Touareg', 'Caddy', 'Crafter'],
  'BMW': ['1 Series', '2 Series Gran Coupe', '3 Series', '4 Series', '5 Series', '7 Series', 'X1', 'X3', 'X5', 'i4', 'iX3'],
  'Mercedes-Benz': ['A-Class', 'C-Class', 'E-Class', 'S-Class', 'CLA', 'GLA', 'GLC', 'GLE', 'Vito', 'Sprinter'],
  'Toyota': ['Corolla', 'Yaris', 'Yaris Cross', 'C-HR', 'RAV4', 'Hilux', 'Proace City'],
  'Peugeot': ['208', '308', '408', '508', '2008', '3008', '5008', 'Rifter', 'Partner'],
  'Hyundai': ['i10', 'i20', 'Elantra', 'Bayon', 'Tucson', 'Santa Fe', 'Staria', 'IONIQ 5'],
  'Audi': ['A3 Sedan', 'A4 Sedan', 'A5 Sportback', 'A6 Sedan', 'Q2', 'Q3', 'Q5', 'Q7'],
  'Volvo': ['XC40', 'XC60', 'XC90', 'S60', 'S90', 'V60'],
  'Skoda': ['Fabia', 'Scala', 'Octavia', 'Superb', 'Kamiq', 'Karoq', 'Kodiaq'],
  'Opel': ['Corsa', 'Astra', 'Mokka', 'Grandland', 'Crossland', 'Combo'],
  'Nissan': ['Juke', 'Qashqai', 'X-Trail', 'Townstar'],
  'Kia': ['Picanto', 'Stonic', 'Ceed', 'Sportage', 'Sorento', 'EV6'],
  'Citroen': ['C3', 'C4', 'C4 X', 'C5 Aircross', 'Berlingo'],
  'Honda': ['Civic', 'City', 'HR-V', 'CR-V'],
  'Chery': ['Omoda 5', 'Tiggo 7 Pro', 'Tiggo 8 Pro'],
  'MG': ['ZS', 'HS', 'MG4'],
  'Cupra': ['Formentor', 'Leon', 'Ateca'],
  'BYD': ['Atto 3', 'Seal', 'Dolphin', 'Han'],
  'Tesla': ['Model 3', 'Model Y'],
  'Dacia': ['Sandero', 'Sandero Stepway', 'Duster', 'Jogger'],
  'Jeep': ['Renegade', 'Compass', 'Avenger'],
  'SEAT': ['Ibiza', 'Leon', 'Ateca', 'Arona'],
  'Alfa Romeo': ['Tonale', 'Giulia', 'Stelvio']
}

const availableModelsForItem = (item) => {
  if (!item.details || !item.details.selected_brands || item.details.selected_brands.length === 0) {
    return []
  }
  let models = []
  item.details.selected_brands.forEach(b => {
    if (brandModelMap[b]) {
      brandModelMap[b].forEach(m => {
        if (!models.includes(m)) {
          models.push(m)
        }
      })
    }
  })
  return models
}

const addBrandFromSelect = (item, e) => {
  const brand = e.target.value
  if (brand && !item.details.selected_brands.includes(brand)) {
    item.details.selected_brands.push(brand)
  }
  e.target.value = ''
}

const removeBrand = (item, brand) => {
  const idx = item.details.selected_brands.indexOf(brand)
  if (idx > -1) {
    item.details.selected_brands.splice(idx, 1)
  }
  const valid = availableModelsForItem(item)
  item.details.selected_models = item.details.selected_models.filter(m => valid.includes(m))
}

const addModelFromSelect = (item, e) => {
  const model = e.target.value
  if (model && !item.details.selected_models.includes(model)) {
    item.details.selected_models.push(model)
  }
  e.target.value = ''
}

const removeModel = (item, model) => {
  const idx = item.details.selected_models.indexOf(model)
  if (idx > -1) {
    item.details.selected_models.splice(idx, 1)
  }
}

// Comma-separated custom brand & model handlers
const handleCustomBrandInput = (item, e) => {
  const val = e.target.value
  if (val.includes(',')) {
    const parts = val.split(',')
    for (let i = 0; i < parts.length - 1; i++) {
      const trimmed = parts[i].trim()
      if (trimmed && !item.details.custom_brands.includes(trimmed)) {
        item.details.custom_brands.push(trimmed)
      }
    }
    item.details.custom_brand_input = parts[parts.length - 1]
  }
}

const addCustomBrandBadge = (item) => {
  const trimmed = (item.details.custom_brand_input || '').trim()
  if (trimmed && !item.details.custom_brands.includes(trimmed)) {
    item.details.custom_brands.push(trimmed)
    item.details.custom_brand_input = ''
  }
}

const removeCustomBrandBadge = (item, brand) => {
  const idx = item.details.custom_brands.indexOf(brand)
  if (idx > -1) {
    item.details.custom_brands.splice(idx, 1)
  }
}

const handleCustomModelInput = (item, e) => {
  const val = e.target.value
  if (val.includes(',')) {
    const parts = val.split(',')
    for (let i = 0; i < parts.length - 1; i++) {
      const trimmed = parts[i].trim()
      if (trimmed && !item.details.custom_models.includes(trimmed)) {
        item.details.custom_models.push(trimmed)
      }
    }
    item.details.custom_model_input = parts[parts.length - 1]
  }
}

const addCustomModelBadge = (item) => {
  const trimmed = (item.details.custom_model_input || '').trim()
  if (trimmed && !item.details.custom_models.includes(trimmed)) {
    item.details.custom_models.push(trimmed)
    item.details.custom_model_input = ''
  }
}

const removeCustomModelBadge = (item, model) => {
  const idx = item.details.custom_models.indexOf(model)
  if (idx > -1) {
    item.details.custom_models.splice(idx, 1)
  }
}

const getAllBrandsForItem = (item) => {
  if (!item.details) return []
  const std = item.details.selected_brands || []
  const custom = item.details.custom_brands || []
  return [...std, ...custom]
}

const getAllModelsForItem = (item) => {
  if (!item.details) return []
  const std = item.details.selected_models || []
  const custom = item.details.custom_models || []
  return [...std, ...custom]
}

const toggleMultiSelect = (targetArray, value) => {
  const idx = targetArray.indexOf(value)
  if (idx > -1) {
    targetArray.splice(idx, 1)
  } else {
    targetArray.push(value)
  }
}

const addQuoteItem = () => {
  quoteItems.value.push(createNewQuoteItem())
}

const removeQuoteItem = (index) => {
  if (quoteItems.value.length > 1) {
    quoteItems.value.splice(index, 1)
  }
}

const hasDetails = (details) => {
  if (!details) return false
  return Object.keys(details).some(key => {
    const val = details[key]
    if (Array.isArray(val)) return val.length > 0
    if (typeof val === 'boolean') return val === true
    if (typeof val === 'string') return val.trim() !== ''
    return false
  })
}

const totalVehiclesCount = computed(() => {
  return quoteItems.value.reduce((acc, item) => acc + (item.vehicle_count || 1), 0)
})

const fetchCompanyStatus = async () => {
  const customerId = localStorage.getItem('fleetcar_customer_id')
  if (!customerId) return
  try {
    const res = await fetch(`/api/company/profile?customer_id=${customerId}`)
    if (res.ok) {
      const data = await res.json()
      documentsUploaded.value = Boolean(data.documents_uploaded)
      const totalVehicles = (data.actual_vehicles_count || 0) + (data.registered_vehicles_count || 0)
      hasNoVehicles.value = (totalVehicles === 0)
      if (data.company_name) companyName.value = data.company_name
      if (data.email && data.email !== '-') userEmail.value = data.email
      if (data.phone && data.phone !== '-') companyPhone.value = data.phone
    }
  } catch (e) {
    console.error('Error fetching company status:', e)
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
  } finally {
    loading.value = false
  }
}

const selectedStatusFilter = ref('Tümü')

const statusFilterOptions = [
  { label: 'Tümü', value: 'Tümü', icon: '📋' },
  { label: 'Teklif Bekleniyor', value: 'Teklif Bekleniyor', icon: '⏳' },
  { label: 'Teklif Geldi', value: 'Teklif Geldi', icon: '📩' },
  { label: 'Sözleşme Yapıldı', value: 'Sözleşme Yapıldı', icon: '✍️' },
  { label: 'Silinen', value: 'Silinen', icon: '🗑️' }
]

const getQuoteTierPriority = (status) => {
  if (['Teklif Bekleniyor', 'Teklif Geldi', 'Teklif Verildi', 'Değerlendirmede'].includes(status)) return 1
  if (['Kabul Edildi', 'Sözleşme İmzalandı', 'Sözleşme Yapıldı'].includes(status)) return 2
  if (['İstek Silindi', 'Silindi', 'Reddedildi'].includes(status)) return 3
  return 1
}

const matchesStatusFilter = (q, filter) => {
  if (filter === 'Tümü') return true
  if (filter === 'Teklif Bekleniyor') {
    return q.status === 'Teklif Bekleniyor'
  }
  if (filter === 'Teklif Geldi') {
    return q.status === 'Teklif Geldi' || q.status === 'Teklif Verildi' || (q.bids && q.bids.length > 0 && !['Kabul Edildi', 'Sözleşme İmzalandı', 'Sözleşme Yapıldı', 'İstek Silindi', 'Silindi', 'Reddedildi'].includes(q.status))
  }
  if (filter === 'Sözleşme Yapıldı') {
    return ['Sözleşme Yapıldı', 'Kabul Edildi', 'Sözleşme İmzalandı'].includes(q.status)
  }
  if (filter === 'Silinen') {
    return ['İstek Silindi', 'Silindi', 'Reddedildi'].includes(q.status)
  }
  return true
}

const myQuotesList = computed(() => {
  return quotes.value.filter(q => 
    (q.email && q.email.toLowerCase() === userEmail.value.toLowerCase()) || 
    (q.company_name && q.company_name.toLowerCase() === companyName.value.toLowerCase())
  )
})

const getFilterCount = (filterVal) => {
  return myQuotesList.value.filter(q => matchesStatusFilter(q, filterVal)).length
}

const filteredQuotes = computed(() => {
  const list = myQuotesList.value.filter(q => matchesStatusFilter(q, selectedStatusFilter.value))
  return [...list].sort((a, b) => {
    const priorityA = getQuoteTierPriority(a.status)
    const priorityB = getQuoteTierPriority(b.status)
    if (priorityA !== priorityB) {
      return priorityA - priorityB
    }
    const timeA = a.created_at ? new Date(a.created_at).getTime() : (a.id || 0)
    const timeB = b.created_at ? new Date(b.created_at).getTime() : (b.id || 0)
    return timeB - timeA
  })
})

const getStatusBadgeClass = (status) => {
  return {
    'status-given': status === 'Teklif Verildi' || status === 'Teklif Bekleniyor',
    'status-reviewing': status === 'Değerlendirmede',
    'status-signed': status === 'Sözleşme İmzalandı',
    'status-rejected': status === 'Reddedildi' || status === 'İstek Silindi'
  }
}

const openBidDetailModal = (bid, quote) => {
  selectedBid.value = bid
  selectedQuoteForBid.value = quote
  showBidDetailModal.value = true
}

const approveBid = async (bidId, quote) => {
  if (!confirm('Bu tedarikçi teklifini onaylamak ve sözleşmeyi başlatmak istediğinize emin misiniz?')) return
  try {
    const res = await fetch(`/api/bids/${bidId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Onaylandı' })
    })

    if (res.ok) {
      showBidDetailModal.value = false
      await fetchQuotes()
      await fetchCompanyStatus()
    } else {
      alert('Teklif onaylanırken bir hata oluştu.')
    }
  } catch (e) {
    console.error('Approve bid error:', e)
  }
}

const rejectBid = async (bidId) => {
  if (!confirm('Bu tedarikçi teklifini reddetmek istediğinize emin misiniz?')) return
  try {
    const res = await fetch(`/api/bids/${bidId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Reddedildi' })
    })

    if (res.ok) {
      showBidDetailModal.value = false
      await fetchQuotes()
    } else {
      alert('Teklif reddedilirken bir hata oluştu.')
    }
  } catch (e) {
    console.error('Reject bid error:', e)
  }
}

const deleteQuoteRequest = async (quoteId) => {
  if (!confirm('Bu kiralama teklif talebini silmek/iptal etmek istediğinize emin misiniz?')) return
  try {
    const res = await fetch(`/api/quotes/${quoteId}`, {
      method: 'DELETE'
    })

    if (res.ok) {
      await fetchQuotes()
    } else {
      alert('İstek silinirken bir hata oluştu.')
    }
  } catch (e) {
    console.error('Delete quote request error:', e)
  }
}

const openPreviewModal = () => {
  // Flush any pending text in custom brand/model inputs into badges
  quoteItems.value.forEach(item => {
    if (item.details) {
      if (item.details.custom_brand_input?.trim()) {
        addCustomBrandBadge(item)
      }
      if (item.details.custom_model_input?.trim()) {
        addCustomModelBadge(item)
      }
    }
  })
  showPreviewModal.value = true
}

const openNewQuoteModal = () => {
  if (!documentsUploaded.value) {
    alert('⚠️ Kiralama teklifi alabilmeniz için şirket evraklarınızı (Vergi Levhası, İmza Sirküsü, Faaliyet Belgesi) yüklemeniz zorunludur. Lütfen önce evraklarınızı tamamlayın.')
    router.push('/dashboard/settings?tab=sirket_evraklari')
    return
  }
  showNewQuoteModal.value = true
}

const confirmAndSubmitQuote = async () => {
  if (!documentsUploaded.value) {
    alert('⚠️ Kiralama teklifi oluşturabilmeniz için şirket evraklarınızı yüklemeniz zorunludur.')
    showPreviewModal.value = false
    showNewQuoteModal.value = false
    router.push('/dashboard/settings?tab=sirket_evraklari')
    return
  }

  submittingQuote.value = true
  try {
    const payload = {
      company_name: companyName.value,
      email: userEmail.value,
      phone: companyPhone.value,
      items: quoteItems.value.map(item => {
        const brands = getAllBrandsForItem(item)
        const models = getAllModelsForItem(item)
        const itemDetails = item.show_details ? {
          ...item.details,
          selected_brands: brands,
          selected_models: models
        } : null
        return {
          vehicle_segment: item.vehicle_segment,
          vehicle_type: item.vehicle_type,
          vehicle_count: item.vehicle_count,
          duration_months: item.duration_months,
          estimated_annual_mileage: item.estimated_annual_mileage,
          details: itemDetails
        }
      }),
      details: null
    }

    const res = await fetch('/api/quotes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      createdQuoteSummary.value = {
        totalVehicles: totalVehiclesCount.value,
        groupCount: quoteItems.value.length
      }
      showPreviewModal.value = false
      showNewQuoteModal.value = false
      showSuccessModal.value = true
      quoteItems.value = [createNewQuoteItem()]
      if (route.query.new) {
        router.replace({ path: '/dashboard/quotes' })
      }
      await fetchQuotes()
    } else {
      const errData = await res.json().catch(() => ({}))
      alert(errData.detail || 'Teklif oluşturulurken bir hata meydana geldi.')
    }
  } catch (e) {
    console.error('Submit quote error:', e)
    alert('Bir hata oluştu.')
  } finally {
    submittingQuote.value = false
  }
}

watch(showNewQuoteModal, (val) => {
  if (val) {
    if (!documentsUploaded.value) {
      showNewQuoteModal.value = false
      alert('⚠️ Kiralama teklifi alabilmeniz için şirket evraklarınızı (Vergi Levhası, İmza Sirküsü, Faaliyet Belgesi) yüklemeniz zorunludur. Lütfen önce evraklarınızı tamamlayın.')
      router.push('/dashboard/settings?tab=sirket_evraklari')
      return
    }
    quoteItems.value = [createNewQuoteItem()]
  }
})

watch(() => route.query.new, (newVal) => {
  if (newVal === 'true') {
    openNewQuoteModal()
  }
})

onMounted(async () => {
  await fetchCompanyStatus()
  await fetchQuotes()
  if (route.query.new === 'true') {
    openNewQuoteModal()
  }
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
  background: rgba(0, 0, 0, 0.75);
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

/* Status Filter Bar Styles */
.filter-bar-container {
  margin-top: 25px;
  padding: 16px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
}

.filter-header-label {
  font-weight: 800;
  color: #475569;
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-right: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-pills-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  color: #334155;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-filter-pill .pill-icon {
  font-size: 1rem;
}

.btn-filter-pill:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

.btn-filter-pill.active {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: #ffffff;
  border-color: #4338ca;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 7px;
  border-radius: 11px;
  background: #e2e8f0;
  font-size: 0.78rem;
  font-weight: 800;
  color: #1e293b;
}

.btn-filter-pill.active .count-badge {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.filter-counter-text {
  font-size: 0.88rem;
  color: #64748b;
  font-weight: 600;
}

.counter-highlight {
  color: #4f46e5;
  font-weight: 800;
  font-size: 0.95rem;
}
</style>
