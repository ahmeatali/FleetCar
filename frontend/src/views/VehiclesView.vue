<template>
  <div class="app-bg-glow"></div>
  <div class="portal-layout">
    <Sidebar :supplier="isSupplier" />

    <main class="portal-main fade-in-up fleet-page">
      <header class="fleet-topbar">
        <UiField class="fleet-search"
          ><span>⌕</span
          ><input
            v-model="filters.search"
            type="search"
            placeholder="Araç plakası, marka, model veya şasi no ara..."
        /></UiField>
        <div class="customer-header-actions">
          <NotificationBell v-if="!isSupplier" />
          <div class="fleet-account">
            <span class="fleet-avatar">{{ userInitials }}</span
            ><span
              ><strong>{{ customerName }}</strong
              ><small>{{ isSupplier ? 'Tedarikçi' : 'Filo yöneticisi' }}</small></span
            >
          </div>
        </div>
      </header>

      <section class="fleet-heading">
        <div>
          <span class="fleet-eyebrow">FİLO YÖNETİMİ</span>
          <h1>Araçlar</h1>
          <p>
            {{
              isSupplier
                ? 'Araçlarınızı filonuza ekleyin, müşterilerinize atayın ve aynı bilgiler üzerinden takip edin.'
                : 'Tüm araçlarınızı tek ekrandan yönetin. Filtreleyin, arayın ve detayları görüntüleyin.'
            }}
          </p>
        </div>
        <div class="fleet-heading-actions">
          <UiButton
            class="fleet-utility-button"
            @click="activeTab = activeTab === 'old' ? 'active' : 'old'"
            >{{ activeTab === 'old' ? 'Aktif Araçlar' : 'Eski Araçlar' }}</UiButton
          ><UiButton
            class="fleet-utility-button"
            @click="activeTab = activeTab === 'tracking' ? 'active' : 'tracking'"
            >⌖ Araç Takibi</UiButton
          >
        </div>
      </section>

      <section v-if="!isSupplier" class="fleet-stats" aria-label="Filo özeti">
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.status === '' }"
          @click="filters.status = ''"
          ><span class="fleet-stat-icon blue">🚘</span
          ><span
            ><small>Toplam Araç</small
            ><strong
              >{{ vehicles.length }}<em>{{ activeVehiclesCount }} aktif</em></strong
            ></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.status === 'Aktif' }"
          @click="filters.status = filters.status === 'Aktif' ? '' : 'Aktif'"
          ><span class="fleet-stat-icon green">✓</span
          ><span
            ><small>Aktif</small><strong>{{ statusCount('Aktif') }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.status === 'Serviste' }"
          @click="filters.status = filters.status === 'Serviste' ? '' : 'Serviste'"
          ><span class="fleet-stat-icon amber">⚒</span
          ><span
            ><small>Serviste</small><strong>{{ statusCount('Serviste') }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.status === 'Kaza' }"
          @click="filters.status = filters.status === 'Kaza' ? '' : 'Kaza'"
          ><span class="fleet-stat-icon red">!</span
          ><span
            ><small>Hasar / Kaza</small><strong>{{ incidentCount }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.status === 'İkame Araç Bekliyor' }"
          @click="
            filters.status = filters.status === 'İkame Araç Bekliyor' ? '' : 'İkame Araç Bekliyor'
          "
          ><span class="fleet-stat-icon navy">◷</span
          ><span
            ><small>İkame Bekliyor</small
            ><strong>{{ statusCount('İkame Araç Bekliyor') }}</strong></span
          ></UiButton
        >
      </section>

      <section v-else class="fleet-stats supplier-stats" aria-label="Tedarikçi filo özeti">
        <UiButton class="fleet-stat" @click="filters.assignment = ''"
          ><span class="fleet-stat-icon blue">🚘</span
          ><span
            ><small>Toplam Araç</small><strong>{{ vehicles.length }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.assignment === 'available' }"
          @click="filters.assignment = filters.assignment === 'available' ? '' : 'available'"
          ><span class="fleet-stat-icon green">✓</span
          ><span
            ><small>Atanmamış Araç</small
            ><strong>{{
              vehicles.filter((v) => v.is_active && !v.customer_id).length
            }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          :class="{ 'fleet-stat-selected': filters.assignment === 'assigned' }"
          @click="filters.assignment = filters.assignment === 'assigned' ? '' : 'assigned'"
          ><span class="fleet-stat-icon navy">▣</span
          ><span
            ><small>Müşteriye Atanan</small
            ><strong>{{
              vehicles.filter((v) => v.is_active && v.customer_id).length
            }}</strong></span
          ></UiButton
        >
        <UiButton
          class="fleet-stat"
          @click="filters.status = filters.status === 'Serviste' ? '' : 'Serviste'"
          ><span class="fleet-stat-icon amber">⚒</span
          ><span
            ><small>Serviste</small><strong>{{ statusCount('Serviste') }}</strong></span
          ></UiButton
        >
      </section>
      <UiAlert v-if="loadError" class="fleet-feedback error" as="p" tone="error"
        >{{ loadError }} <UiButton @click="fetchVehicles">Tekrar Dene</UiButton></UiAlert
      >
      <UiAlert v-if="feedback" class="fleet-feedback" as="p" tone="info">{{ feedback }}</UiAlert>
      <section class="fleet-workspace">
        <div class="fleet-list-column">
          <div class="fleet-list-toolbar">
            <form class="fleet-filters" @submit.prevent="page = 1">
              <UiField v-if="isSupplier"
                ><span>Müşteri Ataması</span
                ><select v-model="filters.assignment">
                  <option value="">Tümü</option>
                  <option value="available">Atanmamış</option>
                  <option value="assigned">Müşteriye atanmış</option>
                  <option
                    v-for="customer in customers"
                    :key="customer.id"
                    :value="String(customer.id)"
                  >
                    {{ customer.company_name }}
                  </option>
                </select></UiField
              >
              <UiField
                ><span>Durum</span
                ><select v-model="filters.status">
                  <option value="">Tümü</option>
                  <option v-for="status in availableStatuses" :key="status" :value="status">
                    {{ status }}
                  </option>
                  <option value="Kaza">Hasar / Kaza</option>
                </select></UiField
              >
              <UiField
                ><span>Marka / Model</span
                ><select v-model="filters.vehicle_type">
                  <option value="">Tümü</option>
                  <option v-for="name in availableModels" :key="name" :value="name">
                    {{ name }}
                  </option>
                </select></UiField
              >
              <UiField
                ><span>Plaka</span><input v-model="filters.plate" placeholder="Plaka girin..."
              /></UiField>
              <UiField
                ><span>Sözleşme Dönemi</span
                ><select v-model="filters.contract">
                  <option value="">Tümü</option>
                  <option value="current">Aktif sözleşmeler</option>
                  <option value="expired">Süresi dolanlar</option>
                </select></UiField
              >
              <UiButton type="submit" class="fleet-filter-button">⌕ Filtrele</UiButton>
            </form>
            <div class="fleet-list-actions">
              <UiButton class="fleet-utility-button" @click="exportVehicles">⇩ Dışa Aktar</UiButton>
              <UiButton class="btn btn-primary" @click="showAddModal = true">＋ Yeni Araç</UiButton>
            </div>
          </div>

          <div class="fleet-table-card">
            <div class="fleet-table-scroll">
              <table class="fleet-table">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        :checked="allVisibleSelected"
                        aria-label="Görünen araçları seç"
                        @change="toggleVisibleSelection"
                      />
                    </th>
                    <th>#</th>
                    <th>Plaka</th>
                    <th>Marka / Model</th>
                    <th>Renk</th>
                    <th>Yıl</th>
                    <th>Şasi No (VIN)</th>
                    <th>Motor No</th>
                    <th>Durum</th>
                    <th>Kira Başlangıç</th>
                    <th>Kira Bitiş</th>
                    <th>Km</th>
                    <th v-if="isSupplier">Müşteri</th>
                    <th>İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading">
                    <td :colspan="isSupplier ? 14 : 13" class="fleet-empty">Araçlar yükleniyor…</td>
                  </tr>
                  <tr v-else-if="!paginatedVehicles.length">
                    <td :colspan="isSupplier ? 14 : 13" class="fleet-empty">
                      Filtrelere uygun araç bulunamadı.
                    </td>
                  </tr>
                  <tr
                    v-for="(vehicle, index) in paginatedVehicles"
                    v-else
                    :key="vehicle.id"
                    @click="goToVehicleDetails(vehicle)"
                  >
                    <td data-label="Seç" @click.stop>
                      <input
                        v-model="selectedVehicleIds"
                        type="checkbox"
                        :value="vehicle.id"
                        :aria-label="`${vehicle.plate} aracını seç`"
                      />
                    </td>
                    <td data-label="Sıra" class="fleet-index">
                      {{ (page - 1) * pageSize + index + 1 }}
                    </td>
                    <td data-label="Plaka">
                      <router-link
                        :to="vehicleDetailsLink(vehicle)"
                        class="plate-badge fleet-plate"
                        @click.stop
                        >{{ vehicle.plate }}</router-link
                      >
                    </td>
                    <td data-label="Araç">
                      <div class="fleet-vehicle-cell">
                        <span class="fleet-car-thumb" aria-hidden="true">🚘</span
                        ><span
                          ><strong>{{ vehicle.brand }} {{ vehicle.model }}</strong
                          ><small v-if="vehicle.version">{{ vehicle.version }}</small></span
                        >
                      </div>
                    </td>
                    <td data-label="Renk">
                      <span class="fleet-color"
                        ><i
                          :style="{ backgroundColor: vehicleColor(vehicle.color) }"
                          aria-hidden="true"
                        ></i
                        >{{ vehicle.color || 'Belirtilmedi' }}</span
                      >
                    </td>
                    <td data-label="Yıl">{{ vehicle.year || '—' }}</td>
                    <td data-label="Şasi No" class="fleet-vin">{{ vehicle.chassis_no || '—' }}</td>
                    <td data-label="Motor No" class="fleet-vin">{{ vehicle.engine_no || '—' }}</td>
                    <td data-label="Durum">
                      <span
                        class="badge fleet-status"
                        :class="getVehicleBadgeClass(vehicle.status)"
                        >{{ vehicle.is_active ? vehicle.status : 'Filodan çıkarıldı' }}</span
                      >
                    </td>
                    <td data-label="Kira Başlangıcı">
                      {{
                        vehicle.contract_start_date ? formatDate(vehicle.contract_start_date) : '—'
                      }}
                    </td>
                    <td data-label="Kira Bitişi">
                      {{ vehicle.contract_end_date ? formatDate(vehicle.contract_end_date) : '—' }}
                    </td>
                    <td data-label="Kilometre">
                      {{ Number(vehicle.mileage || 0).toLocaleString('tr-TR') }}
                    </td>
                    <td v-if="isSupplier" data-label="Müşteri">
                      <span :class="{ 'supplier-unassigned': !vehicle.customer_id }">{{
                        vehicle.customer_name || 'Atanmamış'
                      }}</span>
                    </td>
                    <td data-label="İşlem">
                      <UiButton
                        v-if="isSupplier && vehicle.is_active"
                        class="fleet-utility-button"
                        @click.stop="openAssignment(vehicle)"
                        >{{ vehicle.customer_id ? 'Atamayı Yönet' : 'Müşteriye Ata' }}</UiButton
                      ><UiButton
                        class="fleet-row-menu"
                        :aria-label="`${vehicle.plate} detay sayfasını aç`"
                        @click.stop="goToVehicleDetails(vehicle)"
                        ><span class="desktop-action-label">•••</span
                        ><span class="mobile-action-label">Araç Detayları</span></UiButton
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <footer class="fleet-table-footer">
              <span
                >Toplam {{ filteredVehicles.length }} araçtan {{ pageStart }}–{{
                  pageEnd
                }}
                görüntüleniyor<span v-if="selectedVehicleIds.length">
                  · {{ selectedVehicleIds.length }} seçildi</span
                ></span
              >
              <div class="fleet-pagination">
                <UiButton :disabled="page <= 1" @click="page--">‹</UiButton
                ><UiButton v-if="page > 3" @click="page = 1">1</UiButton
                ><span v-if="page > 4">…</span
                ><UiButton
                  v-for="number in visiblePages"
                  :key="number"
                  :class="{ current: page === number }"
                  @click="page = number"
                  >{{ number }}</UiButton
                ><span v-if="page < totalPages - 3">…</span
                ><UiButton
                  v-if="totalPages > 5 && page < totalPages - 2"
                  @click="page = totalPages"
                  >{{ totalPages }}</UiButton
                ><UiButton :disabled="page >= totalPages" @click="page++">›</UiButton>
              </div>
            </footer>
          </div>

          <div v-if="activeTab === 'tracking'" class="fleet-map-card">
            <div>
              <strong>Araç takibi</strong><UiButton @click="activeTab = 'active'">Kapat</UiButton>
            </div>
            <iframe
              title="İstanbul araç takip haritası"
              src="https://www.openstreetmap.org/export/embed.html?bbox=28.8000%2C40.9000%2C29.2500%2C41.1500&amp;layer=mapnik&amp;marker=41.0082%2C28.9784"
              loading="lazy"
            ></iframe>
            <p>Canlı konum için GPS cihazı ve entegrasyon ayarlarının etkin olması gerekir.</p>
          </div>
        </div>
      </section>
    </main>
  </div>

  <UiModal
    v-if="assignmentVehicle"
    class="modal-overlay"
    @close="!assigning && (assignmentVehicle = null)"
  >
    <section
      class="glass-panel modal-content supplier-assignment"
      role="dialog"
      aria-modal="true"
      aria-labelledby="assignment-title"
      @keydown.esc="!assigning && (assignmentVehicle = null)"
    >
      <h2 id="assignment-title">Müşteri Ataması</h2>
      <p>
        <strong>{{ assignmentVehicle.plate }}</strong> · {{ assignmentVehicle.brand }}
        {{ assignmentVehicle.model }}
      </p>
      <p>
        Mevcut müşteri: <strong>{{ assignmentVehicle.customer_name || 'Atanmamış' }}</strong>
      </p>
      <form @submit.prevent="saveAssignment">
        <UiField class="form-label" for="assignment-customer">Müşteri</UiField>
        <select
          id="assignment-customer"
          v-model="assignmentCustomerId"
          class="form-select"
          :disabled="assigning"
        >
          <option value="">Atama yok / Atamayı kaldır</option>
          <option v-for="customer in customers" :key="customer.id" :value="String(customer.id)">
            {{ customer.company_name }}
          </option>
        </select>
        <p class="assignment-note">
          Atanan araç, tüm araç ve sözleşme bilgileriyle müşterinin araç listesinde görünür. Atama
          kaldırıldığında müşterinin listesinden çıkar.
        </p>
        <UiAlert v-if="assignmentError" class="fleet-feedback error" as="p" tone="error">{{
          assignmentError
        }}</UiAlert>
        <footer>
          <UiButton
            type="button"
            class="btn btn-secondary"
            :disabled="assigning"
            @click="assignmentVehicle = null"
            >Vazgeç</UiButton
          ><UiButton
            class="btn btn-primary"
            :disabled="
              assigning || assignmentCustomerId === String(assignmentVehicle.customer_id || '')
            "
            >{{ assigning ? 'Kaydediliyor…' : 'Atamayı Kaydet' }}</UiButton
          >
        </footer>
      </form>
    </section>
  </UiModal>
  <!-- Add Vehicle Modal -->
  <UiModal v-if="showAddModal" class="modal-overlay" @close="showAddModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 650px; padding: 30px">
      <h2 class="gradient-brand" style="margin-bottom: 20px">Yeni Araç Ekle</h2>

      <p v-if="isSupplier" class="assignment-note">
        Araç önce tedarikçi filonuza kaydedilir. Ardından Müşteriye Ata işlemiyle müşterinizi
        seçebilirsiniz.
      </p>
      <form @submit.prevent="addVehicle">
        <div style="max-height: 65vh; overflow-y: auto; padding-right: 10px">
          <!-- Section 1: Genel Bilgiler -->
          <h3 class="form-section-title">🚗 Genel Bilgiler</h3>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Plaka</UiField>
              <input
                type="text"
                v-model="newVehicleForm.plate"
                required
                class="form-input"
                placeholder="34 AAA 000"
                style="text-transform: uppercase"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Üretim Yılı</UiField>
              <input
                type="number"
                min="2010"
                max="2027"
                v-model.number="newVehicleForm.year"
                required
                class="form-input"
                placeholder="2024"
              />
            </div>
          </div>

          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Marka</UiField>
              <input
                type="text"
                v-model="newVehicleForm.brand"
                required
                class="form-input"
                placeholder="Renault"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Model</UiField>
              <input
                type="text"
                v-model="newVehicleForm.model"
                required
                class="form-input"
                placeholder="Clio"
              />
            </div>
          </div>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Versiyon</UiField
              ><input
                v-model="newVehicleForm.version"
                class="form-input"
                placeholder="1.5 Passion X-Pack"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Motor No</UiField
              ><input
                v-model="newVehicleForm.engine_no"
                class="form-input"
                placeholder="22R-1234567"
              />
            </div>
          </div>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Renk</UiField
              ><input v-model="newVehicleForm.color" class="form-input" placeholder="Beyaz" />
            </div>
            <div class="form-group">
              <UiField class="form-label">Sözleşme Başlangıcı</UiField
              ><input v-model="newVehicleForm.contract_start_date" type="date" class="form-input" />
            </div>
          </div>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Sözleşme Bitişi</UiField
              ><input v-model="newVehicleForm.contract_end_date" type="date" class="form-input" />
            </div>
            <div class="form-group">
              <UiField class="form-label">Aylık Kira Bedeli (TL)</UiField
              ><input
                v-model.number="newVehicleForm.monthly_rent"
                type="number"
                min="0"
                step="0.01"
                class="form-input"
              />
            </div>
          </div>
          <div class="form-group">
            <UiField class="form-label">Aylık Km Limiti</UiField
            ><input
              v-model.number="newVehicleForm.monthly_km_limit"
              type="number"
              min="0"
              class="form-input"
            />
          </div>

          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Araç Segmenti</UiField>
              <select v-model="newVehicleForm.vehicle_segment" class="form-select">
                <option value="A">A Segmenti</option>
                <option value="B">B Segmenti</option>
                <option value="C">C Segmenti</option>
                <option value="D">D Segmenti</option>
                <option value="E">E Segmenti</option>
              </select>
            </div>
            <div class="form-group">
              <UiField class="form-label">Araç Tipi</UiField>
              <select v-model="newVehicleForm.vehicle_type" class="form-select">
                <option value="Sedan">Sedan</option>
                <option value="SUV">SUV</option>
                <option value="Hatchback">Hatchback</option>
                <option value="Hafif Ticari">Hafif Ticari</option>
                <option value="Station Wagon">Station Wagon</option>
              </select>
            </div>
          </div>

          <div
            class="grid-2"
            style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px"
          >
            <div class="form-group">
              <UiField class="form-label">Yakıt Tipi</UiField>
              <select v-model="newVehicleForm.fuel" class="form-select">
                <option value="Benzin">Benzin</option>
                <option value="Dizel">Dizel</option>
                <option value="Hibrit">Hibrit</option>
                <option value="Elektrik">Elektrik</option>
              </select>
            </div>
            <div class="form-group">
              <UiField class="form-label">Güncel KM</UiField>
              <input
                type="number"
                min="0"
                v-model.number="newVehicleForm.mileage"
                required
                class="form-input"
                placeholder="15000"
              />
            </div>
          </div>

          <!-- Section 2: Tescil ve Hukuki -->
          <h3 class="form-section-title">📋 Tescil & Muayene Bilgileri</h3>
          <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
            <div class="form-group">
              <UiField class="form-label">Şase Numarası (Sicil No / Benzersiz ID)</UiField>
              <input
                type="text"
                v-model="newVehicleForm.chassis_no"
                required
                class="form-input"
                placeholder="VF3RENAULTME..."
                style="text-transform: uppercase"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Ruhsat Seri No</UiField>
              <input
                type="text"
                v-model="newVehicleForm.license_serial_no"
                required
                class="form-input"
                placeholder="AA123456"
                style="text-transform: uppercase"
              />
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 15px">
            <UiField class="form-label">Muayene Tarihi</UiField>
            <input
              type="date"
              v-model="newVehicleForm.inspection_date"
              required
              class="form-input"
            />
          </div>

          <!-- Section 3: Bakım ve Lastik -->
          <h3 class="form-section-title">⚙️ Servis & Lastik Durumu</h3>
          <div
            class="grid-3"
            style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px"
          >
            <div class="form-group">
              <UiField class="form-label">Lastik Değ. Tarihi</UiField>
              <input
                type="date"
                v-model="newVehicleForm.tire_change_date"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Son Servis Tarihi</UiField>
              <input
                type="date"
                v-model="newVehicleForm.last_service_date"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">Son Servis KM</UiField>
              <input
                type="number"
                min="0"
                v-model.number="newVehicleForm.last_service_mileage"
                required
                class="form-input"
                placeholder="10000"
              />
            </div>
          </div>

          <!-- Section 4: GPS & UTTS Entegrasyon Bilgileri -->
          <h3 class="form-section-title">📡 GPS & UTTS Entegrasyon Bilgileri</h3>
          <div
            class="grid-2"
            style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px"
          >
            <div class="form-group">
              <UiField class="form-label">GPS Cihaz Kodu / IMEI (Harita Takip)</UiField>
              <input
                type="text"
                v-model="newVehicleForm.gps_device_id"
                class="form-input"
                placeholder="Örn: GPS-TR-884920"
              />
            </div>
            <div class="form-group">
              <UiField class="form-label">UTTS Kodu (Ulusal Taşıt Tanıma Birimi ID)</UiField>
              <input
                type="text"
                v-model="newVehicleForm.utts_code"
                class="form-input"
                placeholder="Örn: UTTS-34-89201"
              />
            </div>
          </div>
        </div>

        <div
          style="
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 20px;
            border-top: 1px solid var(--border-color);
            padding-top: 15px;
          "
        >
          <UiButton type="button" @click="showAddModal = false" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Kaydediliyor...' : 'Kaydet' }}
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Details / Edit Modal -->
  <UiModal v-if="showDetailsModal" class="modal-overlay" @close="showDetailsModal = false">
    <div
      class="glass-panel modal-content fade-in-up"
      style="max-width: 650px; padding: 30px; background: #ffffff"
    >
      <!-- VIEW MODE -->
      <template v-if="!isEditingVehicle">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 15px;
            margin-bottom: 20px;
          "
        >
          <div>
            <span class="plate-badge">{{ selectedVehicle.plate }}</span>
            <h2 style="margin-top: 10px; color: #0f172a">
              {{ selectedVehicle.brand }} {{ selectedVehicle.model }}
            </h2>
          </div>
          <div style="display: flex; gap: 10px; align-items: center">
            <UiButton
              @click="startEditingVehicle"
              class="btn btn-secondary"
              style="
                padding: 6px 14px;
                font-size: 0.85rem;
                font-weight: 700;
                color: #2563eb;
                border: 1px solid #bfdbfe;
                background: #eff6ff;
              "
            >
              ✏️ Düzenle
            </UiButton>
            <span
              class="badge"
              :class="getVehicleBadgeClass(selectedVehicle.status)"
              style="font-size: 0.85rem; padding: 6px 12px"
              >{{ selectedVehicle.status }}</span
            >
          </div>
        </div>

        <div class="grid-2" style="gap: 20px; font-size: 0.95rem">
          <div>
            <h4 style="color: var(--secondary); margin-bottom: 10px">📋 Kimlik & Tescil</h4>
            <p style="margin-bottom: 8px">
              <strong>Şase / Sicil No:</strong>
              <span
                style="
                  font-family: monospace;
                  color: var(--primary);
                  background: rgba(79, 70, 229, 0.08);
                  padding: 2px 6px;
                  border-radius: 4px;
                  font-weight: bold;
                "
                >{{ selectedVehicle.chassis_no }}</span
              >
            </p>
            <p style="margin-bottom: 8px">
              <strong>Ruhsat Seri No:</strong>
              <span style="font-family: monospace">{{ selectedVehicle.license_serial_no }}</span>
            </p>
            <p style="margin-bottom: 8px">
              <strong>Araç Segmenti:</strong> {{ selectedVehicle.vehicle_segment }} Segmenti
            </p>
            <p style="margin-bottom: 8px">
              <strong>Araç Tipi:</strong> {{ selectedVehicle.vehicle_type }}
            </p>

            <div
              v-if="!selectedVehicle.is_active"
              style="
                margin-top: 15px;
                background: #fef2f2;
                border: 1px solid #fca5a5;
                padding: 12px;
                border-radius: 8px;
              "
            >
              <h5 style="color: #dc2626; margin-bottom: 5px; font-weight: bold; font-size: 0.85rem">
                🚫 FİLO DIŞI BIRAKILDI
              </h5>
              <p style="margin-bottom: 4px; font-size: 0.8rem; color: #7f1d1d; line-height: 1.4">
                <strong>Nedeni:</strong> {{ selectedVehicle.removal_reason }}
              </p>
              <p style="margin-bottom: 0; font-size: 0.8rem; color: #7f1d1d">
                <strong>Tarih:</strong> {{ formatDate(selectedVehicle.removed_at) }}
              </p>
            </div>
            <p style="margin-bottom: 8px">
              <strong>Üretim Yılı:</strong> {{ selectedVehicle.year }}
            </p>
            <p style="margin-bottom: 8px">
              <strong>Yakıt Türü:</strong> {{ selectedVehicle.fuel }}
            </p>
          </div>
          <div>
            <h4 style="color: var(--secondary); margin-bottom: 10px">⚙️ Durum & Operasyon</h4>
            <p style="margin-bottom: 8px">
              <strong>Güncel Kilometre:</strong> {{ selectedVehicle.mileage?.toLocaleString() }} km
            </p>
            <p style="margin-bottom: 8px">
              <strong>Muayene Tarihi:</strong> {{ formatDate(selectedVehicle.inspection_date) }}
            </p>
            <p style="margin-bottom: 8px">
              <strong>Lastik Değişim:</strong> {{ formatDate(selectedVehicle.tire_change_date) }}
            </p>
            <p style="margin-bottom: 8px">
              <strong>Son Servis Tarihi:</strong>
              {{ formatDate(selectedVehicle.last_service_date) }}
            </p>
            <p style="margin-bottom: 8px">
              <strong>Son Servis KM:</strong>
              {{ selectedVehicle.last_service_mileage?.toLocaleString() }} km
            </p>

            <h4 style="color: var(--secondary); margin-bottom: 10px; margin-top: 15px">
              📡 GPS & UTTS Entegrasyonu
            </h4>
            <p style="margin-bottom: 8px">
              <strong>GPS Cihaz ID:</strong>
              <span
                style="
                  font-family: monospace;
                  color: #2563eb;
                  background: #eff6ff;
                  padding: 2px 8px;
                  border-radius: 4px;
                  font-weight: bold;
                "
                >{{ selectedVehicle.gps_device_id || 'Tanımlanmadı' }}</span
              >
            </p>
            <p style="margin-bottom: 8px">
              <strong>UTTS Taşıt Tanıma Kodu:</strong>
              <span
                style="
                  font-family: monospace;
                  color: #059669;
                  background: #ecfdf5;
                  padding: 2px 8px;
                  border-radius: 4px;
                  font-weight: bold;
                "
                >{{ selectedVehicle.utts_code || 'Tanımlanmadı' }}</span
              >
            </p>
          </div>
        </div>

        <div
          style="
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
            border-top: 1px solid var(--border-color);
            padding-top: 15px;
          "
        >
          <template v-if="selectedVehicle.is_active">
            <router-link to="/dashboard/requests" class="btn btn-primary" style="font-size: 0.9rem"
              >Hizmet Talebi Oluştur</router-link
            >
          </template>
          <template v-else>
            <UiButton
              @click="reactivateVehicle(selectedVehicle)"
              class="btn btn-primary"
              style="
                font-size: 0.9rem;
                background: #059669;
                border: none;
                box-shadow: 0 4px 15px rgba(5, 150, 105, 0.2);
              "
            >
              Aracı Tekrar Filoya Ekle
            </UiButton>
          </template>
          <UiButton @click="showDetailsModal = false" class="btn btn-secondary">Kapat</UiButton>
        </div>
      </template>

      <!-- EDIT MODE -->
      <template v-else>
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 15px;
            margin-bottom: 20px;
          "
        >
          <h2 style="color: #0f172a; font-size: 1.3rem; font-weight: 800">
            Araç Bilgilerini & Entegrasyonu Düzenle
          </h2>
          <span class="plate-badge">{{ editVehicleForm.plate }}</span>
        </div>

        <form @submit.prevent="saveVehicleEdit">
          <div style="max-height: 60vh; overflow-y: auto; padding-right: 10px">
            <!-- GPS & UTTS Section -->
            <h3 class="form-section-title" style="color: #2563eb">
              📡 GPS & UTTS Entegrasyon Bilgileri
            </h3>
            <div
              class="grid-2"
              style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px"
            >
              <div class="form-group">
                <UiField class="form-label">GPS Cihaz Kodu / IMEI</UiField>
                <input
                  type="text"
                  v-model="editVehicleForm.gps_device_id"
                  class="form-input"
                  placeholder="Örn: GPS-TR-884920"
                />
              </div>
              <div class="form-group">
                <UiField class="form-label">UTTS Taşıt Tanıma Kodu</UiField>
                <input
                  type="text"
                  v-model="editVehicleForm.utts_code"
                  class="form-input"
                  placeholder="Örn: UTTS-34-89201"
                />
              </div>
            </div>

            <!-- Genel Bilgiler -->
            <h3 class="form-section-title">🚗 Genel Bilgiler</h3>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Plaka</UiField>
                <input
                  type="text"
                  v-model="editVehicleForm.plate"
                  required
                  class="form-input"
                  style="text-transform: uppercase"
                />
              </div>
              <div class="form-group">
                <UiField class="form-label">Güncel KM</UiField>
                <input
                  type="number"
                  min="0"
                  v-model.number="editVehicleForm.mileage"
                  required
                  class="form-input"
                />
              </div>
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Marka</UiField>
                <input type="text" v-model="editVehicleForm.brand" required class="form-input" />
              </div>
              <div class="form-group">
                <UiField class="form-label">Model</UiField>
                <input type="text" v-model="editVehicleForm.model" required class="form-input" />
              </div>
            </div>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Versiyon</UiField
                ><input
                  v-model="editVehicleForm.version"
                  class="form-input"
                  placeholder="1.5 Passion X-Pack"
                />
              </div>
              <div class="form-group">
                <UiField class="form-label">Motor No</UiField
                ><input
                  v-model="editVehicleForm.engine_no"
                  class="form-input"
                  placeholder="22R-1234567"
                />
              </div>
            </div>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Renk</UiField
                ><input v-model="editVehicleForm.color" class="form-input" />
              </div>
              <div class="form-group">
                <UiField class="form-label">Sözleşme Başlangıcı</UiField
                ><input
                  v-model="editVehicleForm.contract_start_date"
                  type="date"
                  class="form-input"
                />
              </div>
            </div>
            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Sözleşme Bitişi</UiField
                ><input
                  v-model="editVehicleForm.contract_end_date"
                  type="date"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <UiField class="form-label">Aylık Kira Bedeli (TL)</UiField
                ><input
                  v-model.number="editVehicleForm.monthly_rent"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-input"
                />
              </div>
            </div>
            <div class="form-group">
              <UiField class="form-label">Aylık Km Limiti</UiField
              ><input
                v-model.number="editVehicleForm.monthly_km_limit"
                type="number"
                min="0"
                class="form-input"
              />
            </div>

            <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr">
              <div class="form-group">
                <UiField class="form-label">Üretim Yılı</UiField>
                <input
                  type="number"
                  min="2010"
                  max="2027"
                  v-model.number="editVehicleForm.year"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <UiField class="form-label">Yakıt Tipi</UiField>
                <select v-model="editVehicleForm.fuel" class="form-select">
                  <option value="Benzin">Benzin</option>
                  <option value="Dizel">Dizel</option>
                  <option value="Hibrit">Hibrit</option>
                  <option value="Elektrik">Elektrik</option>
                </select>
              </div>
            </div>

            <div
              class="grid-2"
              style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px"
            >
              <div class="form-group">
                <UiField class="form-label">Ruhsat Seri No</UiField>
                <input type="text" v-model="editVehicleForm.license_serial_no" class="form-input" />
              </div>
              <div class="form-group">
                <UiField class="form-label">Muayene Tarihi</UiField>
                <input type="date" v-model="editVehicleForm.inspection_date" class="form-input" />
              </div>
            </div>
          </div>

          <div
            style="
              display: flex;
              gap: 15px;
              justify-content: flex-end;
              margin-top: 20px;
              border-top: 1px solid var(--border-color);
              padding-top: 15px;
            "
          >
            <UiButton type="button" @click="isEditingVehicle = false" class="btn btn-secondary"
              >Vazgeç</UiButton
            >
            <UiButton type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Kaydediliyor...' : '💾 Değişiklikleri Kaydet' }}
            </UiButton>
          </div>
        </form>
      </template>
    </div>
  </UiModal>

  <!-- Yakıt ve gider kaydı -->
  <UiModal v-if="showFuelModal" class="modal-overlay" @close="showFuelModal = false">
    <div
      class="glass-panel modal-content fade-in-up"
      style="max-width: 480px; padding: 28px; background: #fff"
    >
      <h2 style="margin-bottom: 6px">Yakıt / Gider Kaydı</h2>
      <p style="color: #64748b; margin-bottom: 20px">
        {{ currentVehicle?.plate }} · {{ currentVehicle?.brand }} {{ currentVehicle?.model }}
      </p>
      <form @submit.prevent="saveFuelRecord">
        <div class="form-group">
          <UiField class="form-label">Gider türü</UiField
          ><select v-model="fuelForm.kind" class="form-select">
            <option>Yakıt</option>
            <option>Otopark</option>
            <option>HGS / OGS</option>
            <option>Diğer</option>
          </select>
        </div>
        <div class="grid-2">
          <div class="form-group">
            <UiField class="form-label">Tutar (TL)</UiField
            ><input
              v-model.number="fuelForm.amount"
              class="form-input"
              type="number"
              min="0.01"
              step="0.01"
              required
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Tarih</UiField
            ><input v-model="fuelForm.date" class="form-input" type="date" required />
          </div>
        </div>
        <div class="grid-2">
          <div class="form-group">
            <UiField class="form-label">Litre (isteğe bağlı)</UiField
            ><input
              v-model.number="fuelForm.liters"
              class="form-input"
              type="number"
              min="0"
              step="0.01"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Kilometre</UiField
            ><input
              v-model.number="fuelForm.mileage"
              class="form-input"
              type="number"
              min="0"
              required
            />
          </div>
        </div>
        <div class="form-group">
          <UiField class="form-label">Açıklama</UiField
          ><input
            v-model="fuelForm.note"
            class="form-input"
            placeholder="İstasyon veya gider açıklaması"
          />
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 10px">
          <UiButton type="button" class="btn btn-secondary" @click="showFuelModal = false"
            >Vazgeç</UiButton
          ><UiButton class="btn btn-primary" type="submit">Kaydı Ekle</UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Remove Vehicle Reason Modal -->
  <UiModal v-if="showRemoveModal" class="modal-overlay" @close="showRemoveModal = false">
    <div class="glass-panel modal-content fade-in-up" style="max-width: 450px; padding: 30px">
      <h2
        style="margin-bottom: 10px; color: #dc2626; display: flex; align-items: center; gap: 10px"
      >
        <span>⚠️</span> Araç Kaldırma Talebi
      </h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px">
        <strong>{{ vehicleToRemove?.plate }}</strong> plakalı ({{ vehicleToRemove?.brand }}
        {{ vehicleToRemove?.model }}) aracı filodan kaldırmak istediğinize emin misiniz? Lütfen
        kaldırma nedenini belirtin:
      </p>

      <form @submit.prevent="confirmRemoveVehicle">
        <div class="form-group" style="margin-bottom: 25px">
          <UiField class="form-label">Kaldırma Nedeni</UiField>
          <select v-model="removalReason" required class="form-select">
            <option value="Sözleşme Bitişi">Sözleşme Bitişi</option>
            <option value="Araç Değişimi">Araç Değişimi</option>
            <option value="Pert">Pert</option>
            <option value="Araç Satışı">Araç Satışı</option>
          </select>
        </div>

        <div
          style="
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            border-top: 1px solid var(--border-color);
            padding-top: 15px;
          "
        >
          <UiButton type="button" @click="showRemoveModal = false" class="btn btn-secondary"
            >Vazgeç</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-danger"
            style="
              background: #dc2626;
              color: #fff;
              border: none;
              box-shadow: 0 4px 15px rgba(220, 38, 38, 0.2);
            "
          >
            Aracı Kaldır
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>
</template>

<script setup>
import { UiAlert, UiButton, UiField, UiModal } from '../components/ui/index.js'

import NotificationBell from '../components/NotificationBell.vue'
import { supplierApi, supplierFetch } from '../utils/supplierApi'
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'

const router = useRouter()
const route = useRoute()
const isSupplier = computed(() => Boolean(route.meta.supplierFleet))
const supplierId = Number(localStorage.getItem('fleetcar_supplier_id'))
const customers = ref([]),
  loadError = ref(''),
  feedback = ref('')
const assignmentVehicle = ref(null),
  assignmentCustomerId = ref(''),
  assignmentError = ref(''),
  assigning = ref(false)
const vehicleDetailsLink = (vehicle) => ({
  name: isSupplier.value ? 'SupplierVehicleDetails' : 'VehicleDetails',
  params: { vehicleId: vehicle.id },
})
function openAssignment(vehicle) {
  assignmentVehicle.value = vehicle
  assignmentCustomerId.value = String(vehicle.customer_id || '')
  assignmentError.value = ''
}
async function saveAssignment() {
  assigning.value = true
  assignmentError.value = ''
  try {
    const response = await supplierFetch(
      `/vehicles/${encodeURIComponent(assignmentVehicle.value.id)}/assignment`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: {
          customer_id: assignmentCustomerId.value ? Number(assignmentCustomerId.value) : null,
          expected_customer_id: assignmentVehicle.value.customer_id ?? null,
        },
      },
    )
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Müşteri ataması kaydedilemedi.')
    vehicles.value = vehicles.value.map((v) => (v.id === data.id ? data : v))
    feedback.value = data.customer_id
      ? `${data.plate}, ${data.customer_name} müşterisine atandı.`
      : `${data.plate} için müşteri ataması kaldırıldı.`
    assignmentVehicle.value = null
  } catch (error) {
    assignmentError.value = error.message || 'Bağlantı hatası. Tekrar deneyin.'
  } finally {
    assigning.value = false
  }
}
const goToVehicleDetails = (vehicle) => router.push(vehicleDetailsLink(vehicle))
const vehicles = ref([])
const requests = ref([])
const focusedVehicleId = ref(null)
const selectedVehicleIds = ref([])
const page = ref(1)
const pageSize = 10
const showFuelModal = ref(false)
const fuelRecords = ref([])
const fuelForm = reactive({
  kind: 'Yakıt',
  amount: '',
  date: new Date().toISOString().slice(0, 10),
  liters: '',
  mileage: 0,
  note: '',
})
const loading = ref(true)
const saving = ref(false)
const showAddModal = ref(isSupplier.value && route.query.add === '1')
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
  version: '',
  engine_no: '',
  year: 2024,
  fuel: 'Benzin',
  color: '',
  contract_start_date: '',
  contract_end_date: '',
  monthly_rent: 0,
  monthly_km_limit: 0,
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
  utts_code: '',
})

