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
      <!-- 1. ARAÇ MALİYET RAPORU (Görsel 1)                               -->
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

        <!-- Summary Stat Cards matching screenshot 1 -->
        <div class="grid-4" style="gap: 14px; margin-bottom: 14px;">
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">55.000 ₺</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Kira</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">1.450 ₺</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">HGS</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">10.100 ₺</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Yakıt</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #fefce8; border: 1px solid #fef08a;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #d97706;">3.400 ₺</div>
            <div style="font-size: 0.8rem; color: #b45309; margin-top: 4px;">Lastik</div>
          </div>
        </div>

        <div class="grid-4" style="gap: 14px; margin-bottom: 20px;">
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #fef2f2; border: 1px solid #fecaca;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #dc2626;">9.800 ₺</div>
            <div style="font-size: 0.8rem; color: #b91c1c; margin-top: 4px;">Hasar</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #eff6ff; border: 1px solid #bfdbfe;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #2563eb;">1.200 ₺</div>
            <div style="font-size: 0.8rem; color: #1d4ed8; margin-top: 4px;">Servis</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">500 ₺</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">KM Aşım</div>
          </div>
          <div class="glass-panel stat-card text-center" style="padding: 16px; background: #ffffff;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">450 ₺</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">UTTS</div>
          </div>
        </div>

        <!-- Highlight Total Card -->
        <div style="background: #f0fdf4; border: 2px solid #bbf7d0; border-radius: 16px; padding: 24px; text-align: center;">
          <div style="font-size: 2.2rem; font-weight: 900; color: #16a34a;">82.500 TL</div>
          <div style="font-size: 0.95rem; font-weight: 700; color: #15803d; margin-top: 4px;">Genel Toplam Maliyet</div>
        </div>
      </div>

      <!-- ============================================================== -->
      <!-- 2. LOKASYON RAPORU (Görsel 2)                                  -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'location'" class="fade-in-up">
        <!-- Location Cards list matching screenshot 2 -->
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
      <!-- 3. KİLOMETRE RAPORU (Görsel 3)                                  -->
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

        <!-- Cards per vehicle matching screenshot 3 -->
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
      <!-- 4. ARAÇ KULLANIM SÜRESİ RAPORU (Görsel 4)                       -->
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

        <!-- Green Cards per vehicle matching screenshot 4 -->
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
      <!-- 5. ARAÇ SERVİS SÜRESİ RAPORU (Özel Kırılım)                    -->
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
            <div style="font-size: 1.8rem; font-weight: 800; color: #2563eb;">2.4 Gün</div>
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
      <!-- 6. KULLANICI RAPORU (Görsel 5)                                 -->
      <!-- ============================================================== -->
      <div v-if="activeTab === 'user'" class="fade-in-up">
        <div class="glass-panel" style="padding: 28px; background: #ffffff; margin-bottom: 24px;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 20px;">Kullanıcı Raporu</h2>

          <!-- Table matching screenshot 5 -->
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

        <!-- Summary Cards matching screenshot 5 -->
        <div class="grid-3" style="gap: 20px;">
          <div class="glass-panel text-center" style="padding: 24px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #dc2626;">9.800 TL</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #b91c1c; margin-top: 4px;">Toplam Kaza Yansıtılan</div>
          </div>

          <div class="glass-panel text-center" style="padding: 24px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #2563eb;">1.200 TL</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #1d4ed8; margin-top: 4px;">Toplam Servis Yansıtılan</div>
          </div>

          <div class="glass-panel text-center" style="padding: 24px; background: #fefce8; border: 1px solid #fef08a; border-radius: 16px;">
            <div style="font-size: 2rem; font-weight: 900; color: #d97706;">3.400 TL</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #b45309; margin-top: 4px;">Toplam Lastik Yansıtılan</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const activeTab = ref('cost')
const filterPlate = ref('')
const filterUser = ref('')
const startDate = ref('')
const endDate = ref('')

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

// Cost Data from Screenshot 1
const costData = ref([
  { user: 'Ahmet Türkoğlu', plate: '34 FR 001', kira: 15000, hgs: 450, yakit: 3200, lastik: 0, hasar: 0, servis: 1200, kmAsim: 0, utts: 150, tasitTanima: 200, toplam: 20200 },
  { user: 'Mehmet Yılmaz', plate: '34 FR 002', kira: 18000, hgs: 320, yakit: 2800, lastik: 3400, hasar: 0, servis: 0, kmAsim: 500, utts: 150, tasitTanima: 200, toplam: 25370 },
  { user: 'Ali Demir', plate: '06 FR 003', kira: 22000, hgs: 680, yakit: 4100, lastik: 0, hasar: 9800, servis: 0, kmAsim: 0, utts: 150, tasitTanima: 200, toplam: 36930 }
])

