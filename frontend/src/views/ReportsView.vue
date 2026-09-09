<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar />

    <main class="portal-main fade-in-up">
      <!-- Breadcrumb -->
      <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <router-link to="/dashboard" style="color: #64748b; text-decoration: none;">← Geri</router-link>
        <span>/ Raporlar / {{ activeReportTitle }}</span>
      </div>

      <!-- Header -->
      <header class="dashboard-header" style="margin-bottom: 25px;">
        <div>
          <h1>Operasyonel Filo Raporları</h1>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Filo maliyetleri, lokasyon takibi, kilometre ve kullanıcı analizleri.</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button @click="downloadExcel" class="btn" style="background: #10b981; color: #ffffff; padding: 10px 18px; font-size: 0.88rem; font-weight: 700; display: flex; align-items: center; gap: 6px;">
            <span>📄</span> Excel İndir
          </button>
          <button @click="downloadPDF" class="btn" style="background: #ef4444; color: #ffffff; padding: 10px 18px; font-size: 0.88rem; font-weight: 700; display: flex; align-items: center; gap: 6px;">
            <span>📄</span> PDF İndir
          </button>
        </div>
      </header>

      <!-- 6-Tab Switcher Bar (FleetRent Premium Pill Bar) -->
      <div class="category-tabs-bar">
        <button @click="activeTab = 'cost'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'cost' }">
          <span>📊</span> Araç Maliyet Raporu
        </button>
        <button @click="activeTab = 'location'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'location' }">
          <span>📍</span> Lokasyon Raporu
        </button>
        <button @click="activeTab = 'km'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'km' }">
          <span>🚘</span> Kilometre Raporu
        </button>
        <button @click="activeTab = 'usage'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'usage' }">
          <span>⏱️</span> Araç Kullanım Süresi
        </button>
        <button @click="activeTab = 'service'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'service' }">
          <span>🔧</span> Araç Servis Süresi
        </button>
        <button @click="activeTab = 'user'" class="tab-pill-btn" :class="{ 'active-tab-pill': activeTab === 'user' }">
          <span>👤</span> Kullanıcı Raporu
        </button>
      </div>

      <!-- 🔍 FIXED TOP FILTERS CARD (Plaka Ara, Kullanıcı Ara, Tarih Aralığı) -->
      <div class="glass-panel" style="padding: 20px 24px; background: #ffffff; margin-bottom: 24px; border: 1px solid #e2e8f0; border-radius: 14px;">
        <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
          <span style="display: flex; align-items: center; gap: 8px;">🔍 Sabit Rapor Filtreleri</span>
          <button @click="resetFilters" style="background: none; border: none; color: #2563eb; font-size: 0.82rem; font-weight: 600; cursor: pointer;">
            🔄 Filtreleri Temizle
          </button>
        </div>

        <div class="grid-4" style="gap: 16px;">
          <!-- Plaka Ara -->
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" style="font-size: 0.8rem; color: #64748b;">Plaka Ara</label>
            <input type="text" v-model="filterPlate" class="form-input" placeholder="PLAKA YAZIN...">
          </div>

          <!-- Kullanıcı Ara -->
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" style="font-size: 0.8rem; color: #64748b;">Kullanıcı Ara</label>
            <input type="text" v-model="filterUser" class="form-input" placeholder="Ad Soyad yazın...">
          </div>

          <!-- Başlangıç Tarihi -->
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" style="font-size: 0.8rem; color: #64748b;">Başlangıç Tarihi</label>
            <input type="date" v-model="startDate" class="form-input">
          </div>

          <!-- Bitiş Tarihi -->
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" style="font-size: 0.8rem; color: #64748b;">Bitiş Tarihi</label>
            <input type="date" v-model="endDate" class="form-input">
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 1. ARAÇ MALİYET RAPORU                                          -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'cost'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Maliyet Raporu</h2>

          <!-- Table -->
          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Kullanıcı</th>
                  <th>Plaka</th>
                  <th>Kira</th>
                  <th>HGS</th>
                  <th>Yakıt</th>
                  <th>Lastik</th>
                  <th>Hasar</th>
                  <th>Servis</th>
                  <th>KM Aşım</th>
                  <th>UTTS</th>
                  <th>Taşıt Tan.</th>
                  <th>Toplam</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredCostData.length === 0">
                  <td colspan="12" style="text-align: center; padding: 24px; color: #64748b;">Kayıtlı rapor verisi bulunamadı.</td>
                </tr>
                <tr v-for="row in filteredCostData" :key="row.plate">
                  <td>{{ row.user }}</td>
                  <td><strong style="color: #0f172a;">{{ row.plate }}</strong></td>
                  <td>₺{{ row.kira.toLocaleString() }}</td>
                  <td>₺{{ row.hgs.toLocaleString() }}</td>
                  <td>₺{{ row.yakit.toLocaleString() }}</td>
                  <td><span :style="{ color: row.lastik > 0 ? '#d97706' : '#94a3b8' }">₺{{ row.lastik.toLocaleString() }}</span></td>
                  <td><span :style="{ color: row.hasar > 0 ? '#dc2626' : '#94a3b8' }">₺{{ row.hasar.toLocaleString() }}</span></td>
                  <td><span :style="{ color: row.servis > 0 ? '#2563eb' : '#94a3b8' }">₺{{ row.servis.toLocaleString() }}</span></td>
                  <td>₺{{ row.kmAsim.toLocaleString() }}</td>
                  <td>₺{{ row.utts.toLocaleString() }}</td>
                  <td>₺{{ row.tasitTanima.toLocaleString() }}</td>
                  <td><strong style="color: #0f172a;">₺{{ row.toplam.toLocaleString() }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Stat Cards -->
        <div class="grid-4" style="gap: 14px; margin-bottom: 14px;">
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">₺{{ costTotals.kira.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Kira</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">₺{{ costTotals.hgs.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">HGS</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">₺{{ costTotals.yakit.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Yakıt</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #fefce8; border: 1px solid #fef08a;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #d97706;">₺{{ costTotals.lastik.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #b45309; margin-top: 4px;">Lastik</div>
          </div>
        </div>

        <div class="grid-4" style="gap: 14px; margin-bottom: 20px;">
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #fef2f2; border: 1px solid #fecaca;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #dc2626;">₺{{ costTotals.hasar.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #b91c1c; margin-top: 4px;">Hasar</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #eff6ff; border: 1px solid #bfdbfe;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #2563eb;">₺{{ costTotals.servis.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #1d4ed8; margin-top: 4px;">Servis</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">₺{{ costTotals.kmAsim.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">KM Aşım</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">₺{{ costTotals.utts.toLocaleString() }}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">UTTS</div>
          </div>
        </div>

        <!-- Highlight Total Card -->
        <div style="background: #f0fdf4; border: 2px solid #bbf7d0; border-radius: 16px; padding: 24px; text-align: center;">
          <div style="font-size: 2.2rem; font-weight: 900; color: #16a34a;">₺{{ costTotals.toplam.toLocaleString() }}</div>
          <div style="font-size: 0.95rem; font-weight: 700; color: #15803d; margin-top: 4px;">Genel Toplam Maliyet</div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 2. LOKASYON RAPORU                                             -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'location'" class="fade-in-up">
        <div v-if="filteredLocationData.length === 0" class="glass-panel text-center" style="padding: 30px; color: #64748b; background: #ffffff;">
          Kayıtlı lokasyon verisi bulunamadı.
        </div>
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;" v-for="loc in filteredLocationData" :key="loc.plate">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9;">
            <div style="width: 36px; height: 36px; border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">🚘</div>
            <div>
              <strong style="font-size: 1.1rem; color: #0f172a;">{{ loc.plate }}</strong>
              <div style="font-size: 0.85rem; color: #64748b;">{{ loc.user }}</div>
            </div>
          </div>

          <div class="grid-3" style="gap: 20px;">
            <!-- Semt Bazında -->
            <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #fafafa;">
              <h4 style="font-size: 0.95rem; color: #2563eb; margin-bottom: 16px;">🔵 Semt Bazında</h4>
              <div v-for="(item, idx) in loc.semt" :key="idx" style="margin-bottom: 14px; background: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9;">
                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #0f172a; font-size: 0.9rem;">
                  <span>{{ idx + 1 }}. {{ item.name }}</span>
                  <span style="color: #2563eb;">{{ item.duration }}</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                  Sabah: {{ item.sabah }} | Öğle: {{ item.ogle }} | Akşam: {{ item.aksam }}
                </div>
              </div>
            </div>

            <!-- İlçe Bazında -->
            <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #fafafa;">
              <h4 style="font-size: 0.95rem; color: #2563eb; margin-bottom: 16px;">🔵 İlçe Bazında</h4>
              <div v-for="(item, idx) in loc.ilce" :key="idx" style="margin-bottom: 14px; background: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9;">
                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #0f172a; font-size: 0.9rem;">
                  <span>{{ idx + 1 }}. {{ item.name }}</span>
                  <span style="color: #2563eb;">{{ item.duration }}</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                  Sabah: {{ item.sabah }} | Öğle: {{ item.ogle }} | Akşam: {{ item.aksam }}
                </div>
              </div>
            </div>

            <!-- İl Bazında -->
            <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #fafafa;">
              <h4 style="font-size: 0.95rem; color: #2563eb; margin-bottom: 16px;">🔵 İl Bazında</h4>
              <div v-for="(item, idx) in loc.il" :key="idx" style="margin-bottom: 14px; background: #eff6ff; padding: 12px; border-radius: 8px; border: 1px solid #bfdbfe;">
                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #1e40af; font-size: 0.9rem;">
                  <span>{{ idx + 1 }}. {{ item.name }}</span>
                  <span>{{ item.duration }}</span>
                </div>
                <div style="font-size: 0.75rem; color: #3b82f6; margin-top: 6px;">
                  Sabah: {{ item.sabah }} | Öğle: {{ item.ogle }} | Akşam: {{ item.aksam }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 3. KİLOMETRE RAPORU                                            -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'km'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç KM Raporu</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Plaka</th>
                  <th>Kullanıcı</th>
                  <th>Ocak</th>
                  <th>Şubat</th>
                  <th>Mart</th>
                  <th>Nisan</th>
                  <th>Mayıs</th>
                  <th>Haziran</th>
                  <th>Temmuz</th>
                  <th>Ağustos</th>
                  <th>Eylül</th>
                  <th>Ekim</th>
                  <th>Kasım</th>
                  <th>Aralık</th>
                  <th>Ort.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredKmData.length === 0">
                  <td colspan="15" style="text-align: center; padding: 24px; color: #64748b;">Kayıtlı KM verisi bulunamadı.</td>
                </tr>
                <tr v-for="row in filteredKmData" :key="row.plate">
                  <td><strong style="color: #0f172a;">{{ row.plate }}</strong></td>
                  <td>{{ row.user }}</td>
                  <td v-for="(val, idx) in row.months" :key="idx">{{ val.toLocaleString() }}</td>
                  <td><strong style="color: #2563eb;">{{ row.avg.toLocaleString() }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="grid-3" style="gap: 20px;">
          <div v-for="row in filteredKmData" :key="row.plate" class="glass-panel" style="padding: 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
            <h4 style="color: #2563eb; font-size: 1.1rem; margin-bottom: 12px;">{{ row.plate }}</h4>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 6px;">
              <span style="color: #64748b;">Mevcut KM:</span>
              <strong style="color: #0f172a;">{{ row.currentKm.toLocaleString() }} km</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 6px;">
              <span style="color: #64748b;">Toplam (12 ay):</span>
              <strong style="color: #0f172a;">{{ row.total12m.toLocaleString() }} km</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #cbd5e1;">
              <span style="color: #64748b;">Ortalama:</span>
              <strong style="color: #2563eb;">{{ row.avg.toLocaleString() }} km</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 4. ARAÇ KULLANIM SÜRESİ RAPORU                                 -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'usage'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Kullanım Süresi Raporu</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Plaka</th>
                  <th>Kullanıcı</th>
                  <th>Oca</th>
                  <th>Şub</th>
                  <th>Mar</th>
                  <th>Nis</th>
                  <th>May</th>
                  <th>Haz</th>
                  <th>Tem</th>
                  <th>Ağu</th>
                  <th>Eyl</th>
                  <th>Eki</th>
                  <th>Kas</th>
                  <th>Ara</th>
                  <th>Ort.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredUsageData.length === 0">
                  <td colspan="15" style="text-align: center; padding: 24px; color: #64748b;">Kayıtlı kullanım süresi bulunamadı.</td>
                </tr>
                <tr v-for="row in filteredUsageData" :key="row.plate">
                  <td><strong style="color: #0f172a;">{{ row.plate }}</strong></td>
                  <td>{{ row.user }}</td>
                  <td v-for="(val, idx) in row.months" :key="idx">{{ val }}</td>
                  <td><strong style="color: #10b981;">{{ row.avg }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="grid-3" style="gap: 20px;">
          <div v-for="row in filteredUsageData" :key="row.plate" class="glass-panel" style="padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 14px;">
            <h4 style="color: #16a34a; font-size: 1.1rem; margin-bottom: 12px;">{{ row.plate }}</h4>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 6px;">
              <span style="color: #475569;">Toplam Süre:</span>
              <strong style="color: #0f172a;">{{ row.totalDuration }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 6px;">
              <span style="color: #475569;">Ortalama Günlük:</span>
              <strong style="color: #16a34a;">{{ row.avg }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #a7f3d0;">
              <span style="color: #475569;">Aylık Ortalama:</span>
              <strong style="color: #15803d;">{{ row.monthlyAvg }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 5. ARAÇ SERVİS SÜRESİ RAPORU                                    -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'service'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Araç Servis Süresi Raporu</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Plaka</th>
                  <th>Kullanıcı</th>
                  <th>Bakım Süresi</th>
                  <th>Lastik Değişim Süresi</th>
                  <th>Hasar Onarım Süresi</th>
                  <th>Mekanik Onarım Süresi</th>
                  <th>Toplam Serviste Geçen Süre</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredServiceDurationData.length === 0">
                  <td colspan="7" style="text-align: center; padding: 24px; color: #64748b;">Kayıtlı servis süresi verisi bulunamadı.</td>
                </tr>
                <tr v-for="row in filteredServiceDurationData" :key="row.plate">
                  <td><strong style="color: #0f172a;">{{ row.plate }}</strong></td>
                  <td>{{ row.user }}</td>
                  <td>{{ row.bakim }}</td>
                  <td>{{ row.lastik }}</td>
                  <td>{{ row.hasar }}</td>
                  <td>{{ row.mekanik }}</td>
                  <td><strong style="color: #dc2626;">{{ row.toplam }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="grid-3" style="gap: 20px;">
          <div class="glass-panel text-center" style="padding: 20px; background: #eff6ff; border: 1px solid #bfdbfe;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563eb;">0.0 Gün</div>
            <div style="font-size: 0.85rem; color: #1d4ed8; margin-top: 4px;">Ortalama Serviste Kalma Süresi</div>
          </div>

          <div class="glass-panel text-center" style="padding: 20px; background: #fefce8; border: 1px solid #fef08a;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #d97706;">0 Araç</div>
            <div style="font-size: 0.85rem; color: #b45309; margin-top: 4px;">Şu An Serviste Bekleyen</div>
          </div>

          <div class="glass-panel text-center" style="padding: 20px; background: #f0fdf4; border: 1px solid #bbf7d0;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #16a34a;">0 Gün</div>
            <div style="font-size: 0.85rem; color: #15803d; margin-top: 4px;">Kullanılan İkame Araç Süresi</div>
          </div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 6. KULLANICI RAPORU                                            -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'user'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Kullanıcı Raporu</h2>

          <div class="custom-table-container">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Kullanıcı</th>
                  <th>Plaka</th>
                  <th>Kaza Yansıtılan</th>
                  <th>Servis Yansıtılan</th>
                  <th>Lastik Yansıtılan</th>
                  <th>Toplam</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="filteredUserData.length === 0">
                  <td colspan="6" style="text-align: center; padding: 24px; color: #64748b;">Kayıtlı kullanıcı rapor verisi bulunamadı.</td>
                </tr>
                <tr v-for="row in filteredUserData" :key="row.plate">
                  <td>{{ row.user }}</td>
                  <td><strong style="color: #0f172a;">{{ row.plate }}</strong></td>
                  <td><span :style="{ color: row.kaza > 0 ? '#dc2626' : '#94a3b8' }">₺{{ row.kaza.toLocaleString() }}</span></td>
                  <td><span :style="{ color: row.servis > 0 ? '#2563eb' : '#94a3b8' }">₺{{ row.servis.toLocaleString() }}</span></td>
                  <td><span :style="{ color: row.lastik > 0 ? '#d97706' : '#94a3b8' }">₺{{ row.lastik.toLocaleString() }}</span></td>
                  <td><strong style="color: #0f172a;">₺{{ row.toplam.toLocaleString() }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="grid-3" style="gap: 20px;">
          <div class="glass-panel text-center" style="padding: 24px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #dc2626;">₺{{ userTotals.kaza.toLocaleString() }}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #b91c1c; margin-top: 4px;">Toplam Kaza Yansıtılan</div>
          </div>

          <div class="glass-panel text-center" style="padding: 24px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #2563eb;">₺{{ userTotals.servis.toLocaleString() }}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #1d4ed8; margin-top: 4px;">Toplam Servis Yansıtılan</div>
          </div>

          <div class="glass-panel text-center" style="padding: 24px; background: #fefce8; border: 1px solid #fef08a; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #d97706;">₺{{ userTotals.lastik.toLocaleString() }}</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #b45309; margin-top: 4px;">Toplam Lastik Yansıtılan</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const activeTab = ref('cost')
const filterPlate = ref('')
const filterUser = ref('')
const startDate = ref('')
const endDate = ref('')

const costData = ref([])
const locationData = ref([])
const kmData = ref([])
const usageData = ref([])
const serviceDurationData = ref([])
const userData = ref([])

onMounted(async () => {
  try {
    const customerId = localStorage.getItem('customer_id')
    const userRole = localStorage.getItem('user_role')
    let url = '/api/vehicles'
    if (userRole === 'customer' && customerId) {
      url += `?customer_id=${customerId}`
    }
    const res = await fetch(url)
    if (res.ok) {
      const vehicles = await res.json()

      costData.value = vehicles.map(v => {
        const kira = v.monthly_rent || 0
        const hgs = 0
        const yakit = 0
        const lastik = 0
        const hasar = 0
        const servis = 0
        const kmAsim = 0
        const utts = 0
        const tasitTanima = 0
        const toplam = kira + hgs + yakit + lastik + hasar + servis + kmAsim + utts + tasitTanima
        return {
          user: v.assigned_user || v.driver_name || 'Atanmadı',
          plate: v.plate,
          kira, hgs, yakit, lastik, hasar, servis, kmAsim, utts, tasitTanima, toplam
        }
      })

      locationData.value = vehicles.map(v => ({
        plate: v.plate,
        user: v.assigned_user || v.driver_name || 'Atanmadı',
        semt: [{ name: v.city || 'Belirtilmedi', duration: '0s 0dk', sabah: '0s 0dk', ogle: '0s 0dk', aksam: '0s 0dk' }],
        ilce: [{ name: v.city || 'Belirtilmedi', duration: '0s 0dk', sabah: '0s 0dk', ogle: '0s 0dk', aksam: '0s 0dk' }],
        il: [{ name: v.city || 'Belirtilmedi', duration: '0s 0dk', sabah: '0s 0dk', ogle: '0s 0dk', aksam: '0s 0dk' }]
      }))

      kmData.value = vehicles.map(v => {
        const km = v.current_km || v.km || 0
        return {
          plate: v.plate,
          user: v.assigned_user || v.driver_name || 'Atanmadı',
          months: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, km],
          avg: Math.round(km / 12),
          currentKm: km,
          total12m: km
        }
      })

      usageData.value = vehicles.map(v => ({
        plate: v.plate,
        user: v.assigned_user || v.driver_name || 'Atanmadı',
        months: ['0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk', '0s 0dk'],
        avg: '0s 0dk',
        totalDuration: '0s 0dk',
        monthlyAvg: '0s 0dk'
      }))

      serviceDurationData.value = vehicles.map(v => ({
        plate: v.plate,
        user: v.assigned_user || v.driver_name || 'Atanmadı',
        bakim: '0.0 Gün',
        lastik: '0.0 Gün',
        hasar: '0.0 Gün',
        mekanik: '0.0 Gün',
        toplam: '0.0 Gün'
      }))

      userData.value = vehicles.map(v => ({
        user: v.assigned_user || v.driver_name || 'Atanmadı',
        plate: v.plate,
        kaza: 0,
        servis: 0,
        lastik: 0,
        toplam: 0
      }))
    }
  } catch (e) {
    console.error('Reports fetch error:', e)
  }
})

const costTotals = computed(() => {
  const init = { kira: 0, hgs: 0, yakit: 0, lastik: 0, hasar: 0, servis: 0, kmAsim: 0, utts: 0, tasitTanima: 0, toplam: 0 }
  return filteredCostData.value.reduce((acc, row) => {
    acc.kira += row.kira || 0
    acc.hgs += row.hgs || 0
    acc.yakit += row.yakit || 0
    acc.lastik += row.lastik || 0
    acc.hasar += row.hasar || 0
    acc.servis += row.servis || 0
    acc.kmAsim += row.kmAsim || 0
    acc.utts += row.utts || 0
    acc.tasitTanima += row.tasitTanima || 0
    acc.toplam += row.toplam || 0
    return acc
  }, init)
})

const userTotals = computed(() => {
  const init = { kaza: 0, servis: 0, lastik: 0, toplam: 0 }
  return filteredUserData.value.reduce((acc, row) => {
    acc.kaza += row.kaza || 0
    acc.servis += row.servis || 0
    acc.lastik += row.lastik || 0
    acc.toplam += row.toplam || 0
    return acc
  }, init)
})

const resetFilters = () => {
  filterPlate.value = ''
  filterUser.value = ''
  startDate.value = ''
  endDate.value = ''
}

const activeReportTitle = computed(() => {
  switch (activeTab.value) {
    case 'cost': return 'Araç Maliyet Raporu'
    case 'location': return 'Lokasyon Raporu'
    case 'km': return 'Kilometre Raporu'
    case 'usage': return 'Araç Kullanım Süresi'
    case 'service': return 'Araç Servis Süresi'
    case 'user': return 'Kullanıcı Raporu'
    default: return 'Raporlar'
  }
})

const filteredCostData = computed(() => {
  return costData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

const filteredLocationData = computed(() => {
  return locationData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

const filteredKmData = computed(() => {
  return kmData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

const filteredUsageData = computed(() => {
  return usageData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

const filteredServiceDurationData = computed(() => {
  return serviceDurationData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

const filteredUserData = computed(() => {
  return userData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// Real Excel Download (.csv UTF-8 BOM export)
const downloadExcel = () => {
  let headers = []
  let rows = []

  if (activeTab.value === 'cost') {
    headers = ['Kullanıcı', 'Plaka', 'Kira (TL)', 'HGS (TL)', 'Yakıt (TL)', 'Lastik (TL)', 'Hasar (TL)', 'Servis (TL)', 'KM Aşım (TL)', 'UTTS (TL)', 'Taşıt Tanıma (TL)', 'Toplam (TL)']
    rows = filteredCostData.value.map(r => [r.user, r.plate, r.kira, r.hgs, r.yakit, r.lastik, r.hasar, r.servis, r.kmAsim, r.utts, r.tasitTanima, r.toplam])
  } else if (activeTab.value === 'location') {
    headers = ['Plaka', 'Kullanıcı', 'En Çok Bulunduğu Semt', 'Süre', 'İl']
    rows = filteredLocationData.value.map(r => [r.plate, r.user, r.semt[0]?.name, r.semt[0]?.duration, r.il[0]?.name])
  } else if (activeTab.value === 'km') {
    headers = ['Plaka', 'Kullanıcı', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık', 'Aylık Ortalama']
    rows = filteredKmData.value.map(r => [r.plate, r.user, ...r.months, r.avg])
  } else if (activeTab.value === 'usage') {
    headers = ['Plaka', 'Kullanıcı', 'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara', 'Ortalama']
    rows = filteredUsageData.value.map(r => [r.plate, r.user, ...r.months, r.avg])
  } else if (activeTab.value === 'service') {
    headers = ['Plaka', 'Kullanıcı', 'Bakım Süresi', 'Lastik Süresi', 'Hasar Süresi', 'Mekanik Süre', 'Toplam Servis Süresi']
    rows = filteredServiceDurationData.value.map(r => [r.plate, r.user, r.bakim, r.lastik, r.hasar, r.mekanik, r.toplam])
  } else if (activeTab.value === 'user') {
    headers = ['Kullanıcı', 'Plaka', 'Kaza Yansıtılan (TL)', 'Servis Yansıtılan (TL)', 'Lastik Yansıtılan (TL)', 'Toplam (TL)']
    rows = filteredUserData.value.map(r => [r.user, r.plate, r.kaza, r.servis, r.lastik, r.toplam])
  }

  let csvContent = '\uFEFF' + headers.join(';') + '\n'
  rows.forEach(row => {
    csvContent += row.map(val => `"${val}"`).join(';') + '\n'
  })

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const fileName = `FleetRent_${activeReportTitle.value.replace(/ /g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`
  link.href = URL.createObjectURL(blob)
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Real PDF Print/Download
const downloadPDF = () => {
  const printWindow = window.open('', '_blank')
  const title = activeReportTitle.value
  const dateRangeStr = startDate.value && endDate.value ? `${startDate.value} - ${endDate.value}` : 'Tüm Dönemler'

  let tableHtml = ''
  
  if (activeTab.value === 'cost') {
    tableHtml = `
      <table>
        <thead>
          <tr>
            <th>Kullanıcı</th><th>Plaka</th><th>Kira</th><th>HGS</th><th>Yakıt</th><th>Lastik</th><th>Hasar</th><th>Servis</th><th>KM Aşım</th><th>UTTS</th><th>Taşıt Tan.</th><th>Toplam</th>
          </tr>
        </thead>
        <tbody>
          ${filteredCostData.value.map(r => `
            <tr>
              <td>${r.user}</td><td><b>${r.plate}</b></td><td>₺${r.kira.toLocaleString()}</td><td>₺${r.hgs.toLocaleString()}</td><td>₺${r.yakit.toLocaleString()}</td><td>₺${r.lastik.toLocaleString()}</td><td>₺${r.hasar.toLocaleString()}</td><td>₺${r.servis.toLocaleString()}</td><td>₺${r.kmAsim.toLocaleString()}</td><td>₺${r.utts.toLocaleString()}</td><td>₺${r.tasitTanima.toLocaleString()}</td><td><b>₺${r.toplam.toLocaleString()}</b></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      <div style="margin-top: 20px; font-size: 18px; font-weight: bold; color: #16a34a; text-align: right;">
        Genel Toplam Maliyet: ₺${costTotals.value.toplam.toLocaleString()}
      </div>
    `
  } else if (activeTab.value === 'km') {
    tableHtml = `
      <table>
        <thead>
          <tr><th>Plaka</th><th>Kullanıcı</th><th>Ocak</th><th>Şubat</th><th>Mart</th><th>Nisan</th><th>Mayıs</th><th>Haziran</th><th>Temmuz</th><th>Ağustos</th><th>Eylül</th><th>Ekim</th><th>Kasım</th><th>Aralık</th><th>Ort.</th></tr>
        </thead>
        <tbody>
          ${filteredKmData.value.map(r => `
            <tr><td><b>${r.plate}</b></td><td>${r.user}</td>${r.months.map(m => `<td>${m.toLocaleString()}</td>`).join('')}<td><b>${r.avg.toLocaleString()}</b></td></tr>
          `).join('')}
        </tbody>
      </table>
    `
  } else if (activeTab.value === 'usage') {
    tableHtml = `
      <table>
        <thead>
          <tr><th>Plaka</th><th>Kullanıcı</th><th>Oca</th><th>Şub</th><th>Mar</th><th>Nis</th><th>May</th><th>Haz</th><th>Tem</th><th>Ağu</th><th>Eyl</th><th>Eki</th><th>Kas</th><th>Ara</th><th>Ort.</th></tr>
        </thead>
        <tbody>
          ${filteredUsageData.value.map(r => `
            <tr><td><b>${r.plate}</b></td><td>${r.user}</td>${r.months.map(m => `<td>${m}</td>`).join('')}<td><b>${r.avg}</b></td></tr>
          `).join('')}
        </tbody>
      </table>
    `
  } else if (activeTab.value === 'service') {
    tableHtml = `
      <table>
        <thead>
          <tr><th>Plaka</th><th>Kullanıcı</th><th>Bakım Süresi</th><th>Lastik Süresi</th><th>Hasar Süresi</th><th>Mekanik Süre</th><th>Toplam Servis</th></tr>
        </thead>
        <tbody>
          ${filteredServiceDurationData.value.map(r => `
            <tr><td><b>${r.plate}</b></td><td>${r.user}</td><td>${r.bakim}</td><td>${r.lastik}</td><td>${r.hasar}</td><td>${r.mekanik}</td><td><b>${r.toplam}</b></td></tr>
          `).join('')}
        </tbody>
      </table>
    `
  } else if (activeTab.value === 'user') {
    tableHtml = `
      <table>
        <thead>
          <tr><th>Kullanıcı</th><th>Plaka</th><th>Kaza Yansıtılan</th><th>Servis Yansıtılan</th><th>Lastik Yansıtılan</th><th>Toplam</th></tr>
        </thead>
        <tbody>
          ${filteredUserData.value.map(r => `
            <tr><td>${r.user}</td><td><b>${r.plate}</b></td><td>₺${r.kaza.toLocaleString()}</td><td>₺${r.servis.toLocaleString()}</td><td>₺${r.lastik.toLocaleString()}</td><td><b>₺${r.toplam.toLocaleString()}</b></td></tr>
          `).join('')}
        </tbody>
      </table>
    `
  } else {
    tableHtml = `
      <table>
        <thead>
          <tr><th>Plaka</th><th>Kullanıcı</th><th>En Çok Bulunduğu Semt</th><th>Süre</th><th>İl</th></tr>
        </thead>
        <tbody>
          ${filteredLocationData.value.map(r => `
            <tr><td><b>${r.plate}</b></td><td>${r.user}</td><td>${r.semt[0]?.name}</td><td>${r.semt[0]?.duration}</td><td>${r.il[0]?.name}</td></tr>
          `).join('')}
        </tbody>
      </table>
    `
  }

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>FleetRent - ${title}</title>
        <style>
          body { font-family: sans-serif; padding: 25px; color: #0f172a; }
          .header { display: flex; justify-content: space-between; border-bottom: 2px solid #2563eb; padding-bottom: 15px; margin-bottom: 20px; }
          h1 { font-size: 20px; margin: 0; color: #2563eb; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }
          th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
          th { background: #f1f5f9; color: #0f172a; }
          tr:nth-child(even) { background: #f8fafc; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1>FleetRent Filo Yönetim Raporu</h1>
            <h3 style="margin: 5px 0 0; color: #334155;">${title}</h3>
          </div>
          <div style="text-align: right; font-size: 12px; color: #64748b;">
            Oluşturulma Tarihi: ${new Date().toLocaleDateString('tr-TR')}<br>
            Seçili Filtre: Plaka: "${filterPlate.value || 'Tüm'}", Kullanıcı: "${filterUser.value || 'Tüm'}"<br>
            Dönem: ${dateRangeStr}
          </div>
        </div>
        ${tableHtml}
      </body>
    </html>
  `)

  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.print()
  }, 500)
}
</script>