const activeVehiclesCount = computed(() => vehicles.value.filter((v) => v.is_active).length)
const customerName =
  localStorage.getItem(isSupplier.value ? 'fleetcar_supplier_name' : 'fleetcar_customer_name') ||
  'Filo Yöneticisi'
const userInitials = customerName
  .split(/\s+/)
  .map((part) => part[0])
  .slice(0, 2)
  .join('')
  .toLocaleUpperCase('tr-TR')
const availableStatuses = computed(() => [
  ...new Set(
    vehicles.value
      .filter((v) => v.is_active)
      .map((v) => v.status)
      .filter(Boolean),
  ),
])
const availableModels = computed(() => [
  ...new Set(
    vehicles.value.map((v) => [v.brand, v.model].filter(Boolean).join(' ')).filter(Boolean),
  ),
])
const statusCount = (status) =>
  vehicles.value.filter((v) => v.is_active && v.status === status).length
const incidentCount = computed(
  () =>
    requests.value.filter(
      (r) =>
        r.type === 'servis' &&
        /hasar|kaza/i.test((r.details?.service_type || '') + ' ' + (r.description || '')) &&
        !['Tamamlandı', 'İptal Edildi'].includes(r.status),
    ).length,
)
const currentVehicle = computed(
  () =>
    filteredVehicles.value.find((v) => v.id === focusedVehicleId.value) ||
    filteredVehicles.value[0] ||
    null,
)