const filteredCostData = computed(() => {
  return costData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// Location Data from Screenshot 2
const locationData = ref([
  {
    plate: '34 FR 001',
    user: 'Ahmet Türkoğlu',
    semt: [
      { name: 'Kadıköy', duration: '6s 30dk', sabah: '2s 0dk', ogle: '3s 0dk', aksam: '1s 30dk' },
      { name: 'Ümraniye', duration: '5s 0dk', sabah: '1s 0dk', ogle: '1s 30dk', aksam: '2s 30dk' },
      { name: 'Ataşehir', duration: '3s 0dk', sabah: '45dk', ogle: '1s 0dk', aksam: '1s 15dk' }
    ],
    ilce: [
      { name: 'Kadıköy', duration: '6s 30dk', sabah: '2s 0dk', ogle: '3s 0dk', aksam: '1s 30dk' },
      { name: 'Ümraniye', duration: '5s 0dk', sabah: '1s 0dk', ogle: '1s 30dk', aksam: '2s 30dk' },
      { name: 'Ataşehir', duration: '3s 0dk', sabah: '45dk', ogle: '1s 0dk', aksam: '1s 15dk' }
    ],
    il: [
      { name: 'İstanbul', duration: '14s 30dk', sabah: '3s 45dk', ogle: '5s 30dk', aksam: '5s 15dk' }
    ]
  }
])

const filteredLocationData = computed(() => {
  return locationData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// KM Data from Screenshot 3
const kmData = ref([
  { plate: '34 FR 001', user: 'Ahmet Türkoğlu', months: [3650, 3420, 3890, 4100, 3950, 3780, 4020, 3850, 4200, 3980, 3750, 4120], avg: 3893, currentKm: 45230, total12m: 46710 },
  { plate: '34 FR 002', user: 'Mehmet Yılmaz', months: [3280, 3150, 3520, 3680, 3450, 3320, 3590, 3410, 3750, 3580, 3290, 3650], avg: 3473, currentKm: 38900, total12m: 41670 },
  { plate: '06 FR 003', user: 'Ali Demir', months: [4520, 4280, 4650, 4890, 4720, 4580, 4810, 4650, 4920, 4780, 4450, 4830], avg: 4673, currentKm: 52150, total12m: 56080 }
])

const filteredKmData = computed(() => {
  return kmData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// Usage Duration Data from Screenshot 4
const usageData = ref([
  { plate: '34 FR 001', user: 'Ahmet Türkoğlu', months: ['120s 0dk', '113s 20dk', '125s 0dk', '130s 0dk', '126s 40dk', '120s 0dk', '128s 20dk', '123s 20dk', '133s 20dk', '126s 40dk', '118s 20dk', '130s 0dk'], avg: '124s 35dk', totalDuration: '1495s 0dk', monthlyAvg: '49s 50dk' },
  { plate: '34 FR 002', user: 'Mehmet Yılmaz', months: ['106s 40dk', '103s 20dk', '113s 20dk', '118s 20dk', '111s 40dk', '108s 20dk', '115s 0dk', '110s 0dk', '120s 0dk', '115s 0dk', '105s 0dk', '116s 40dk'], avg: '111s 57dk', totalDuration: '1343s 20dk', monthlyAvg: '44s 47dk' },
  { plate: '06 FR 003', user: 'Ali Demir', months: ['160s 0dk', '151s 40dk', '165s 0dk', '173s 20dk', '166s 40dk', '161s 40dk', '170s 0dk', '163s 20dk', '175s 0dk', '168s 20dk', '156s 40dk', '171s 40dk'], avg: '165s 17dk', totalDuration: '1983s 20dk', monthlyAvg: '66s 7dk' }
])

const filteredUsageData = computed(() => {
  return usageData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// Service Duration Data
const serviceDurationData = ref([
  { plate: '34 FR 001', user: 'Ahmet Türkoğlu', bakim: '1.0 Gün', lastik: '0.4 Gün', hasar: '0.0 Gün', mekanik: '1.0 Gün', toplam: '2.4 Gün' },
  { plate: '34 FR 002', user: 'Mehmet Yılmaz', bakim: '0.5 Gün', lastik: '1.0 Gün', hasar: '0.0 Gün', mekanik: '0.0 Gün', toplam: '1.5 Gün' },
  { plate: '06 FR 003', user: 'Ali Demir', bakim: '1.2 Gün', lastik: '0.0 Gün', hasar: '4.5 Gün', mekanik: '0.0 Gün', toplam: '5.7 Gün' }
])

const filteredServiceDurationData = computed(() => {
  return serviceDurationData.value.filter(row => {
    const matchPlate = !filterPlate.value || row.plate.toLowerCase().includes(filterPlate.value.toLowerCase())
    const matchUser = !filterUser.value || row.user.toLowerCase().includes(filterUser.value.toLowerCase())
    return matchPlate && matchUser
  })
})

// User Cost Data from Screenshot 5
const userData = ref([
  { user: 'Ahmet Türkoğlu', plate: '34 FR 001', kaza: 0, servis: 1200, lastik: 0, toplam: 1200 },
  { user: 'Mehmet Yılmaz', plate: '34 FR 002', kaza: 0, servis: 0, lastik: 3400, toplam: 3400 },
  { user: 'Ali Demir', plate: '06 FR 003', kaza: 9800, servis: 0, lastik: 0, toplam: 9800 }
])

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
        Genel Toplam Maliyet: 82.500 TL
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