const filters = reactive({
  search: String(route.query.search || ''),
  status: '',
  vehicle_segment: '',
  vehicle_type: '',
  fuel: '',
  plate: '',
  contract: '',
  assignment: '',
})

const newVehicleForm = reactive({
  plate: '',
  brand: '',
  model: '',
  version: '',
  engine_no: '',
  year: 2024,
  fuel: 'Benzin',
  color: '',
  contract_start_date: '',
  contract_end_date: '',
  monthly_rent: 0,
  monthly_km_limit: 0,
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
  utts_code: '',
})

const fetchVehicles = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const customerId =
      localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
    const ownerId = isSupplier.value ? supplierId : customerId
    if (!ownerId) throw new Error('Hesap bilgisi bulunamadı. Lütfen tekrar giriş yapın.')
    if (isSupplier.value) {
      const snapshot = await supplierApi('/snapshot')
      vehicles.value = snapshot.vehicles
      customers.value = snapshot.customers.map((c) => ({ ...c, company_name: c.title }))
      requests.value = snapshot.service.map((r) => ({ ...r, type: r.details.type }))
      fuelRecords.value = snapshot.fuel.map((r) => r.details)
      return
    }
    const query = new URLSearchParams({
      [isSupplier.value ? 'supplier_id' : 'customer_id']: ownerId,
    })
    const urls = ['/api/vehicles', '/api/requests', '/api/vehicle-expenses'].map(
      (url) => `${url}?${query}`,
    )
    if (isSupplier.value)
      urls[1] = `/api/requests?fleet_supplier_id=${encodeURIComponent(supplierId)}`
    if (isSupplier.value) urls.push(`/api/suppliers/${supplierId}/customers`)
    const responses = await Promise.all(urls.map((url) => fetch(url)))
    if (responses.some((response) => !response.ok))
      throw new Error('Filo bilgileri yüklenemedi. Tekrar deneyin.')
    const data = await Promise.all(responses.map((response) => response.json()))
    ;[vehicles.value, requests.value, fuelRecords.value] = data
    if (isSupplier.value) customers.value = data[3]
  } catch (error) {
    loadError.value = error.message || 'Sistem bağlantı hatası.'
  } finally {
    loading.value = false
  }
}

const addVehicle = async () => {
  saving.value = true
  try {
    const customerId =
      localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
    const payload = { ...newVehicleForm }
    if (isSupplier.value) {
      if (!supplierId) throw new Error('Tedarikçi bilgisi bulunamadı.')
      payload.supplier_id = supplierId
      payload.customer_id = null
    } else if (customerId) {
      payload.customer_id = parseInt(customerId)
    }

    const response = await (isSupplier.value
      ? supplierFetch('/vehicles', { method: 'POST', body: payload })
      : fetch('/api/vehicles', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }))

    if (response.ok) {
      const addedVehicle = await response.json()
      vehicles.value.push(addedVehicle)
      focusedVehicleId.value = addedVehicle.id
      showAddModal.value = false
      resetForm()
      if (isSupplier.value) {
        feedback.value = `${addedVehicle.plate} filonuza eklendi. Müşteriye Ata işlemiyle atayabilirsiniz.`
        const target = customers.value.find((c) => String(c.id) === String(route.query.customer_id))
        if (target) {
          openAssignment(addedVehicle)
          assignmentCustomerId.value = String(target.id)
        }
      }
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
  newVehicleForm.version = ''
  newVehicleForm.engine_no = ''
  newVehicleForm.year = 2024
  newVehicleForm.fuel = 'Benzin'
  newVehicleForm.color = ''
  newVehicleForm.contract_start_date = ''
  newVehicleForm.contract_end_date = ''
  newVehicleForm.monthly_rent = 0
  newVehicleForm.monthly_km_limit = 0
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

const startEditingVehicle = () => {
  if (!selectedVehicle.value) return
  const v = selectedVehicle.value
  editVehicleForm.plate = v.plate || ''
  editVehicleForm.brand = v.brand || ''
  editVehicleForm.model = v.model || ''
  editVehicleForm.version = v.version || ''
  editVehicleForm.engine_no = v.engine_no || ''
  editVehicleForm.year = v.year || 2024
  editVehicleForm.fuel = v.fuel || 'Benzin'
  editVehicleForm.color = v.color || ''
  editVehicleForm.contract_start_date = v.contract_start_date || ''
  editVehicleForm.contract_end_date = v.contract_end_date || ''
  editVehicleForm.monthly_rent = v.monthly_rent || 0
  editVehicleForm.monthly_km_limit = v.monthly_km_limit || 0
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(editVehicleForm),
    })

    if (response.ok) {
      const updatedVehicle = await response.json()
      const idx = vehicles.value.findIndex((v) => v.id === updatedVehicle.id)
      if (idx !== -1) {
        vehicles.value[idx] = updatedVehicle
      }
      selectedVehicle.value = updatedVehicle
      focusedVehicleId.value = updatedVehicle.id
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

const confirmRemoveVehicle = async () => {
  try {
    const response = await fetch(`/api/vehicles/${vehicleToRemove.value.id}/remove`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ reason: removalReason.value }),
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
        'Content-Type': 'application/json',
      },
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
    return d.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return dateStr
  }
}

const getVehicleBadgeClass = (status) => {
  return {
    'badge-active': status === 'Aktif',
    'badge-service': status === 'Serviste',
    'badge-tire': status === 'Lastik Değişiminde',
    'badge-roadside': status === 'Yol Yardımında',
    'badge-replacement': status === 'İkame Araç Bekliyor',
  }
}

const filteredVehicles = computed(() =>
  vehicles.value.filter((vehicle) => {
    if (!(activeTab.value === 'old' ? !vehicle.is_active : vehicle.is_active)) return false
    const search = filters.search.trim().toLocaleLowerCase('tr-TR')
    const searchable = [vehicle.plate, vehicle.brand, vehicle.model, vehicle.chassis_no].some(
      (value) =>
        String(value || '')
          .toLocaleLowerCase('tr-TR')
          .includes(search),
    )
    const model =
      !filters.vehicle_type ||
      [vehicle.brand, vehicle.model].filter(Boolean).join(' ') === filters.vehicle_type
    const plate =
      !filters.plate ||
      String(vehicle.plate || '')
        .toLocaleLowerCase('tr-TR')
        .includes(filters.plate.trim().toLocaleLowerCase('tr-TR'))
    const date = vehicle.contract_end_date ? new Date(vehicle.contract_end_date) : null
    const startDate = vehicle.contract_start_date ? new Date(vehicle.contract_start_date) : null
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const contract =
      !filters.contract ||
      (date &&
        (filters.contract === 'current'
          ? date >= today && (!startDate || startDate <= today)
          : date < today))
    const status =
      !filters.status ||
      (filters.status === 'Kaza'
        ? requests.value.some(
            (r) =>
              String(r.vehicle_id) === String(vehicle.id) &&
              /hasar|kaza/i.test((r.details?.service_type || '') + ' ' + (r.description || '')) &&
              !['Tamamlandı', 'İptal Edildi'].includes(r.status),
          )
        : vehicle.status === filters.status)
    const assignment =
      !isSupplier.value ||
      !filters.assignment ||
      (filters.assignment === 'available'
        ? !vehicle.customer_id
        : filters.assignment === 'assigned'
          ? Boolean(vehicle.customer_id)
          : String(vehicle.customer_id) === filters.assignment)
    return searchable && model && plate && contract && status && assignment
  }),
)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredVehicles.value.length / pageSize)))
const paginatedVehicles = computed(() =>
  filteredVehicles.value.slice((page.value - 1) * pageSize, page.value * pageSize),
)
const pageStart = computed(() =>
  filteredVehicles.value.length ? (page.value - 1) * pageSize + 1 : 0,
)
const pageEnd = computed(() => Math.min(page.value * pageSize, filteredVehicles.value.length))
const visiblePages = computed(() => {
  const start = Math.max(1, Math.min(page.value - 2, totalPages.value - 4))
  return Array.from({ length: Math.min(totalPages.value, 5) }, (_, i) => start + i)
})
const allVisibleSelected = computed(
  () =>
    paginatedVehicles.value.length > 0 &&
    paginatedVehicles.value.every((v) => selectedVehicleIds.value.includes(v.id)),
)
watch(
  () => route.query.search,
  (value) => {
    filters.search = String(value || '')
  },
)
watch(
  [filters, activeTab],
  () => {
    page.value = 1
  },
  { deep: true },
)
watch(totalPages, (count) => {
  if (page.value > count) page.value = count
})
const toggleVisibleSelection = (event) => {
  const ids = paginatedVehicles.value.map((v) => v.id)
  selectedVehicleIds.value = event.target.checked
    ? [...new Set([...selectedVehicleIds.value, ...ids])]
    : selectedVehicleIds.value.filter((id) => !ids.includes(id))
}
const vehicleColor = (color) =>
  ({
    beyaz: '#fff',
    siyah: '#1e293b',
    gri: '#94a3b8',
    gümüş: '#cbd5e1',
    mavi: '#2563eb',
    lacivert: '#1e3a8a',
    kırmızı: '#dc2626',
    yeşil: '#16a34a',
    sarı: '#facc15',
    turuncu: '#f97316',
    kahverengi: '#92400e',
    bej: '#d6c5a1',
  })[
    String(color || '')
      .trim()
      .toLocaleLowerCase('tr-TR')
  ] || '#c7d0d9'

const saveFuelRecord = async () => {
  try {
    const response = await fetch('/api/vehicle-expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...fuelForm,
        vehicle_id: currentVehicle.value.id,
        amount: Number(fuelForm.amount),
        liters: fuelForm.liters ? Number(fuelForm.liters) : null,
        mileage: Number(fuelForm.mileage),
      }),
    })
    if (!response.ok) {
      const error = await response.json()
      alert(error.detail || 'Gider kaydı eklenemedi.')
      return
    }
    fuelRecords.value.unshift({
      ...(await response.json()),
      vehicle_plate: currentVehicle.value.plate,
      created_at: fuelForm.date,
    })
    showFuelModal.value = false
  } catch (error) {
    console.error('Vehicle expense save error:', error)
    alert('Gider kaydı kaydedilirken bağlantı hatası oluştu.')
  }
}
const csvDownload = (rows, filename) => {
  const headers = [
    'Plaka',
    'Marka',
    'Model',
    'Versiyon',
    'Renk',
    'Yıl',
    'Şasi No',
    'Motor No',
    'Durum',
    'Sözleşme Başlangıcı',
    'Sözleşme Bitişi',
    'Aylık Kira',
    'Aylık Km Limiti',
    'Kilometre',
    'Yakıt',
  ]
  const fields = [
    'plate',
    'brand',
    'model',
    'version',
    'color',
    'year',
    'chassis_no',
    'engine_no',
    'status',
    'contract_start_date',
    'contract_end_date',
    'monthly_rent',
    'monthly_km_limit',
    'mileage',
    'fuel',
  ]
  const csv =
    '\uFEFF' +
    [headers, ...rows.map((row) => fields.map((field) => row[field] ?? ''))]
      .map((row) => row.map((value) => '"' + String(value).replaceAll('"', '""') + '"').join(';'))
      .join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
const exportVehicles = () => {
  const rows = filteredVehicles.value.filter(
    (v) => !selectedVehicleIds.value.length || selectedVehicleIds.value.includes(v.id),
  )
  csvDownload(rows, 'fleetrent-araclar-' + new Date().toISOString().slice(0, 10) + '.csv')
}

onMounted(() => {
  if (isSupplier.value && route.query.add === '1') {
    if (['A', 'B', 'C', 'D', 'E'].includes(route.query.segment))
      newVehicleForm.vehicle_segment = route.query.segment
    if (
      ['Sedan', 'SUV', 'Hatchback', 'Hafif Ticari', 'Station Wagon'].includes(
        route.query.vehicle_type,
      )
    )
      newVehicleForm.vehicle_type = route.query.vehicle_type
  }
  fetchVehicles()
})
</script>

<style scoped>
.supplier-stats {
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
}
.supplier-assignment {
  max-width: 520px;
  padding: 28px;
}
.supplier-assignment h2 {
  font-size: 22px;
}
.supplier-assignment p {
  color: #627493;
  font-size: 13px;
  margin: 14px 0;
}
.supplier-assignment footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}
.supplier-unassigned {
  color: #8995a7;
}
.assignment-note {
  line-height: 1.6;
}
.fleet-feedback {
  padding: 12px 16px;
  background: #e8f7f1;
  color: #147956;
  border-radius: 6px;
  font-size: 13px;
}
.fleet-feedback.error {
  background: #fff0eb;
  color: #a43a27;
}
.fleet-feedback button {
  margin-left: 10px;
}
.fleet-filters {
  flex-wrap: wrap;
}
@media (max-width: 600px) {
  .supplier-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 20px;
}

.fleet-page {
  --fleet-ink: #10284d;
  --fleet-muted: #73849b;
  --fleet-line: #e5edf5;
  --fleet-blue: #1265e9;
  padding: 0 18px 24px;
  background: #f5f8fc;
  color: var(--fleet-ink);
  font-size: 12px;
}

.fleet-topbar {
  min-height: 56px;
  margin: 0 -18px 20px;
  padding: 8px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border-bottom: 1px solid var(--fleet-line);
  background: rgba(255, 255, 255, 0.9);
}
.fleet-search {
  width: min(460px, 58%);
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #edf2f8;
  border-radius: 10px;
  background: #f6f9fd;
  color: #7c91aa;
  padding: 8px 12px;
  font-size: 20px;
}
.fleet-search input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fleet-ink);
  font: inherit;
  font-size: 11px;
}
.fleet-account {
  display: flex;
  align-items: center;
  gap: 9px;
}
.fleet-account > span:last-child {
  display: grid;
  gap: 2px;
}
.fleet-account strong {
  font-size: 11px;
}
.fleet-account small {
  color: var(--fleet-muted);
  font-size: 9px;
}
.fleet-avatar {
  display: grid;
  place-items: center;
  width: 29px;
  height: 29px;
  border-radius: 50%;
  background: #1c70dc;
  color: white;
  font-size: 10px;
  font-weight: 700;
}
.fleet-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin: 0 0 17px;
}
.fleet-heading h1 {
  margin: 2px 0 2px;
  font-size: 22px;
  letter-spacing: -0.03em;
}
.fleet-heading p {
  color: var(--fleet-muted);
  font-size: 10px;
}
.fleet-eyebrow {
  color: #91a1b5;
  font-size: 8px;
  font-weight: 750;
  letter-spacing: 0.1em;
}
.fleet-heading-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.fleet-heading-actions .btn {
  padding: 10px 14px;
  font-size: 11px;
}
.fleet-utility-button,
.fleet-filter-button {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--fleet-line);
  border-radius: 7px;
  background: white;
  color: #47617f;
  padding: 7px 10px;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
  white-space: nowrap;
}
.fleet-filter-button {
  color: white;
  background: var(--fleet-blue);
  border-color: var(--fleet-blue);
}
.fleet-stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 13px;
}
.fleet-stat {
  min-width: 0;
  min-height: 58px;
  padding: 10px;
  display: flex;
  gap: 9px;
  align-items: center;
  text-align: left;
  border: 1px solid var(--fleet-line);
  border-radius: 9px;
  background: white;
  color: var(--fleet-ink);
  cursor: pointer;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.fleet-stat-selected,
.fleet-stat:hover {
  border-color: #9fc2f7;
  box-shadow: 0 3px 12px rgba(26, 89, 167, 0.07);
}
.fleet-stat-icon {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 800;
}
.fleet-stat-icon.blue {
  background: #e8f1ff;
  color: #1764d9;
}
.fleet-stat-icon.green {
  background: #e8f8f1;
  color: #12a26c;
}
.fleet-stat-icon.amber {
  background: #fff5e2;
  color: #ed9c14;
}
.fleet-stat-icon.red {
  background: #fff0f0;
  color: #e44e54;
}
.fleet-stat-icon.navy {
  background: #edf2ff;
  color: #526fdd;
}
.fleet-stat small,
.fleet-stat strong {
  display: block;
}
.fleet-stat small {
  color: var(--fleet-muted);
  font-size: 9px;
  white-space: nowrap;
}
.fleet-stat strong {
  margin-top: 2px;
  font-size: 14px;
}
.fleet-stat em {
  margin-left: 5px;
  color: #1aa578;
  font-size: 8px;
  font-style: normal;
  font-weight: 600;
}
.fleet-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 13px;
}
.fleet-workspace:has(.fleet-no-selection) {
  grid-template-columns: minmax(0, 1fr);
}
.fleet-list-column {
  min-width: 0;
}
.fleet-list-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.fleet-filters label {
  display: grid;
  gap: 6px;
  flex: 1 1 135px;
  min-width: 0;
  color: var(--fleet-muted);
  font-size: 12px;
}
.fleet-list-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--fleet-line);
  border-radius: 9px;
  background: #fff;
}
.fleet-list-actions button {
  min-height: 40px;
  white-space: nowrap;
}
.fleet-filters {
  flex: 1 1 650px;
  min-height: 48px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 10px;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--fleet-line);
  border-radius: 9px;
  background: white;
}
.fleet-filters select,
.fleet-filters input {
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  height: 40px;
  flex: 1 1 105px;
  border: 1px solid #eaf0f6;
  border-radius: 6px;
  outline-color: #8bb5f5;
  background: #fff;
  color: #52677f;
  padding: 5px 7px;
  font: inherit;
  font-size: 12px;
}
.fleet-filters .fleet-filter-button,
.fleet-filters .fleet-utility-button {
  min-height: 40px;
  padding: 8px 14px;
}
.fleet-table-card,
.fleet-detail-panel,
.fleet-map-card {
  border: 1px solid var(--fleet-line);
  border-radius: 9px;
  background: white;
  overflow: hidden;
}
.fleet-table-scroll {
  overflow-x: auto;
}
.fleet-table {
  width: 100%;
  min-width: 1060px;
  border-collapse: collapse;
  text-align: left;
}
.fleet-table th {
  padding: 10px 6px;
  border-bottom: 1px solid var(--fleet-line);
  background: #fbfcfe;
  color: #8292a6;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.fleet-table td {
  height: 62px;
  padding: 8px 6px;
  border-bottom: 1px solid #eff3f8;
  color: #425771;
  font-size: 11px;
  white-space: nowrap;
}
.fleet-table tbody tr {
  cursor: pointer;
}
.fleet-table tbody tr:hover td,
.fleet-table tbody tr.fleet-row-selected td {
  background: #f5f9ff;
}
.fleet-table th:first-child,
.fleet-table td:first-child {
  padding-left: 10px;
}
.fleet-table input[type='checkbox'] {
  width: 12px;
  height: 12px;
  accent-color: #1466e9;
  vertical-align: middle;
}
.fleet-index {
  color: #9ba9b8 !important;
}
.fleet-plate {
  text-decoration: none;
  padding: 4px 5px 4px 17px;
  border-color: #d9e1e9;
  background: #fafcff;
  color: #264365;
  box-shadow: none;
  font-size: 11px;
}
.fleet-plate::before {
  width: 11px;
  font-size: 6px;
}
.fleet-vehicle-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.fleet-vehicle-cell > span:last-child {
  display: grid;
  gap: 3px;
}
.fleet-vehicle-cell strong {
  color: #294563;
  font-size: 11px;
  font-weight: 700;
}
.fleet-vehicle-cell small {
  color: #708399;
  font-size: 10px;
}
.fleet-car-thumb {
  display: grid;
  place-items: center;
  width: 34px;
  height: 24px;
  border-radius: 5px;
  background: #f1f5fa;
  font-size: 16px;
}
.tone-silver {
  color: #8090a0;
}
.tone-blue {
  color: #266dd2;
}
.tone-red {
  color: #d74346;
}
.tone-navy {
  color: #163b70;
}
.tone-graphite {
  color: #44515c;
}
.fleet-color {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #708399;
}
.fleet-color i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1px solid #cbd5e1;
  background: #c7d0d9;
}
.fleet-color .tone-blue {
  background: #266dd2;
}
.fleet-color .tone-red {
  background: #d74346;
}
.fleet-color .tone-navy {
  background: #163b70;
}
.fleet-color .tone-graphite {
  background: #44515c;
}
.fleet-status {
  padding: 3px 6px;
  border-radius: 20px;
  font-size: 10px;
  text-transform: none;
  white-space: nowrap;
}
.fleet-vin {
  color: #697f98 !important;
  font-family: monospace;
}
.fleet-row-menu {
  border: 0;
  background: none;
  color: #73859a;
  font-size: 13px;
  cursor: pointer;
}
.fleet-empty {
  height: 86px !important;
  text-align: center;
  color: #8697aa !important;
}
.fleet-table-footer {
  min-height: 37px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 10px;
  color: #8696a8;
  font-size: 8px;
}
.fleet-pagination {
  display: flex;
  align-items: center;
  gap: 3px;
}
.fleet-pagination button {
  min-width: 22px;
  height: 22px;
  border: 0;
  border-radius: 5px;
  background: white;
  color: #657b94;
  cursor: pointer;
  font-size: 9px;
}
.fleet-pagination button.current {
  background: #1467e9;
  color: white;
}
.fleet-pagination button:disabled {
  opacity: 0.35;
  cursor: default;
}
.fleet-detail-panel {
  position: sticky;
  top: 10px;
  padding: 12px 12px 0;
}
.fleet-detail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.fleet-detail-heading h2 {
  margin-top: 3px;
  font-size: 15px;
}
.fleet-close {
  border: 0;
  background: none;
  color: #8999aa;
  cursor: pointer;
  font-size: 17px;
}
.fleet-car-hero {
  height: 90px;
  margin: 10px -1px 9px;
  display: grid;
  place-items: center;
  position: relative;
  border-radius: 7px;
  background: linear-gradient(140deg, #f4f8fc, #eaf1f8);
}
.fleet-car-hero > span:first-child {
  font-size: 51px;
  filter: drop-shadow(0 4px 2px #b5c0cb);
}
.fleet-car-hero .fleet-status {
  position: absolute;
  top: 7px;
  right: 7px;
}
.fleet-detail-model {
  font-size: 11px;
  line-height: 1.4;
}
.fleet-detail-subtitle {
  margin-top: 2px;
  color: #667e99;
  font-size: 9px;
}
.fleet-specs {
  display: flex;
  justify-content: space-between;
  gap: 5px;
  padding: 9px 0;
  border-bottom: 1px solid #eef2f7;
  color: #627790;
  font-size: 8px;
}
.fleet-info-section {
  padding: 10px 0;
  border-bottom: 1px solid #eef2f7;
}
.fleet-info-section h4 {
  margin-bottom: 8px;
  font-size: 9px;
}
.fleet-info-section dl {
  display: grid;
  grid-template-columns: minmax(92px, 0.8fr) 1.2fr;
  gap: 6px 8px;
  font-size: 8px;
}
.fleet-info-section dt {
  color: #8494a7;
}
.fleet-info-section dd {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #314c6b;
  font-weight: 600;
}
.fleet-quick-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.fleet-quick-heading button {
  border: 0;
  background: none;
  color: #1567dd;
  font-size: 8px;
  cursor: pointer;
}
.fleet-quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}
.fleet-quick-grid button {
  min-height: 29px;
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid #e5edf5;
  border-radius: 6px;
  background: white;
  color: #49627f;
  padding: 4px 5px;
  text-align: left;
  font-size: 7px;
  cursor: pointer;
}
.fleet-quick-grid button:hover {
  border-color: #a8c8f5;
  background: #f7faff;
}
.fleet-quick-grid button span {
  color: #1465dd;
  font-size: 11px;
}
.fleet-history {
  border-bottom: 0;
}
.fleet-history ol {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0 0 0 10px;
  list-style: none;
}
.fleet-history li {
  min-height: 29px;
  position: relative;
  display: grid;
  gap: 3px;
  padding-left: 9px;
  border-left: 1px solid #e2eaf2;
}
.fleet-history li strong {
  color: #405978;
  font-size: 8px;
}
.fleet-history li small,
.fleet-history li p {
  margin: 0;
  color: #8797a9;
  font-size: 7px;
}
.fleet-history-dot {
  position: absolute;
  left: -4px;
  top: 1px;
  width: 7px;
  height: 7px;
  border: 1px solid #fff;
  border-radius: 50%;
  background: #1aaa77;
}
.fleet-history-dot.badge-service {
  background: #eea226;
}
.fleet-history-dot.badge-tire {
  background: #3178de;
}
.fleet-history-dot.badge-roadside {
  background: #e25056;
}
.fleet-history-empty {
  color: #8797a9;
  font-size: 8px;
}
.fleet-detail-footer {
  display: flex;
  gap: 6px;
  margin: 0 -12px;
  padding: 8px 10px;
  border-top: 1px solid #edf2f7;
}
.fleet-detail-footer button {
  flex: 1;
  border: 0;
  background: #f3f7fc;
  color: #46617f;
  padding: 7px 4px;
  border-radius: 5px;
  font-size: 8px;
  cursor: pointer;
}
.fleet-no-selection {
  min-height: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #6e829a;
  text-align: center;
}
.fleet-no-selection > span {
  font-size: 36px;
}
.fleet-no-selection strong {
  font-size: 10px;
}
.fleet-no-selection p {
  font-size: 9px;
}
.fleet-workspace:has(.fleet-no-selection) .fleet-no-selection {
  display: none;
}
.fleet-map-card {
  margin-top: 10px;
  padding: 12px;
}
.fleet-map-card > div {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.fleet-map-card button {
  border: 0;
  background: none;
  color: #1465dd;
  cursor: pointer;
}
.fleet-map-card iframe {
  width: 100%;
  height: 260px;
  border: 0;
  border-radius: 6px;
}
.fleet-map-card p {
  margin-top: 8px;
  color: #75879b;
  font-size: 9px;
}

@media (max-width: 1350px) {
  .fleet-page {
    padding-right: 6px;
    padding-left: 6px;
  }
  .fleet-topbar {
    margin-left: -6px;
    margin-right: -6px;
  }
  .fleet-workspace {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
  .fleet-stats {
    gap: 6px;
  }
  .fleet-stat {
    padding: 8px 6px;
    gap: 6px;
  }
}
@media (max-width: 1050px) {
  .fleet-workspace {
    grid-template-columns: 1fr;
  }
  .fleet-detail-panel {
    position: static;
  }
  .fleet-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 700px) {
  .fleet-page {
    padding: 0 0 18px;
  }
  .fleet-topbar {
    margin: 0 0 15px;
    padding: 8px 10px;
  }
  .fleet-account strong {
    max-width: 90px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .fleet-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .fleet-heading-actions {
    width: 100%;
    flex-wrap: wrap;
  }
  .fleet-heading-actions .btn {
    margin-left: auto;
  }
  .fleet-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .fleet-filters {
    align-items: stretch;
  }
  .fleet-filters label {
    flex-basis: calc(50% - 7px);
  }
  .fleet-filters .fleet-filter-button {
    width: 100%;
  }
  .fleet-table-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
@media (max-width: 900px) {
  .fleet-page .fleet-table td[data-label='Şasi No'],
  .fleet-page .fleet-table td[data-label='Kira Başlangıcı'] {
    display: flex !important;
  }
  :global(.portal-layout:has(.fleet-page) > .portal-sidebar) {
    width: 100%;
  }
  :global(.portal-layout:has(.fleet-page) > .portal-main) {
    margin-left: 0;
    width: 100%;
    max-width: 100%;
  }
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  position: relative;
}

/* Blue band for TR on Turkish Plates */
.plate-badge::before {
  content: 'TR';
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
.fleet-workspace {
  grid-template-columns: minmax(0, 1fr);
}
</style>
