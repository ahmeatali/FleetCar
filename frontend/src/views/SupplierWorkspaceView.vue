<template>
  <div class="portal-layout supplier-workspace">
    <Sidebar supplier />
    <main class="portal-main supplier-main-workspace">
      <header class="sw-topbar">
        <UiField class="sw-global-search"
          ><span>⌕</span
          ><input
            v-model="globalSearch"
            type="search"
            placeholder="Plaka, müşteri, sözleşme, fatura, rapor ara..."
            @keydown.enter="searchAll"
        /></UiField>
        <router-link
          to="/supplier-portal/approvals"
          class="sw-notification"
          :aria-label="`${pendingApprovals} bekleyen onay`"
          >♧<b v-if="pendingApprovals">{{ pendingApprovals }}</b></router-link
        >
        <div class="sw-profile">
          <span>{{ initials }}</span>
          <div>
            <strong>{{ data?.session?.name || companyName }}</strong
            ><small
              >{{ data?.settings?.company_name || data?.session?.company_name || companyName }} ·
              {{ roleLabels[role] }}</small
            >
          </div>
        </div>
      </header>
      <section class="sw-heading">
        <div>
          <h1>
            <span>{{ cfg.icon }}</span
            >{{
              section === 'home' ? `Hoş geldiniz, ${data?.session?.name || companyName}` : cfg.label
            }}
          </h1>
          <p>{{ cfg.description }}</p>
        </div>
        <div class="sw-heading-actions">
          <UiButton v-if="canCreate" class="sw-button primary" @click="openCreate"
            >＋ {{ cfg.create }}</UiButton
          ><UiButton
            v-if="
              !['home', 'settings', 'operations', 'branches', 'reservations'].includes(section) &&
              data?.session?.capabilities?.export_report
            "
            class="sw-button"
            @click="exportRows"
            >⇩ Dışa Aktar</UiButton
          ><span v-if="section === 'home'" class="sw-date">▦ {{ currentDate }}</span>
        </div>
      </section>
      <UiAlert v-if="error" class="sw-alert error" as="p" tone="error"
        >{{ error }}
        <router-link v-if="unauthorized" to="/supplier-login">Tekrar Giriş Yap</router-link
        ><UiButton v-else @click="load">Tekrar Dene</UiButton></UiAlert
      >
      <UiAlert v-if="notice" class="sw-alert" as="p" tone="info">{{ notice }}</UiAlert>
      <div v-if="loading && !data" class="sw-loading">Çalışma alanınız yükleniyor…</div>
      <template v-if="data">
        <section v-if="globalSearch.trim() && section === 'home'" class="sw-card sw-search-results">
          <h2>Arama Sonuçları</h2>
          <router-link v-for="item in searchResults" :key="item.key" :to="item.to"
            >{{ item.title }}<span>{{ item.subtitle }}</span></router-link
          >
          <p v-if="!searchResults.length">Bu arama için kayıt bulunamadı.</p>
        </section>
        <section v-if="section === 'home'" class="sw-kpis">
          <router-link class="sw-kpi" to="/supplier-portal/rentals?status=Teslim%20Bekliyor"
            ><div>
              <small>Teslim Bekleyen Kiralamalar</small
              ><strong>{{
                data.rentals.filter((r) => r.status === 'Teslim Bekliyor').length
              }}</strong>
            </div></router-link
          ><router-link class="sw-kpi" to="/supplier-portal/returns"
            ><div>
              <small>İade / Mutabakat Bekleyen</small
              ><strong>{{
                data.records.filter(
                  (r) => r.kind === 'return' && !['Tamamlandı', 'İptal'].includes(r.raw_status),
                ).length
              }}</strong>
            </div></router-link
          ><router-link class="sw-kpi" to="/supplier-portal/maintenance"
            ><div>
              <small>Bakım Önerileri</small
              ><strong>{{
                data.records.filter((r) => r.kind === 'maintenance' && r.raw_status === 'Önerildi')
                  .length
              }}</strong>
            </div></router-link
          ><router-link class="sw-kpi" to="/supplier-portal/fines"
            ><div>
              <small>Mali Eşleştirme Bekleyen</small
              ><strong>{{ data.matching_queue.length }}</strong>
            </div></router-link
          >
        </section>
        <section
          v-if="!['settings', 'users', 'operations', 'branches', 'reservations'].includes(section)"
          class="sw-kpis"
        >
          <UiButton
            v-for="card in kpis"
            :key="card.label"
            class="sw-kpi"
            @click="card.to ? router.push(card.to) : (filters.status = card.status || '')"
            ><span :class="['sw-kpi-icon', card.tone || 'blue']">{{ card.icon || cfg.icon }}</span>
            <div>
              <small>{{ card.label }}</small
              ><strong>{{ card.value }}</strong
              ><em>{{ card.note }}</em>
            </div></UiButton
          >
        </section>

        <SupplierFleetPlanning
          v-if="section === 'home'"
          compact
          :role="role"
          :customers="data.customers"
        />
        <!-- The overview and reports use the same ledger, with no synthetic history. -->
        <template v-if="['home', 'reports'].includes(section)">
          <section v-if="section === 'reports'" class="sw-card sw-report-ledger">
            <div class="sw-card-heading sw-detailed-report-heading">
              <h2>Ayrıntılı Filo Raporları</h2>
              <div
                v-if="['owner', 'finance', 'fleet_manager'].includes(role)"
                class="sw-report-export-actions"
              >
                <UiButton class="sw-button" @click="exportServerReport('xlsx')"
                  >Excel İndir</UiButton
                >
                <UiButton class="sw-button" @click="exportServerReport('pdf')">PDF İndir</UiButton>
              </div>
            </div>
            <form class="sw-detailed-report-filters" @submit.prevent="loadServerReport">
              <UiField
                >Rapor Türü
                <select
                  aria-label="Ayrıntılı Rapor"
                  v-model="serverReportKey"
                  @change="loadServerReport"
                >
                  <option v-for="report in reportCatalog" :key="report.key" :value="report.key">
                    {{ report.label }}
                  </option>
                </select>
              </UiField>
              <UiField
                >Marka<input v-model="reportFilters.brand" placeholder="Tüm markalar"
              /></UiField>
              <UiField
                >Model<input v-model="reportFilters.model" placeholder="Tüm modeller"
              /></UiField>
              <UiField
                >Araç Grubu<input v-model="reportFilters.group" placeholder="Tüm gruplar"
              /></UiField>
              <UiField
                >Sözleşme
                <select v-model="reportFilters.contract" aria-label="Rapor Sözleşmesi">
                  <option value="">Tümü</option>
                  <option
                    v-for="contract in data.records.filter(
                      (r) => r.kind === 'contract' && r.source === 'operation',
                    )"
                    :key="contract.id"
                    :value="contract.id"
                  >
                    {{ contract.number }}
                  </option>
                </select>
              </UiField>
              <UiButton type="submit" class="sw-button primary">Filtreleri Uygula</UiButton>
            </form>
            <p v-if="serverReport" class="sw-muted">{{ serverReport.note }}</p>
            <UiTable v-if="serverReport" class="sw-table-scroll"
              ><table class="sw-table">
                <thead>
                  <tr>
                    <th v-for="key in serverReport.columns" :key="key">
                      {{ serverReport.labels[key] }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in serverReport.rows" :key="index">
                    <td v-for="key in serverReport.columns" :key="key">{{ row[key] ?? '—' }}</td>
                  </tr>
                  <tr v-if="!serverReport.rows.length">
                    <td :colspan="serverReport.columns.length">Bu filtrelerde kayıt yok.</td>
                  </tr>
                </tbody>
              </table></UiTable
            >
          </section>
          <nav v-if="section === 'reports'" class="sw-status-tabs" aria-label="Rapor kategorileri">
            <UiButton
              v-for="tab in reportTabs"
              :key="tab"
              :class="{ active: reportTab === tab }"
              @click="reportTab = tab"
              >{{ tab }}</UiButton
            >
          </nav>
          <section v-if="section === 'reports'" class="sw-card sw-report-filter">
            <UiField
              >Müşteri<select v-model="filters.customer">
                <option value="">Tümü</option>
                <option v-for="c in data.customers" :key="c.id" :value="String(c.id)">
                  {{ c.title }}
                </option>
              </select></UiField
            ><UiField
              >Araç<select v-model="filters.vehicle">
                <option value="">Tümü</option>
                <option v-for="v in data.vehicles" :key="v.id" :value="v.id">{{ v.plate }}</option>
              </select></UiField
            ><UiField>Başlangıç<input v-model="filters.start" type="date" /></UiField
            ><UiField>Bitiş<input v-model="filters.end" type="date" /></UiField
            ><UiButton class="sw-button" @click="clearFilters">Temizle</UiButton>
          </section>
          <div class="sw-dashboard-grid">
            <article class="sw-card">
              <div class="sw-card-heading">
                <h2>
                  {{
                    section === 'home' ? 'Kayıtlı Gelir ve Maliyet' : 'Aylık Ciro ve Maliyet (TL)'
                  }}
                </h2>
                <small>Gerçekleşen kayıtlar</small>
              </div>
              <div v-if="analytics.monthly.length" class="sw-bar-chart">
                <div v-for="month in analytics.monthly" :key="month.key" class="sw-bar-group">
                  <div>
                    <i
                      class="income"
                      :style="{ height: `${(month.revenue / maxMonthly) * 150}px` }"
                      :title="money(month.revenue)"
                    ></i
                    ><i
                      class="cost"
                      :style="{ height: `${(month.cost / maxMonthly) * 150}px` }"
                      :title="money(month.cost)"
                    ></i>
                  </div>
                  <small>{{ month.key }}</small>
                </div>
              </div>
              <p v-else class="sw-empty">Grafik için dönem kaydı bulunmuyor.</p>
              <div class="sw-legend">
                <span><i class="income" /> Gelir</span><span><i class="cost" /> Maliyet</span>
              </div>
            </article>
            <article class="sw-card">
              <div class="sw-card-heading">
                <h2>Araç Durum Dağılımı</h2>
                <router-link to="/supplier-portal/vehicles">Araçları Gör →</router-link>
              </div>
              <div class="sw-distribution">
                <div
                  class="sw-donut"
                  :style="{ background: donut(analytics.statusGroups.map((g) => g.count)) }"
                >
                  <div>
                    <strong>{{ analytics.cars.length }}</strong
                    ><small>Toplam Araç</small>
                  </div>
                </div>
                <div>
                  <div
                    v-for="(group, index) in analytics.statusGroups"
                    :key="group.label"
                    class="sw-distribution-row"
                  >
                    <i :style="{ background: colors[index] }" /><span>{{ group.label }}</span
                    ><strong>{{ group.count }}</strong>
                  </div>
                </div>
              </div>
            </article>
            <article v-if="section === 'home'" class="sw-card">
              <div class="sw-card-heading">
                <h2>Araç Konumları</h2>
                <router-link to="/supplier-portal/vehicles">Tüm Araçları Gör →</router-link>
              </div>
              <iframe
                v-if="mapUrl"
                :src="mapUrl"
                title="Kayıtlı araç konumu"
                loading="lazy"
                class="sw-map"
              />
              <p v-else class="sw-empty">GPS konum kaydı bulunmuyor.</p>
              <small class="sw-muted"
                >{{ locatedCars.length }} araçta kayıtlı koordinat var. Son kayıt kullanılır.</small
              >
            </article>
            <article v-else class="sw-card">
              <h2>Müşterilere Göre Araç Dağılımı</h2>
              <div
                v-for="c in analytics.customerDistribution.slice(0, 7)"
                :key="c.label"
                class="sw-horizontal-row"
              >
                <span>{{ c.label }}</span
                ><i
                  :style="{
                    width: `${(c.count / Math.max(1, ...analytics.customerDistribution.map((x) => x.count))) * 100}%`,
                  }"
                /><strong>{{ c.count }}</strong>
              </div>
              <p v-if="!analytics.customerDistribution.length" class="sw-empty">
                Atanmış araç bulunmuyor.
              </p>
            </article>
            <article class="sw-card">
              <div class="sw-card-heading">
                <h2>Son İşlemler</h2>
                <router-link to="/supplier-portal/contracts">Tümünü Gör →</router-link>
              </div>
              <div v-for="event in data.events.slice(0, 5)" :key="event.id" class="sw-event-row">
                <span>▤</span>
                <div>
                  <strong>{{ event.title }}</strong
                  ><small>{{ event.actor }} · {{ dateText(event.date) }}</small>
                </div>
              </div>
              <p v-if="!data.events.length" class="sw-empty">Henüz işlem geçmişi yok.</p>
            </article>
            <article class="sw-card">
              <div class="sw-card-heading">
                <h2>Yaklaşan İşlemler</h2>
                <router-link to="/supplier-portal/reports">Tümünü Gör →</router-link>
              </div>
              <router-link
                v-for="event in analytics.upcoming.slice(0, 5)"
                :key="event.key"
                :to="vehicleLink(event.vehicle_id)"
                class="sw-upcoming"
                ><span>▦</span>
                <div>
                  <strong>{{ event.title }}</strong
                  ><small>{{ event.plate }} · {{ dateText(event.date) }}</small>
                </div>
                <b>{{ event.days }} gün</b></router-link
              >
              <p v-if="!analytics.upcoming.length" class="sw-empty">
                Önümüzdeki 90 gün içinde kayıtlı tarih yok.
              </p>
            </article>
            <article v-if="section === 'home'" class="sw-card">
              <h2>Hızlı İşlemler</h2>
              <div class="sw-quick-grid">
                <router-link
                  v-for="key in [
                    'vehicles',
                    'contracts',
                    'offers',
                    'service',
                    'damage',
                    'hgs',
                    'fuel',
                    'invoices',
                    'reports',
                  ]"
                  :key="key"
                  :to="`/supplier-portal/${key}${key !== 'vehicles' && key !== 'reports' ? '?new=1' : ''}`"
                  ><span>{{ supplierModules[key].icon }}</span
                  >{{ supplierModules[key].label }}</router-link
                >
              </div>
            </article>
            <article v-else class="sw-card">
              <h2>Maliyet Türleri</h2>
              <div v-for="c in analytics.costCategories" :key="c.label" class="sw-detail-line">
                <span>{{ c.label }}</span
                ><strong>{{ money(c.amount) }}</strong>
              </div>
              <p v-if="!analytics.costCategories.length" class="sw-empty">
                Gider kaydı bulunmuyor.
              </p>
            </article>
            <article class="sw-card">
              <h2>Marka / Model Dağılımı</h2>
              <div
                v-for="c in analytics.models.slice(0, 5)"
                :key="c.label"
                class="sw-horizontal-row"
              >
                <span>{{ c.label }}</span
                ><i
                  :style="{
                    width: `${(c.count / Math.max(1, ...analytics.models.map((x) => x.count))) * 100}%`,
                  }"
                /><strong>{{ c.count }}</strong>
              </div>
            </article>
            <article class="sw-card">
              <h2>Sözleşme Bitişleri</h2>
              <router-link
                v-for="r in endingContracts.slice(0, 5)"
                :key="r.id"
                :to="recordLink(r)"
                class="sw-upcoming"
                ><div>
                  <strong>{{ r.plate || r.number }}</strong
                  ><small>{{ r.customer_name }} · {{ dateText(r.end_date) }}</small>
                </div>
                <b>{{ daysUntil(r.end_date) }} gün</b></router-link
              >
              <p v-if="!endingContracts.length" class="sw-empty">Yaklaşan sözleşme bitişi yok.</p>
            </article>
            <article class="sw-card">
              <h2>Maliyet Özeti</h2>
              <strong class="sw-total">{{ money(analytics.totals.cost) }}</strong>
              <div
                v-for="(item, index) in analytics.costCategories"
                :key="item.label"
                class="sw-distribution-row"
              >
                <i :style="{ background: colors[index % colors.length] }" /><span>{{
                  item.label
                }}</span
                ><strong>{{ money(item.amount) }}</strong>
              </div>
              <p class="sw-muted">
                Kira taahhütleri gerçekleşmiş gelire eklenmez. HGS yüklemesi ve tahsilat çift
                sayılmaz.
              </p>
            </article>
          </div>
          <section v-if="section === 'reports'" class="sw-report-cost-charts">
            <article v-for="category in ['Yakıt', 'HGS', 'Servis']" :key="category" class="sw-card">
              <h2>{{ category }} Maliyetleri (TL)</h2>
              <div v-if="categoryMonths(category).length" class="sw-bar-chart">
                <div
                  v-for="month in categoryMonths(category)"
                  :key="month.key"
                  class="sw-bar-group"
                >
                  <div>
                    <i
                      class="income"
                      :style="{
                        height: `${(month.amount / Math.max(1, ...categoryMonths(category).map((m) => m.amount))) * 125}px`,
                      }"
                      :title="money(month.amount)"
                    />
                  </div>
                  <small>{{ month.key }}</small>
                </div>
              </div>
              <p v-else class="sw-empty">Bu kategoride dönem kaydı yok.</p>
            </article>
          </section>
          <section
            v-if="section === 'reports' && reportTab === 'Araç Kullanımı'"
            class="sw-card sw-report-ledger"
          >
            <h2>Araç Kullanım Kayıtları</h2>
            <UiTable class="sw-table-scroll"
              ><table class="sw-table">
                <thead>
                  <tr>
                    <th>Plaka</th>
                    <th>Marka / Model</th>
                    <th>Toplam Km</th>
                    <th>Aylık Km</th>
                    <th>Aylık Limit</th>
                    <th>Kayıtlı Kullanım (Saat)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in analytics.cars" :key="v.id">
                    <td>{{ v.plate }}</td>
                    <td>{{ v.brand }} {{ v.model }}</td>
                    <td>{{ num(v.mileage).toLocaleString('tr-TR') }}</td>
                    <td>
                      {{
                        v.current_month_km != null
                          ? num(v.current_month_km).toLocaleString('tr-TR')
                          : 'Veri yok'
                      }}
                    </td>
                    <td>{{ v.monthly_km_limit || '—' }}</td>
                    <td>{{ usageHours(v.id) ?? 'Veri yok' }}</td>
                  </tr>
                </tbody>
              </table></UiTable
            >
          </section>
          <section
            v-if="section === 'reports' && reportTab === 'Müşteri Raporları'"
            class="sw-card sw-report-ledger"
          >
            <h2>Müşterilere Göre Kayıtlı Gelir</h2>
            <div
              v-for="c in data.customers.filter(
                (c) => !filters.customer || String(c.id) === filters.customer,
              )"
              :key="c.id"
              class="sw-detail-line"
            >
              <span>{{ c.title }}</span
              ><strong>{{
                money(
                  analytics.revenue
                    .filter((r) => r.customer_id === c.id)
                    .reduce((s, r) => s + num(r.amount), 0),
                )
              }}</strong>
            </div>
          </section>
          <section v-if="section === 'reports'" class="sw-card sw-report-ledger">
            <div class="sw-card-heading">
              <h2>
                {{
                  reportTab === 'Genel Bakış' ? 'Gerçekleşen Gelir / Maliyet Defteri' : reportTab
                }}
              </h2>
              <UiButton
                v-if="data.session.capabilities.export_report"
                class="sw-button"
                @click="exportLedger"
                >CSV İndir</UiButton
              >
            </div>
            <UiTable class="sw-table-scroll"
              ><table class="sw-table">
                <thead>
                  <tr>
                    <th>Tarih</th>
                    <th>Kaynak</th>
                    <th>Plaka</th>
                    <th>Müşteri</th>
                    <th>Kategori</th>
                    <th>Tutar</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(r, index) in reportRows" :key="`${r.id}-${index}`">
                    <td>{{ dateText(r.date) }}</td>
                    <td>{{ r.number }}</td>
                    <td>{{ r.plate || '—' }}</td>
                    <td>{{ r.customer_name || '—' }}</td>
                    <td>{{ r.category }}</td>
                    <td>{{ money(r.amount) }}</td>
                  </tr>
                  <tr v-if="!reportRows.length">
                    <td colspan="6" class="sw-empty">Bu rapor ve filtre için kayıt bulunamadı.</td>
                  </tr>
                </tbody>
              </table></UiTable
            >
          </section>
          <section v-if="section === 'reports'" class="sw-card sw-report-ledger">
            <h2>En Yüksek Maliyetli Araçlar</h2>
            <div v-for="r in highCostVehicles.slice(0, 5)" :key="r.id" class="sw-detail-line">
              <router-link :to="vehicleLink(r.id)">{{ r.plate }}</router-link
              ><strong>{{ money(r.amount) }}</strong>
            </div>
            <p v-if="!highCostVehicles.length" class="sw-empty">Araç maliyet kaydı yok.</p>
          </section>
        </template>

        <SupplierFleetPlanning
          v-else-if="['operations', 'branches', 'reservations'].includes(section)"
          :mode="section"
          :role="role"
          :customers="data.customers"
        />
        <template v-else-if="section === 'settings'">
          <div class="sw-settings-tabs" role="tablist" aria-label="Ayarlar">
            <UiButton
              id="settings-general-tab"
              class="sw-button"
              role="tab"
              :class="{ primary: settingsTab === 'general' }"
              :aria-selected="settingsTab === 'general'"
              aria-controls="settings-general"
              @click="settingsTab = 'general'"
              >Genel Ayarlar</UiButton
            >
            <UiButton
              id="settings-integrations-tab"
              class="sw-button"
              role="tab"
              :class="{ primary: settingsTab === 'integrations' }"
              :aria-selected="settingsTab === 'integrations'"
              aria-controls="settings-integrations"
              @click="settingsTab = 'integrations'"
              >Entegrasyonlar</UiButton
            >
          </div>
          <div
            v-if="settingsTab === 'integrations'"
            id="settings-integrations"
            role="tabpanel"
            aria-labelledby="settings-integrations-tab"
          >
            <SupplierIntegrations :vehicles="data.vehicles" :role="role" @updated="load" />
          </div>
          <section
            v-if="settingsTab === 'general'"
            id="settings-general"
            role="tabpanel"
            aria-labelledby="settings-general-tab"
            class="sw-card sw-settings"
          >
            <h2>Şirket ve Operasyon Ayarları</h2>
            <p class="sw-muted">Eşikler rapor uyarılarını ve yeni işlem onaylarını belirler.</p>
            <form @submit.prevent="saveSettings">
              <UiField
                >Şirket Çalışma Modu<select v-model="settingsForm.company_mode">
                  <option value="FLEETRENT_PANEL">FleetRent Paneli</option>
                  <option value="EXTERNAL_INTEGRATION">Harici Entegrasyon</option>
                </select></UiField
              ><UiField>Şirket Görünen Adı<input v-model="settingsForm.company_name" /></UiField
              ><UiField
                >Onay Gerektiren Tutar (TL)<input
                  v-model.number="settingsForm.approval_threshold"
                  type="number"
                  min="0"
                  required /></UiField
              ><UiField
                >Düşük HGS Bakiye Eşiği (TL)<input
                  v-model.number="settingsForm.low_balance"
                  type="number"
                  min="0"
                  required /></UiField
              ><UiField
                >Yenileme Uyarısı (Gün)<input
                  v-model.number="settingsForm.renewal_days"
                  type="number"
                  min="1"
                  max="365"
                  required /></UiField
              ><UiField
                >Düşük Kullanım Eşiği (Aylık Km)<input
                  v-model.number="settingsForm.low_usage_km"
                  type="number"
                  min="0"
                  required /></UiField
              ><UiField
                >Yakıt İnceleme Eşiği (L/100 km)<input
                  v-model.number="settingsForm.fuel_l100_threshold"
                  type="number"
                  min="0.1"
                  step="0.1"
                  required /></UiField
              ><UiButton class="sw-button primary" :disabled="saving || role !== 'owner'"
                >Ayarları Kaydet</UiButton
              >
            </form>
            <p class="sw-muted">
              ERP, HGS ve e-imza sağlayıcıları henüz seçilmedi. GPS ve yakıt bağlantılarını
              Entegrasyonlar sekmesinden yönetin.
            </p>
          </section>
        </template>

        <template v-else-if="section === 'savings'">
          <section class="sw-card">
            <div class="sw-card-heading">
              <h2>Tespitler ve Öneriler</h2>
              <small>Eşikler: Ayarlar ekranı</small>
            </div>
            <UiTable class="sw-table-scroll"
              ><table class="sw-table">
                <thead>
                  <tr>
                    <th>Kategori</th>
                    <th>Tespit</th>
                    <th>Kanıt</th>
                    <th>İncelenecek Tutar</th>
                    <th>Aksiyon</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in findings" :key="r.id">
                    <td>
                      <span class="sw-status amber">{{ r.category }}</span>
                    </td>
                    <td>{{ r.title }}</td>
                    <td>{{ r.evidence }}</td>
                    <td>{{ r.amount ? money(r.amount) : '—' }}</td>
                    <td>
                      <router-link class="sw-button" :to="vehicleLink(r.vehicle_id)"
                        >Araç Detayı</router-link
                      >
                    </td>
                  </tr>
                  <tr v-if="!findings.length">
                    <td colspan="5" class="sw-empty">
                      Kayıtlı verilerde bu eşikleri aşan tespit bulunamadı.
                    </td>
                  </tr>
                </tbody>
              </table></UiTable
            >
            <p class="sw-muted">
              Bu tespitler inceleme önerisidir. Tutarlar gerçekleşmiş tasarruf değildir; AI veya dış
              piyasa kıyaslaması kullanılmaz.
            </p>
          </section>
        </template>

        <template v-else>
          <section v-if="section === 'planning'" class="sw-scenarios">
            <article class="sw-card">
              <h2>Mevcut Filo</h2>
              <div class="sw-detail-line">
                <span>Aktif araç</span
                ><strong>{{ analytics.cars.filter((v) => v.is_active).length }}</strong>
              </div>
              <div class="sw-detail-line">
                <span>Kayıtlı aylık kira taahhüdü</span
                ><strong>{{ money(currentMonthlyRent) }}</strong>
              </div>
              <p class="sw-muted">Taahhüt, toplam sahip olma maliyeti değildir.</p>
            </article>
            <article v-for="r in rows" :key="r.id" class="sw-card" @click="selectRow(r)">
              <h2>{{ r.title }}</h2>
              <div class="sw-detail-line">
                <span>Araç Sayısı</span><strong>{{ r.details.vehicle_count }}</strong>
              </div>
              <div class="sw-detail-line">
                <span>Aylık Tahmin</span
                ><strong>{{
                  money(num(r.details.vehicle_count) * num(r.details.monthly_unit_cost))
                }}</strong>
              </div>
              <div class="sw-detail-line">
                <span>Yıllık Tahmin</span
                ><strong>{{
                  money(num(r.details.vehicle_count) * num(r.details.monthly_unit_cost) * 12)
                }}</strong>
              </div>
              <p>{{ r.details.assumptions }}</p>
            </article>
          </section>
          <section v-if="section === 'approvals'" class="sw-card sw-permissions">
            <h2>Yetki Matrisi ve Onay Limiti</h2>
            <div class="sw-role-grid">
              <span><strong>Şirket Sahibi</strong>Tüm modüller, onay ve kullanıcı yönetimi</span
              ><span
                ><strong>Operasyon</strong>Müşteri, araç, teklif, sözleşme, teslimat, bakım</span
              ><span><strong>Finans</strong>Fatura, tahsilat, ödeme, TPC, yakıt ve HGS</span
              ><span
                ><strong>Filo Yöneticisi</strong>Filo operasyonları, satış hazırlığı ve rapor dışa
                aktarma</span
              ><span><strong>Satış</strong>Müşteri, teklif, sözleşme ve satış dosyaları</span
              ><span
                ><strong>Teslim &amp; İade</strong>Teslim formu ve iade kontrolü; finans son
                mutabakatı hariç</span
              ><span><strong>Görüntüleyici</strong>Salt okuma ve rapor görüntüleme</span>
            </div>
            <p>
              {{ money(data.settings.approval_threshold) }} üzerindeki ticari işlemler güncel tutar
              ve sürüm için şirket sahibi onayı gerektirir.
            </p>
          </section>
          <section v-if="section === 'service'" class="sw-card sw-due-card">
            <h2>Yaklaşan Bakımlar</h2>
            <router-link v-for="v in dueServiceCars.slice(0, 6)" :key="v.id" :to="vehicleLink(v.id)"
              ><strong>{{ v.plate }}</strong
              ><span
                >{{
                  v.next_service_due_date ? dateText(v.next_service_due_date) : 'Km bazlı bakım'
                }}
                ·
                {{
                  v.next_service_due_km ? `${v.next_service_due_km - num(v.mileage)} km kaldı` : ''
                }}</span
              ></router-link
            >
            <p v-if="!dueServiceCars.length" class="sw-muted">
              Yaklaşan bakım kaydı bulunmuyor. Araç detayından bakım tarihini ve kilometresini
              tanımlayın.
            </p>
          </section>
          <ResponsibilityQueue
            v-if="['hgs', 'fuel', 'fines'].includes(section)"
            :items="
              data.matching_queue.filter(
                (r) => r.kind === { hgs: 'hgs', fuel: 'fuel', fines: 'fine' }[section],
              )
            "
            :customers="data.customers"
            :role="role"
            @updated="load"
          />
          <section v-if="section === 'hgs'" class="sw-card sw-hgs-accounts">
            <h2>HGS Hesapları ve Etiketler</h2>
            <UiTable class="sw-table-scroll"
              ><table class="sw-table">
                <thead>
                  <tr>
                    <th>Plaka</th>
                    <th>HGS No</th>
                    <th>Müşteri</th>
                    <th>Bakiye</th>
                    <th>Durum</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="v in data.vehicles.filter((v) => v.hgs_no || v.hgs_active)"
                    :key="v.id"
                  >
                    <td>{{ v.plate }}</td>
                    <td>{{ v.hgs_no || 'Etiket tanımlanmamış' }}</td>
                    <td>{{ v.customer_name || 'Havuzda' }}</td>
                    <td>{{ money(v.hgs_balance) }}</td>
                    <td>
                      <span
                        class="sw-status"
                        :class="
                          num(v.hgs_balance) < num(data.settings.low_balance) ? 'red' : 'green'
                        "
                        >{{
                          num(v.hgs_balance) < num(data.settings.low_balance)
                            ? 'Düşük Bakiye'
                            : v.hgs_active
                              ? 'Aktif'
                              : 'Kapalı'
                        }}</span
                      >
                    </td>
                    <td>
                      <UiButton v-if="writeAllowed('hgs')" class="sw-button" @click="openHgs(v)"
                        >Bakiye / Etiket İşlemi</UiButton
                      ><router-link class="sw-button" :to="`${vehicleLink(v.id)}?tab=hgs`"
                        >Geçmiş</router-link
                      >
                    </td>
                  </tr>
                  <tr v-if="!data.vehicles.some((v) => v.hgs_no || v.hgs_active)">
                    <td colspan="6" class="sw-empty">Henüz HGS hesabı tanımlanmadı.</td>
                  </tr>
                </tbody>
              </table></UiTable
            >
          </section>
          <div class="sw-record-workspace" :class="{ 'with-detail': selected }">
            <section class="sw-list-column">
              <nav class="sw-status-tabs" aria-label="Kayıt durumları">
                <UiButton :class="{ active: !filters.status }" @click="filters.status = ''"
                  >Tümü <b>{{ rows.length }}</b></UiButton
                ><UiButton
                  v-for="status in rowStatuses"
                  :key="status"
                  :class="{ active: filters.status === status }"
                  @click="filters.status = status"
                  >{{ status }}
                  <b>{{ rows.filter((r) => r.status === status).length }}</b></UiButton
                >
              </nav>
              <form class="sw-card sw-filters" @submit.prevent="page = 1">
                <UiField class="sw-search-filter"
                  >Ara<input
                    v-model="filters.search"
                    type="search"
                    placeholder="Plaka, müşteri, kayıt no ara..." /></UiField
                ><UiField
                  >Durum<select v-model="filters.status">
                    <option value="">Tümü</option>
                    <option v-for="s in rowStatuses" :key="s">{{ s }}</option>
                  </select></UiField
                ><UiField
                  >Müşteri<select v-model="filters.customer">
                    <option value="">Tümü</option>
                    <option v-for="c in data.customers" :key="c.id" :value="String(c.id)">
                      {{ c.title }}
                    </option>
                  </select></UiField
                ><UiField>Başlangıç<input v-model="filters.start" type="date" /></UiField
                ><UiField>Bitiş<input v-model="filters.end" type="date" /></UiField
                ><UiButton class="sw-button primary">Filtrele</UiButton
                ><UiButton type="button" class="sw-button" @click="clearFilters">Temizle</UiButton>
              </form>
              <section class="sw-card sw-table-card">
                <UiTable class="sw-table-scroll"
                  ><table class="sw-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>
                          {{
                            section === 'customers'
                              ? 'Müşteri / Şirket'
                              : section === 'users'
                                ? 'Kullanıcı'
                                : 'Kayıt No'
                          }}
                        </th>
                        <th v-if="section !== 'users'">
                          {{ section === 'customers' ? 'Yetkili Kişi' : 'Araç / Plaka' }}
                        </th>
                        <th>
                          {{
                            section === 'users'
                              ? 'E-posta'
                              : section === 'customers'
                                ? 'Sektör / Şehir'
                                : 'Müşteri'
                          }}
                        </th>
                        <th>
                          {{
                            section === 'users'
                              ? 'Rol'
                              : section === 'customers'
                                ? 'Aktif / Toplam Araç'
                                : 'Tarih'
                          }}
                        </th>
                        <th v-if="section !== 'users'">
                          {{ section === 'customers' ? 'Kayıtlı Ciro' : 'Tutar' }}
                        </th>
                        <th v-for="column in extraColumns" :key="column.key">{{ column.label }}</th>
                        <th>Durum</th>
                        <th>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(row, index) in pagedRows"
                        :key="row.id"
                        :class="{ selected: selected?.id === row.id }"
                        tabindex="0"
                        @click="selectRow(row)"
                        @keydown.enter="selectRow(row)"
                      >
                        <td>{{ (page - 1) * pageSize + index + 1 }}</td>
                        <td>
                          <strong class="sw-number">{{ row.number || row.name }}</strong
                          ><small>{{ row.title || row.name }}</small>
                        </td>
                        <td v-if="section !== 'users'">
                          <strong>{{
                            section === 'customers' ? row.details.contact : row.plate || '—'
                          }}</strong
                          ><small>{{ row.vehicle_name }}</small>
                        </td>
                        <td>
                          {{
                            section === 'users'
                              ? row.email
                              : section === 'customers'
                                ? `${row.details.sector || '—'} / ${row.details.city || '—'}`
                                : row.customer_name || '—'
                          }}
                        </td>
                        <td>
                          {{
                            section === 'users'
                              ? roleLabels[row.role]
                              : section === 'customers'
                                ? `${row.active_vehicles} / ${row.vehicle_count}`
                                : dateText(row.date)
                          }}
                        </td>
                        <td v-if="section !== 'users'">{{ money(row.amount) }}</td>
                        <td v-for="column in extraColumns" :key="column.key">
                          {{ columnValue(row, column) }}
                        </td>
                        <td>
                          <span class="sw-status" :class="statusTone(row.status)">{{
                            row.status
                          }}</span>
                        </td>
                        <td>
                          <UiButton
                            class="sw-row-button"
                            :aria-label="`${row.number || row.name} detayını aç`"
                            @click.stop="selectRow(row)"
                            >•••</UiButton
                          >
                        </td>
                      </tr>
                      <tr v-if="!pagedRows.length">
                        <td :colspan="8 + extraColumns.length" class="sw-empty">
                          {{ loading ? 'Yükleniyor…' : 'Bu filtrelere uygun kayıt bulunamadı.'
                          }}<br /><UiButton
                            v-if="canCreate"
                            class="sw-button primary"
                            @click="openCreate"
                            >{{ cfg.create }}</UiButton
                          >
                        </td>
                      </tr>
                    </tbody>
                  </table></UiTable
                >
                <footer class="sw-table-footer">
                  <span
                    >Toplam {{ filteredRows.length }} kayıttan
                    {{ filteredRows.length ? (page - 1) * pageSize + 1 : 0 }}–{{
                      Math.min(page * pageSize, filteredRows.length)
                    }}
                    görüntüleniyor</span
                  >
                  <div>
                    <UiButton :disabled="page === 1" @click="page--">‹</UiButton
                    ><span>{{ page }} / {{ totalPages }}</span
                    ><UiButton :disabled="page === totalPages" @click="page++">›</UiButton
                    ><select v-model.number="pageSize" aria-label="Sayfa başına kayıt">
                      <option :value="10">10</option>
                      <option :value="25">25</option>
                      <option :value="50">50</option>
                    </select>
                  </div>
                </footer>
              </section>
            </section>
            <aside
              v-if="selected"
              class="sw-card sw-detail-panel"
              aria-label="Seçilen kayıt detayı"
            >
              <div class="sw-detail-title">
                <h2>{{ selected.number || selected.name }}</h2>
                <span class="sw-status" :class="statusTone(selected.status)">{{
                  selected.status
                }}</span
                ><UiButton
                  class="sw-row-button"
                  aria-label="Detay panelini kapat"
                  @click="selected = null"
                  >×</UiButton
                >
              </div>
              <img
                v-if="selectedPhoto"
                class="sw-detail-photo"
                :src="selectedPhoto.url"
                :alt="selected.vehicle_name || selected.plate"
              />
              <div v-if="selected.plate" class="sw-detail-vehicle">
                <strong>{{ selected.plate }}</strong
                ><small>{{ selected.vehicle_name }}</small
                ><router-link :to="vehicleLink(selected.vehicle_id)"
                  >Araç Detayını Gör →</router-link
                >
              </div>
              <nav class="sw-detail-tabs">
                <UiButton
                  v-for="tab in ['Genel', 'İlişkiler', 'Belgeler', 'Geçmiş']"
                  :key="tab"
                  :class="{ active: detailTab === tab }"
                  @click="detailTab = tab"
                  >{{ tab }}</UiButton
                >
              </nav>
              <template v-if="detailTab === 'Genel'"
                ><SupplierSignedDocument
                  v-if="
                    selected.source === 'operation' &&
                    ['contract', 'delivery'].includes(selected.kind)
                  "
                  :operation="selected"
                  :role="role"
                  @updated="load"
                />
                <h3>{{ selected.title || selected.name }}</h3>
                <dl class="sw-details">
                  <div v-for="item in selectedInfo" :key="item.label">
                    <dt>{{ item.label }}</dt>
                    <dd>{{ item.value }}</dd>
                  </div>
                </dl>
                <div v-if="selected.source === 'customer'" class="sw-detail-metrics">
                  <div>
                    <small>Aktif Araç</small><strong>{{ selected.active_vehicles }}</strong>
                  </div>
                  <div>
                    <small>Toplam Araç</small><strong>{{ selected.vehicle_count }}</strong>
                  </div>
                </div>
                <section v-if="selected.kind === 'delivery'" class="sw-check-preview">
                  <h3>Teslimat Kontrol Listesi</h3>
                  <p v-for="[key, label] in deliveryChecks" :key="key">
                    {{ selected.details.checks?.[key] ? '✓' : '○' }} {{ label }}
                  </p>
                </section>
                <div class="sw-detail-actions">
                  <UiButton v-if="canEditSelected" class="sw-button" @click="openEdit"
                    >✎ Düzenle</UiButton
                  ><UiButton
                    v-for="action in permittedActions"
                    :key="action"
                    class="sw-button"
                    :class="action === 'İptal' || action === 'Reddedildi' ? 'danger' : 'primary'"
                    :disabled="saving"
                    @click="transition(action)"
                    >{{ actionLabel(action) }}</UiButton
                  ><UiButton
                    v-if="
                      selected.kind === 'offer' &&
                      selected.raw_status === 'Onaylandı' &&
                      writeAllowed('contract')
                    "
                    class="sw-button primary"
                    @click="convertRecord('contract')"
                    >Sözleşme Oluştur</UiButton
                  ><UiButton
                    v-if="
                      selected.kind === 'contract' &&
                      selected.raw_status === 'Aktif' &&
                      writeAllowed('delivery')
                    "
                    class="sw-button primary"
                    @click="convertRecord('delivery')"
                    >Teslimat Planla</UiButton
                  ><UiButton
                    v-if="
                      ((selected.kind === 'contract' && selected.raw_status === 'Aktif') ||
                        (selected.kind === 'sale' && selected.raw_status === 'Satıldı') ||
                        (selected.kind === 'return' && selected.raw_status === 'Tamamlandı')) &&
                      writeAllowed('invoice')
                    "
                    class="sw-button"
                    @click="convertRecord('invoice')"
                    >Fatura Oluştur</UiButton
                  ><UiButton
                    v-if="
                      ['fine', 'fuel', 'hgs'].includes(selected.kind) &&
                      ['owner', 'finance'].includes(role) &&
                      !(selected.kind === 'hgs' && selected.details.type !== 'Geçiş')
                    "
                    class="sw-button"
                    @click="reflectCost"
                    >Müşteriye Yansıtma Faturası</UiButton
                  ><UiButton
                    v-if="
                      selected.kind === 'invoice' &&
                      selected.balance > 0 &&
                      ['Kesildi', 'Kısmen Ödendi'].includes(selected.raw_status) &&
                      writeAllowed('payment')
                    "
                    class="sw-button primary"
                    @click="openPayment"
                    >{{
                      selected.details.direction === 'gelir' ? 'Tahsilat' : 'Ödeme'
                    }}
                    Kaydet</UiButton
                  ><UiButton
                    v-if="
                      selected.source === 'operation' &&
                      writeAllowed(selected.kind) &&
                      !['approval', 'payment', 'scenario'].includes(selected.kind) &&
                      !['İptal', 'Sona Erdi', 'Ödendi', 'Tamamlandı'].includes(selected.raw_status)
                    "
                    class="sw-button"
                    @click="requestApproval"
                    >Onay İste</UiButton
                  ><UiButton
                    v-if="section === 'users' && role === 'owner'"
                    class="sw-button"
                    @click="toggleUser"
                    >{{
                      selected.is_active ? 'Kullanıcıyı Pasife Al' : 'Kullanıcıyı Etkinleştir'
                    }}</UiButton
                  ><UiButton class="sw-button" @click="printSelected">Yazdır / PDF</UiButton>
                </div></template
              >
              <template v-else-if="detailTab === 'İlişkiler'"
                ><router-link
                  v-if="selected.source === 'rental'"
                  :to="`/supplier-portal/contracts?record=${selected.parent_id}`"
                  class="sw-related"
                  >Bağlı Sözleşmeyi Gör</router-link
                ><router-link
                  v-for="r in relatedRecords"
                  :key="r.id"
                  :to="recordLink(r)"
                  class="sw-related"
                  ><strong>{{ r.number }}</strong
                  ><span>{{ r.title }} · {{ r.status }}</span></router-link
                ><router-link
                  v-for="v in relatedVehicles"
                  :key="v.id"
                  :to="vehicleLink(v.id)"
                  class="sw-related"
                  ><strong>{{ v.plate }}</strong
                  ><span>{{ v.brand }} {{ v.model }}</span></router-link
                >
                <p v-if="!relatedRecords.length && !relatedVehicles.length" class="sw-empty">
                  Bağlı kayıt yok.
                </p></template
              >
              <template v-else-if="detailTab === 'Belgeler'"
                ><a
                  v-for="file in selectedFiles"
                  :key="file.id"
                  :href="file.url"
                  target="_blank"
                  rel="noopener"
                  class="sw-related"
                  ><strong>{{ file.original_name }}</strong
                  ><span
                    >{{ file.document_type || file.category }} ·
                    {{ dateText(file.uploaded_at) }}</span
                  ></a
                >
                <p v-if="!selectedFiles.length" class="sw-empty">Bağlı araç belgesi yok.</p>
                <router-link
                  v-if="selected.vehicle_id"
                  :to="`${vehicleLink(selected.vehicle_id)}?tab=documents`"
                  class="sw-button primary"
                  >Araç Belgesi Ekle</router-link
                ></template
              >
              <template v-else
                ><div
                  v-for="version in selectedVersions"
                  :key="`version-${version.version}`"
                  class="sw-event-row"
                >
                  <div>
                    <strong
                      >Teklif Sürümü {{ version.version }} · {{ version.snapshot.status }}</strong
                    ><small
                      >{{ money(version.snapshot.amount) }} ·
                      {{ version.snapshot.details.quantity || 1 }} araç ·
                      {{ version.snapshot.details.months }} ay ·
                      {{ dateText(version.created_at) }}</small
                    >
                  </div>
                </div>
                <div v-for="event in selectedEvents" :key="event.id" class="sw-event-row">
                  <span>●</span>
                  <div>
                    <strong>{{ event.title }}</strong
                    ><small>{{ event.actor }} · {{ dateText(event.date) }}</small>
                  </div>
                </div>
                <p v-if="!selectedEvents.length" class="sw-empty">
                  Bu kayıt için işlem geçmişi yok.
                </p></template
              >
            </aside>
          </div>
        </template>
      </template>
    </main>
  </div>

  <UiModal
    :busy="saving"
    v-if="conversion"
    class="sw-modal-overlay"
    @close="!saving && (conversion = null)"
  >
    <section
      class="sw-form-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sw-convert-title"
    >
      <h2 id="sw-convert-title">Tekliften Sözleşme Oluştur</h2>
      <p class="sw-muted">
        Teklifteki tüm araçları tek sözleşmeye bağlayın. Her araç için ayrı kiralama, teslim ve iade
        kaydı tutulur.
      </p>
      <form @submit.prevent="confirmConversion">
        <UiField v-if="conversion.quantity > 1"
          >Sözleşme Araçları<select
            aria-label="Sözleşme Araçları"
            v-model="conversionVehicles"
            multiple
            required
          >
            <option
              v-for="v in data.vehicles.filter((v) => v.is_active && !v.customer_id)"
              :key="v.id"
              :value="v.id"
            >
              {{ v.plate }} · {{ v.brand }} {{ v.model }}
            </option></select
          ><small
            >{{ conversionVehicles.length }} / {{ conversion.quantity }} araç seçildi</small
          ></UiField
        ><UiField v-else
          >Araç<select aria-label="Araç" v-model="conversionVehicle" required>
            <option value="">Araç seçin</option>
            <option v-for="v in data.vehicles.filter((v) => v.is_active)" :key="v.id" :value="v.id">
              {{ v.plate }} · {{ v.brand }} {{ v.model }}
            </option>
          </select></UiField
        >
        <p v-if="error" class="sw-alert error">{{ error }}</p>
        <footer>
          <UiButton type="button" class="sw-button" :disabled="saving" @click="conversion = null"
            >Vazgeç</UiButton
          ><UiButton class="sw-button primary" :disabled="saving">Sözleşme Oluştur</UiButton>
        </footer>
      </form>
    </section>
  </UiModal>
  <UiModal
    :busy="saving"
    v-if="showForm"
    class="sw-modal-overlay"
    @close="!saving && (showForm = false)"
  >
    <section
      class="sw-form-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sw-form-title"
      @keydown.esc="!saving && (showForm = false)"
    >
      <header>
        <h2 id="sw-form-title">
          {{ editing ? 'Kaydı Düzenle' : modalCfg.create || modalCfg.label }}
        </h2>
        <UiButton
          class="sw-row-button"
          aria-label="Formu kapat"
          :disabled="saving"
          @click="showForm = false"
          >×</UiButton
        >
      </header>
      <UiAlert v-if="formError" class="sw-alert error" as="p" tone="error">{{ formError }}</UiAlert>
      <form @submit.prevent="saveForm">
        <template v-if="modalSection === 'customers'"
          ><UiField v-if="!editing"
            >Mevcut Müşteriyi Bağla<select
              aria-label="Müşteri"
              v-model="form.customer_id"
              @change="syncDirectory"
            >
              <option value="">Yeni müşteri oluştur</option>
              <option v-for="c in directory" :key="c.id" :value="String(c.id)">
                {{ c.company_name }}
              </option>
            </select></UiField
          ><UiField
            >Firma Adı<input
              v-model="form.title"
              required
              :disabled="Boolean(editing || form.customer_id)"
          /></UiField>
          <div class="sw-form-grid">
            <UiField
              >E-posta<input
                v-model="form.email"
                type="email"
                :disabled="Boolean(editing || form.customer_id)" /></UiField
            ><UiField
              >Telefon<input v-model="form.phone" :disabled="Boolean(editing || form.customer_id)"
            /></UiField>
          </div>
          <UiField
            >Adres<input
              v-model="form.address"
              :disabled="Boolean(editing || form.customer_id)" /></UiField
        ></template>
        <template v-else-if="modalSection === 'users'"
          ><UiField>Ad Soyad<input v-model="form.title" required /></UiField
          ><UiField
            >E-posta<input
              v-model="form.email"
              type="email"
              required
              :disabled="Boolean(editing)"
              autocomplete="off" /></UiField
          ><UiField
            >{{ editing ? 'Yeni Şifre (İsteğe Bağlı)' : 'Şifre'
            }}<input
              v-model="form.password"
              type="password"
              minlength="10"
              :required="!editing"
              autocomplete="new-password" /></UiField
          ><UiField
            >Rol<select v-model="form.role">
              <option value="fleet_manager">Filo Yöneticisi</option>
              <option value="sales">Satış</option>
              <option value="delivery">Teslim &amp; İade</option>
              <option value="operations">Operasyon</option>
              <option value="finance">Finans</option>
              <option value="viewer">Görüntüleyici</option>
            </select></UiField
          ></template
        >
        <template v-else
          ><UiField
            >Başlık / Açıklama<input v-model="form.title" required maxlength="200"
          /></UiField>
          <div class="sw-form-grid">
            <UiField v-if="modalCfg.customer || modalCfg.optionalCustomer"
              >Müşteri<select
                aria-label="Müşteri"
                v-model="form.customer_id"
                :required="Boolean(modalCfg.customer)"
              >
                <option value="">Müşteri seçin</option>
                <option v-for="c in data.customers" :key="c.id" :value="String(c.id)">
                  {{ c.title }}
                </option>
              </select></UiField
            ><UiField
              v-if="modalCfg.vehicle || modalCfg.optionalVehicle || modalCfg.kind === 'offer'"
              >Araç<select aria-label="Araç" v-model="form.vehicle_id" :required="modalCfg.vehicle">
                <option value="">
                  {{ modalCfg.vehicle ? 'Araç seçin' : 'Araç seçimi isteğe bağlı' }}
                </option>
                <option
                  v-for="v in data.vehicles.filter((v) => v.is_active)"
                  :key="v.id"
                  :value="v.id"
                >
                  {{ v.plate }} · {{ v.brand }} {{ v.model }}
                </option>
              </select></UiField
            ><UiField v-if="modalCfg.parentKind"
              >Bağlı {{ modalCfg.parentKind === 'invoice' ? 'Fatura' : 'Sözleşme'
              }}<select
                :aria-label="modalCfg.parentKind === 'invoice' ? 'Bağlı Fatura' : 'Bağlı Sözleşme'"
                v-model="form.parent_id"
                :required="modalCfg.parentRequired !== false"
                :disabled="Boolean(editing)"
                @change="syncParent"
              >
                <option value="">Kayıt seçin</option>
                <option v-for="r in parentOptions" :key="r.id" :value="String(r.id)">
                  {{ r.number }} · {{ r.customer_name }}
                </option>
              </select></UiField
            ><UiField
              >{{
                modalCfg.kind === 'delivery'
                  ? 'Planlanan Teslim Tarihi'
                  : 'Başlangıç / Kayıt Tarihi'
              }}<input
                :aria-label="
                  modalCfg.kind === 'delivery'
                    ? 'Planlanan Teslim Tarihi'
                    : 'Başlangıç / Kayıt Tarihi'
                "
                v-model="form.date"
                type="date"
                required /></UiField
            ><UiField v-if="modalCfg.endLabel"
              >{{ modalCfg.endLabel
              }}<input
                :aria-label="modalCfg.endLabel"
                v-model="form.end_date"
                type="date"
                :required="modalCfg.endRequired"
                :min="form.date" /></UiField
            ><UiField v-if="modalCfg.amountLabel"
              >{{ modalCfg.amountLabel
              }}<input
                :aria-label="modalCfg.amountLabel"
                v-model.number="form.amount"
                type="number"
                min="0"
                step="0.01"
                required
            /></UiField></div
        ></template>
        <div class="sw-form-grid">
          <UiField
            v-for="field in modalCfg.fields || []"
            :key="field.key"
            :class="{
              wide: field.type === 'textarea',
              'sw-checkbox-field': field.type === 'checkbox',
            }"
            >{{ field.label
            }}<select
              v-if="field.type === 'select'"
              :aria-label="field.label"
              v-model="form.details[field.key]"
              @change="field.key === 'source_reference' && syncCostSource()"
              :required="field.required"
            >
              <option v-if="!field.required" value="">Seçin / Yok</option>
              <option
                v-for="option in fieldOptions(field)"
                :key="typeof option === 'object' ? option.value : option"
                :value="typeof option === 'object' ? option.value : option"
              >
                {{ typeof option === 'object' ? option.label : option }}
              </option></select
            ><textarea
              v-else-if="field.type === 'textarea'"
              :aria-label="field.label"
              v-model="form.details[field.key]"
              :required="field.required"
              rows="3" /><input
              v-else-if="field.type === 'checkbox'"
              :aria-label="field.label"
              v-model="form.details[field.key]"
              type="checkbox" /><input
              v-else
              @input="syncInvoiceTax(field.key)"
              :aria-label="field.label"
              v-model="form.details[field.key]"
              :type="field.type || 'text'"
              :min="field.min"
              :step="field.step || (field.type === 'number' ? '1' : undefined)"
              :required="field.required"
          /></UiField>
        </div>
        <fieldset v-if="modalCfg.checks" class="sw-delivery-checks">
          <legend>
            {{ modalCfg.kind === 'return' ? 'İade Kontrol Listesi' : 'Teslimat Kontrol Listesi' }}
          </legend>
          <UiField v-for="[key, label] in deliveryChecks" :key="key"
            ><input v-model="form.details.checks[key]" type="checkbox" />{{ label }}</UiField
          >
        </fieldset>
        <p v-if="modalCfg.kind === 'invoice'" class="sw-muted">
          Bu kayıt e-Fatura sistemine gönderilmez. Gerçek kesilmiş faturayı Kesildi durumuna alın.
        </p>
        <p v-if="modalSection === 'users'" class="sw-muted">
          Kullanıcı bu e-posta ve şifreyle tedarikçi girişini kullanır. E-posta gönderilmez.
        </p>
        <footer>
          <UiButton type="button" class="sw-button" :disabled="saving" @click="showForm = false"
            >Vazgeç</UiButton
          ><UiButton class="sw-button primary" :disabled="saving">{{
            saving ? 'Kaydediliyor…' : 'Kaydet'
          }}</UiButton>
        </footer>
      </form>
    </section>
  </UiModal>
</template>

<script setup>
import { usePagination } from '../composables/usePagination.js'

import { formatMoney, formatDate } from '../utils/formatters.js'
import { downloadApi } from '../utils/downloads.js'

import { UiAlert, UiButton, UiField, UiModal, UiTable } from '../components/ui/index.js'

import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import ResponsibilityQueue from '../components/ResponsibilityQueue.vue'
import SupplierSignedDocument from '../components/SupplierSignedDocument.vue'
import SupplierIntegrations from '../components/SupplierIntegrations.vue'
import SupplierFleetPlanning from '../components/SupplierFleetPlanning.vue'
import { supplierApi, downloadSupplierCsv } from '../utils/supplierApi'
import { supplierModules, roleLabels } from '../utils/supplierModules'
import { analyzeSupplier, detectSupplierFindings, num } from '../utils/supplierAnalytics'
const route = useRoute(),
  router = useRouter(),
  data = ref(null),
  loading = ref(false),
  saving = ref(false),
  error = ref(''),
  unauthorized = ref(false),
  notice = ref('')
const section = computed(() => route.params.section || 'home'),
  cfg = computed(() => supplierModules[section.value] || supplierModules.home)
const companyName = localStorage.getItem('fleetcar_supplier_name') || 'Tedarikçi'
const currentDate = new Date().toLocaleDateString('tr-TR', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})
const initials = computed(() =>
  (data.value?.session?.name || companyName)
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0])
    .join('')
    .toUpperCase(),
)
const role = computed(() => data.value?.session?.role || 'viewer')
const settingsTab = ref('general')
const reportTab = ref('Genel Bakış'),
  reportCatalog = ref([]),
  serverReportKey = ref('fleet'),
  serverReport = ref(null),
  reportFilters = reactive({ brand: '', model: '', group: '', contract: '' })
const globalSearch = ref(''),
  filters = reactive({
    search: String(route.query.search || ''),
    status: '',
    customer: '',
    vehicle: '',
    start: '',
    end: '',
  })
const page = ref(1),
  pageSize = ref(10),
  selected = ref(null),
  detailTab = ref('Genel'),
  selectedEvents = ref([]),
  selectedVersions = ref([]),
  settingsForm = reactive({})
const showForm = ref(false),
  conversion = ref(null),
  conversionVehicle = ref(''),
  conversionVehicles = ref([]),
  modalSection = ref(''),
  editing = ref(null),
  formError = ref(''),
  directory = ref([])
const form = reactive({
  title: '',
  customer_id: '',
  vehicle_id: '',
  parent_id: '',
  date: '',
  end_date: '',
  amount: 0,
  details: {},
  email: '',
  phone: '',
  address: '',
  password: '',
  role: 'viewer',
})
const colors = ['#0064ff', '#13b785', '#ffa92e', '#8879db', '#a5aec0', '#f15d7d']
const deliveryChecks = [
  ['exterior', 'Araç dış kontrolü'],
  ['interior', 'Araç iç kontrolü'],
  ['documents', 'Belgeler teslim edildi'],
  ['equipment', 'Aksesuar ve ekipman kontrolü'],
]
const money = (value) => formatMoney(num(value))
const dateText = formatDate
const daysUntil = (value) =>
  Math.ceil(
    (new Date(String(value).slice(0, 10) + 'T00:00:00') - new Date(new Date().toDateString())) /
      86400000,
  )
const vehicleLink = (id) => `/supplier-portal/vehicles/${encodeURIComponent(id)}`
const kindSection = (kind) =>
  Object.keys(supplierModules).find(
    (k) => supplierModules[k].kind === kind && !supplierModules[k].readonly,
  ) ||
  { payment: 'accounting', approval: 'approvals' }[kind] ||
  kind
const recordLink = (r) =>
  r.source === 'vehicle'
    ? vehicleLink(r.vehicle_id)
    : `/supplier-portal/${kindSection(r.kind)}?record=${encodeURIComponent(r.id)}`
const analytics = computed(() =>
  analyzeSupplier(data.value || {}, section.value === 'reports' ? filters : {}),
)
const findings = computed(() => detectSupplierFindings(data.value || {}, analytics.value))
const reportTabs = [
  'Genel Bakış',
  'Araç Kullanımı',
  'Finansal Raporlar',
  'Müşteri Raporları',
  'Operasyon Raporları',
  'HGS & Yakıt',
  'Servis & Bakım',
  'Hasar & Kaza',
  'TPC Raporları',
  'Sözleşme Raporları',
]
const reportRows = computed(() => {
  const ledger = [...analytics.value.revenue, ...analytics.value.costs]
  const categories = {
    'HGS & Yakıt': ['HGS', 'Yakıt'],
    'Servis & Bakım': ['Servis'],
    'Hasar & Kaza': ['Hasar'],
    'TPC Raporları': ['TPC'],
  }[reportTab.value]
  if (categories) return ledger.filter((r) => categories.includes(r.category))
  if (reportTab.value === 'Sözleşme Raporları')
    return analytics.value.records
      .filter((r) => r.kind === 'contract')
      .map((r) => ({ ...r, category: 'Sözleşme — Aylık Kira' }))
  if (reportTab.value === 'Operasyon Raporları')
    return (data.value?.service || [])
      .filter(
        (r) =>
          (!filters.customer || String(r.customer_id) === filters.customer) &&
          (!filters.vehicle || r.vehicle_id === filters.vehicle) &&
          (!filters.start || String(r.date).slice(0, 10) >= filters.start) &&
          (!filters.end || String(r.date).slice(0, 10) <= filters.end),
      )
      .map((r) => ({ ...r, category: r.status }))
  return ledger
})
const highCostVehicles = computed(() =>
  Object.values(
    analytics.value.costs
      .filter((r) => r.vehicle_id)
      .reduce((acc, r) => {
        acc[r.vehicle_id] ??= { id: r.vehicle_id, plate: r.plate, amount: 0 }
        acc[r.vehicle_id].amount += num(r.amount)
        return acc
      }, {}),
  ).sort((a, b) => b.amount - a.amount),
)
function categoryMonths(category) {
  const totals = {}
  for (const r of analytics.value.costs.filter((r) => r.category === category)) {
    const key = String(r.date).slice(0, 7)
    totals[key] = (totals[key] || 0) + num(r.amount)
  }
  return Object.entries(totals)
    .sort()
    .map(([key, amount]) => ({ key, amount }))
}
function usageHours(vid) {
  const records = (data.value?.usage || []).filter(
    (r) =>
      r.vehicle_id === vid &&
      (!filters.start || r.ended_at.slice(0, 10) >= filters.start) &&
      (!filters.end || r.started_at.slice(0, 10) <= filters.end),
  )
  if (!records.length) return null
  return records
    .reduce((sum, r) => {
      const start = Math.max(
        new Date(r.started_at).getTime(),
        filters.start ? new Date(filters.start + 'T00:00:00').getTime() : -Infinity,
      )
      const end = Math.min(
        new Date(r.ended_at).getTime(),
        filters.end ? new Date(filters.end + 'T23:59:59').getTime() : Infinity,
      )
      return sum + Math.max(0, end - start) / 3600000
    }, 0)
    .toFixed(1)
}
const maxMonthly = computed(() =>
  Math.max(1, ...analytics.value.monthly.flatMap((m) => [m.revenue, m.cost])),
)
const locatedCars = computed(() =>
  analytics.value.cars.filter((v) => v.gps_latitude != null && v.gps_longitude != null),
)
const mapUrl = computed(() => {
  const v = locatedCars.value[0]
  if (!v) return ''
  const lat = num(v.gps_latitude),
    lon = num(v.gps_longitude)
  return `https://www.openstreetmap.org/export/embed.html?bbox=${[lon - 0.04, lat - 0.03, lon + 0.04, lat + 0.03].join(',')}&layer=mapnik&marker=${lat},${lon}`
})
const endingContracts = computed(() =>
  analytics.value.records
    .filter(
      (r) =>
        r.kind === 'contract' &&
        (r.raw_status === 'Aktif' || (r.source === 'vehicle' && r.status === 'Aktif')) &&
        r.end_date &&
        daysUntil(r.end_date) >= 0 &&
        daysUntil(r.end_date) <= 90,
    )
    .sort((a, b) => a.end_date.localeCompare(b.end_date)),
)
const currentMonthlyRent = computed(() =>
  analytics.value.cars
    .filter((v) => v.is_active && v.customer_id)
    .reduce((sum, v) => sum + num(v.monthly_rent), 0),
)
const pendingApprovals = computed(
  () =>
    data.value?.records.filter((r) => r.kind === 'approval' && r.status === 'Beklemede').length ||
    0,
)
const dueServiceCars = computed(() =>
  analytics.value.cars.filter(
    (v) =>
      v.is_active &&
      ((v.next_service_due_date && daysUntil(v.next_service_due_date) <= 30) ||
        (v.next_service_due_km != null && num(v.next_service_due_km) - num(v.mileage) <= 3000)),
  ),
)
const rows = computed(() => {
  if (!data.value) return []
  if (section.value === 'rentals') return data.value.rentals || []
  if (section.value === 'customers') return data.value.customers
  if (section.value === 'users')
    return (data.value.users || []).map((u) => ({
      ...u,
      status: u.is_active ? 'Aktif' : 'Pasif',
      source: 'user',
    }))
  if (cfg.value.shared)
    return section.value === 'fuel'
      ? (data.value.fuel || []).filter((r) => r.details.kind === 'Yakıt')
      : data.value[section.value] || []
  return data.value.records.filter((r) => r.kind === cfg.value.kind)
})
const extraColumns = computed(
  () =>
    ({
      offers: [
        { key: 'details.quantity', label: 'Adet' },
        { key: 'details.months', label: 'Ay' },
        { key: 'end_date', label: 'Geçerlilik', type: 'date' },
      ],
      contracts: [
        { key: 'end_date', label: 'Bitiş', type: 'date' },
        { key: 'details.months', label: 'Ay' },
      ],
      rentals: [{ key: 'end_date', label: 'Bitiş', type: 'date' }],
      policies: [
        { key: 'details.policy_type', label: 'Tür' },
        { key: 'details.insurer', label: 'Sigortacı' },
        { key: 'end_date', label: 'Bitiş', type: 'date' },
      ],
      fuel: [
        { key: 'details.liters', label: 'Litre' },
        { key: 'details.mileage', label: 'Km' },
        { key: 'details.station', label: 'İstasyon' },
      ],
      hgs: [
        { key: 'details.type', label: 'Tür' },
        { key: 'details.balance', label: 'Bakiye', type: 'money' },
      ],
      tire: [
        { key: 'details.remaining_km', label: 'Kalan Km' },
        { key: 'details.tread_depth_mm', label: 'Diş (mm)' },
      ],
      invoices: [
        { key: 'end_date', label: 'Vade', type: 'date' },
        { key: 'balance', label: 'Açık Bakiye', type: 'money' },
      ],
      fines: [{ key: 'end_date', label: 'Son Ödeme', type: 'date' }],
      deliveries: [{ key: 'details.receiver', label: 'Teslim Alan' }],
    })[section.value] || [],
)
function columnValue(row, column) {
  const value = column.key.split('.').reduce((o, k) => o?.[k], row)
  return column.type === 'date'
    ? dateText(value)
    : column.type === 'money'
      ? money(value)
      : (value ?? '—')
}
const rowStatuses = computed(() => [...new Set(rows.value.map((r) => r.status))])
const filteredRows = computed(() =>
  rows.value.filter((r) => {
    const text = JSON.stringify([
      r.number,
      r.title,
      r.name,
      r.plate,
      r.customer_name,
      r.vehicle_name,
      r.email,
      r.details,
    ]).toLocaleLowerCase('tr-TR')
    return (
      (!filters.search || text.includes(filters.search.trim().toLocaleLowerCase('tr-TR'))) &&
      (!filters.status || r.status === filters.status) &&
      (!filters.customer || String(r.customer_id) === filters.customer) &&
      (!filters.start || String(r.date || '').slice(0, 10) >= filters.start) &&
      (!filters.end || String(r.date || '').slice(0, 10) <= filters.end)
    )
  }),
)
const { totalPages, pageItems: pagedRows } = usePagination(filteredRows, { page, pageSize })
watch(
  [filters, pageSize],
  () => {
    page.value = 1
  },
  { deep: true },
)
function writeAllowed(kind) {
  const grants = data.value?.session?.capabilities?.write || []
  return grants.includes('*') || grants.includes(kind)
}

const canCreate = computed(() =>
  Boolean(cfg.value.create && !cfg.value.readonly && writeAllowed(cfg.value.kind || section.value)),
)
const permittedActions = computed(() =>
  selected.value && writeAllowed(selected.value.kind)
    ? (selected.value.actions || []).filter(
        (s) =>
          !(
            selected.value.kind === 'return' &&
            s === 'Tamamlandı' &&
            !['owner', 'finance'].includes(role.value)
          ),
      )
    : [],
)
const canEditSelected = computed(() => {
  const r = selected.value
  if (!r) return false
  if (r.source === 'customer') return writeAllowed('customer')
  if (r.source === 'user') return role.value === 'owner'
  return (
    r.source === 'operation' &&
    writeAllowed(r.kind) &&
    ((['offer', 'contract', 'invoice'].includes(r.kind) && r.raw_status === 'Taslak') ||
      (r.kind === 'offer' && r.raw_status === 'Revizyon Bekliyor') ||
      (r.kind === 'maintenance' && r.raw_status === 'Önerildi') ||
      (r.kind === 'sale' &&
        ['Hazırlık', 'Ekspertizde', 'İlanda', 'Teklif Alındı'].includes(r.raw_status)) ||
      (r.kind === 'return' &&
        ['Planlandı', 'İnceleniyor', 'Mutabakat Bekliyor'].includes(r.raw_status)) ||
      (r.kind === 'delivery' && r.raw_status === 'Planlandı') ||
      (r.kind === 'damage' && r.raw_status === 'Bildirildi') ||
      (r.kind === 'policy' && ['Taslak', 'Aktif'].includes(r.raw_status)) ||
      r.kind === 'scenario')
  )
})
const modalCfg = computed(() =>
  modalSection.value === 'payment'
    ? {
        label: 'Tahsilat / Ödeme',
        create: 'Tahsilat / Ödeme Kaydet',
        kind: 'payment',
        customer: true,
        parentKind: 'invoice',
        amountLabel: 'Ödeme Tutarı (TL)',
        fields: [
          { key: 'method', label: 'Ödeme Yöntemi' },
          { key: 'notes', label: 'Notlar', type: 'textarea' },
        ],
      }
    : supplierModules[modalSection.value] || {},
)
const parentOptions = computed(
  () =>
    data.value?.records.filter(
      (r) =>
        r.source === 'operation' &&
        r.kind === modalCfg.value.parentKind &&
        (r.kind === 'contract'
          ? r.raw_status === 'Aktif' ||
            (modalCfg.value.kind === 'invoice' && r.raw_status === 'Sona Erdi')
          : ['Kesildi', 'Kısmen Ödendi'].includes(r.raw_status)),
    ) || [],
)
const selectedFiles = computed(
  () => data.value?.files.filter((f) => f.vehicle_id === selected.value?.vehicle_id) || [],
)
const selectedPhoto = computed(() => selectedFiles.value.find((f) => f.category === 'photo'))
const relatedRecords = computed(
  () =>
    data.value?.records.filter(
      (r) =>
        r.id !== selected.value?.id &&
        (r.parent_id === selected.value?.id ||
          r.id === selected.value?.parent_id ||
          (selected.value?.source === 'customer' && r.customer_id === selected.value.id)),
    ) || [],
)
const relatedVehicles = computed(() =>
  selected.value?.source === 'customer'
    ? data.value.vehicles.filter((v) => v.customer_id === selected.value.id)
    : data.value?.vehicles.filter((v) =>
        (selected.value?.details?.vehicle_ids || []).includes(v.id),
      ) || [],
)
const selectedInfo = computed(() => {
  const r = selected.value
  if (!r) return []
  const entries = [
    ['Müşteri', r.customer_name],
    ['Araç', r.plate],
    ['Başlangıç / Kayıt', dateText(r.date)],
    [
      r.kind === 'offer'
        ? 'Teklif Geçerliliği'
        : r.kind === 'invoice'
          ? 'Fatura Vadesi'
          : 'Bitiş Tarihi',
      ['offer', 'contract', 'policy', 'invoice', 'fine'].includes(r.kind)
        ? dateText(r.end_date)
        : null,
    ],
    [
      'Tutar',
      [
        'offer',
        'contract',
        'policy',
        'damage',
        'fine',
        'invoice',
        'payment',
        'fuel',
        'hgs',
      ].includes(r.kind)
        ? money(r.amount)
        : null,
    ],
    ['Ödenen', r.kind === 'invoice' ? money(r.paid) : null],
    ['Açık Bakiye', r.balance != null ? money(r.balance) : null],
    [
      'Kaynak',
      r.source === 'operation'
        ? 'İşlem Kaydı'
        : r.source === 'vehicle'
          ? 'Ortak Araç Kaydı'
          : {
              customer: 'Müşteri',
              user: 'Kullanıcı',
              fuel: 'Yakıt / Gider Kaydı',
              hgs: 'HGS Hareketi',
              service: 'Servis Talebi',
              tire: 'Lastik Kaydı',
            }[r.source] || r.source,
    ],
  ]
  const localFields =
    (r.source === 'customer' ? supplierModules.customers : supplierModules[kindSection(r.kind)])
      ?.fields || []
  if (r.source === 'user')
    entries.push(
      ['E-posta', r.email],
      ['Rol', roleLabels[r.role]],
      ['Hesap', r.is_active ? 'Aktif' : 'Pasif'],
    )
  const commonLabels = {
    responsibility_status: 'Sorumluluk Eşleştirmesi',
    responsibility_reason: 'Mali Eşleştirme Gerekçesi',
    rental_id: 'Kiralama Kaydı',
    reflection_reference: 'Yansıtılan Olay',
    billing_period: 'Fatura Dönemi',
    driven_km: 'Kullanılan Km',
    contract_km_limit: 'Dönem Km Limiti',
    excess_km: 'Fazla Km',
    excess_km_charge: 'Fazla Km Bedeli',
    settlement_total: 'Son Mutabakat Tutarı',
    settled_at: 'Mutabakat Tarihi',
    settled_by: 'Mutabakat Onaylayan',
    delivery_reference: 'Teslim Durum Referansı',
    condition_reference: 'Teslim Durum Referansı',
    delivery_id: 'Teslimat Kaydı',
    return_id: 'İade Kaydı',
    delivered_at: 'Gerçek Teslim Zamanı',
    returned_at: 'Gerçek İade Zamanı',
    acceptance_source: 'Karar Kaynağı',
    customer_decision: 'Müşteri Kararı',
    customer_decision_note: 'Müşteri Revizyon Açıklaması',
    customer_decision_at: 'Müşteri Karar Zamanı',
    customer_decision_version: 'Karar Verilen Sürüm',
    accepted_offer_version: 'Kabul Edilen Teklif Sürümü',
    email: 'E-posta',
    phone: 'Telefon',
    address: 'Adres',
    source_note: 'Kaynak Notu',
    delivery_form_id: 'Müşteri Teslim Formu',
    balance: 'Bakiye',
    type: 'Tür',
    invoice_amount: 'Servis Faturası',
    invoice_no: 'Fatura No',
    invoice_date: 'Fatura Tarihi',
    season: 'Mevsim',
    installed_at: 'Takılma Tarihi',
    changed_at: 'Değişim Tarihi',
    inspected_at: 'Kontrol Tarihi',
    position: 'Konum',
    method: 'Ödeme Yöntemi',
    notes: 'Notlar',
    note: 'Notlar',
    description: 'Açıklama',
    closed_at: 'Gerçek Bitiş Tarihi',
  }
  for (const [key, value] of Object.entries(r.details || {})) {
    if (
      ['checks', 'target_version', 'target_amount', 'vehicle_id', 'id'].includes(key) ||
      value == null ||
      value === ''
    )
      continue
    const label = localFields.find((f) => f.key === key)?.label || commonLabels[key]
    if (!label) continue
    entries.push([
      label,
      typeof value === 'object'
        ? JSON.stringify(value)
        : typeof value === 'boolean'
          ? value
            ? 'Evet'
            : 'Hayır'
          : value,
    ])
  }
  return entries.filter(([, value]) => value != null).map(([label, value]) => ({ label, value }))
})
const kpis = computed(() => {
  const a = analytics.value,
    card = (label, value, tone = 'blue', status = '', note = '') => ({
      label,
      value,
      tone,
      status,
      note,
    })
  if (['home', 'reports'].includes(section.value)) {
    if (section.value === 'reports')
      return [
        card('Toplam Araç', a.cars.length),
        card('Kiradaki Araç', a.statusGroups[0].count, 'green'),
        card(
          'Aktif Müşteri',
          new Set(a.cars.filter((v) => v.customer_id).map((v) => v.customer_id)).size,
        ),
        card('Kayıtlı Ciro', money(a.totals.revenue), 'green', '', 'Kesilmiş gelir faturaları'),
        card('Toplam Maliyet', money(a.totals.cost), 'amber'),
        card('Açık Alacak', money(a.totals.balance), 'red'),
      ]
    return [
      { ...card('Toplam Araç', a.cars.length), icon: '▱', to: '/supplier-portal/vehicles' },
      ...a.statusGroups.map((g, i) => ({
        ...card(g.label + ' Araç', g.count, ['blue', 'green', 'amber', 'purple', 'gray', 'red'][i]),
        icon: ['⚿', '▤', '⚒', '◇', '○', '!'][i],
        to: '/supplier-portal/vehicles',
      })),
    ]
  }
  if (section.value === 'savings')
    return [
      card('İnceleme Tespiti', findings.value.length, 'amber'),
      card('KM Uyarısı', findings.value.filter((f) => f.category === 'KM').length, 'red'),
      card('Düşük Kullanım', findings.value.filter((f) => f.category === 'Kullanım').length),
      card('Yakıt İncelemesi', findings.value.filter((f) => f.category === 'Yakıt').length),
      card('Düşük HGS', findings.value.filter((f) => f.category === 'HGS').length, 'amber'),
    ]
  if (section.value === 'customers')
    return [
      card('Toplam Müşteri', rows.value.length),
      card(
        'Aktif Müşteri',
        rows.value.filter((r) => r.status === 'Aktif').length,
        'green',
        'Aktif',
      ),
      card(
        'Teklif Aşamasında',
        rows.value.filter((r) => r.status === 'Teklif Aşamasında').length,
        'amber',
        'Teklif Aşamasında',
      ),
      card('Pasif Müşteri', rows.value.filter((r) => r.status === 'Pasif').length, 'gray', 'Pasif'),
    ]
  if (section.value === 'hgs')
    return [
      card('HGS Etiketi', data.value.vehicles.filter((v) => v.hgs_no).length),
      card(
        'Toplam Bakiye',
        money(data.value.vehicles.reduce((s, v) => s + num(v.hgs_balance), 0)),
        'green',
      ),
      card(
        'Düşük Bakiye',
        data.value.vehicles.filter(
          (v) => v.hgs_no && num(v.hgs_balance) < num(data.value.settings.low_balance),
        ).length,
        'red',
      ),
      card(
        'Geçiş Tutarı',
        money(
          data.value.hgs
            .filter((r) => r.details.type === 'Geçiş')
            .reduce((s, r) => s + num(r.amount), 0),
        ),
        'amber',
      ),
    ]
  if (section.value === 'accounting')
    return [
      card('Tahsilat', money(a.totals.receipts), 'green'),
      card('Ödemeler', money(a.totals.payments), 'amber'),
      card('Açık Alacak', money(a.totals.balance), 'red'),
      card('Kayıtlı Ciro', money(a.totals.revenue)),
    ]
  if (section.value === 'fuel')
    return [
      card('Yakıt Kaydı', rows.value.length),
      card('Toplam Gider', money(rows.value.reduce((s, r) => s + num(r.amount), 0)), 'amber'),
      card(
        'Toplam Litre',
        rows.value.reduce((s, r) => s + num(r.details.liters), 0).toLocaleString('tr-TR'),
      ),
      card('Araç', new Set(rows.value.map((r) => r.vehicle_id)).size),
    ]
  return [
    card('Toplam Kayıt', rows.value.length),
    ...rowStatuses.value
      .slice(0, 4)
      .map((s) => card(s, rows.value.filter((r) => r.status === s).length, statusTone(s), s)),
  ]
})
const searchResults = computed(() => {
  if (!data.value) return []
  const q = globalSearch.value.toLocaleLowerCase('tr-TR')
  return [
    ...data.value.vehicles.map((v) => ({
      key: `v-${v.id}`,
      title: v.plate,
      subtitle: `${v.brand} ${v.model}`,
      to: vehicleLink(v.id),
    })),
    ...data.value.customers.map((c) => ({
      key: `c-${c.id}`,
      title: c.title,
      subtitle: 'Müşteri',
      to: `/supplier-portal/customers?record=${c.id}`,
    })),
    ...data.value.records.map((r) => ({
      key: `r-${r.id}`,
      title: r.number,
      subtitle: `${r.title} ${r.customer_name || ''}`,
      to: recordLink(r),
    })),
  ]
    .filter((r) => `${r.title} ${r.subtitle}`.toLocaleLowerCase('tr-TR').includes(q))
    .slice(0, 10)
})
function donut(values) {
  const total = values.reduce((s, v) => s + num(v), 0)
  if (!total) return '#e8f0f7'
  let offset = 0
  return `conic-gradient(${values
    .map((value, index) => {
      const start = offset
      offset += (num(value) / total) * 100
      return `${colors[index % colors.length]} ${start}% ${offset}%`
    })
    .join(',')})`
}
function statusTone(s) {
  return /Tamam|Aktif|Ödendi|Onaylandı|İyi|Kaydedildi/.test(s)
    ? 'green'
    : /İptal|Redded|Doldu|Gecik|Açık/.test(s)
      ? 'red'
      : /Bekle|Plan|Taslak|İncel|Onarım/.test(s)
        ? 'amber'
        : 'blue'
}
function actionLabel(s) {
  return (
    {
      Aktif: 'Sözleşmeyi Aktifleştir',
      Tamamlandı: 'Tamamla',
      Kesildi: 'Kesildi Olarak Kaydet',
      Ödendi: 'Ödendi Olarak Kaydet',
      Onaylandı: 'Onayla',
      Reddedildi: 'Reddet',
      'Sona Erdi': 'Sözleşmeyi Sonlandır',
      İptal: 'İptal Et',
    }[s] || s
  )
}
function clearFilters() {
  Object.assign(filters, { search: '', status: '', customer: '', vehicle: '', start: '', end: '' })
  page.value = 1
}
function searchAll() {
  if (section.value !== 'home')
    router.push({ path: '/supplier-portal', query: { search: globalSearch.value } })
}
async function load() {
  loading.value = true
  error.value = ''
  unauthorized.value = false
  try {
    data.value = await supplierApi('/snapshot')
    localStorage.setItem('fleetcar_supplier_role', data.value.session.role)
    Object.assign(settingsForm, data.value.settings)
    if (section.value === 'users') data.value.users = await supplierApi('/users')
    if (section.value === 'reports') {
      reportCatalog.value = await supplierApi('/reports/catalog')
      await loadServerReport()
    }
    if (route.query.record) {
      const row = rows.value.find((r) => String(r.id) === String(route.query.record))
      if (row) await selectRow(row)
    }
    if (!route.query.record && !selected.value && window.innerWidth >= 1200 && rows.value.length)
      await selectRow(rows.value[0])
    if (route.query.new === '1' && canCreate.value && !showForm.value) await openCreate()
  } catch (e) {
    error.value = e.message
    unauthorized.value = e.status === 401
  } finally {
    loading.value = false
  }
}
async function selectRow(row) {
  selected.value = row
  detailTab.value = 'Genel'
  selectedEvents.value = []
  selectedVersions.value = []
  if (row.source === 'operation') {
    try {
      if (row.kind === 'offer')
        selectedVersions.value = await supplierApi(`/records/${row.id}/versions`)
      selectedEvents.value = await supplierApi(`/records/${row.id}/events`)
    } catch (e) {
      error.value = e.message
    }
  }
}
function initForm(key, row = null) {
  modalSection.value = key
  editing.value = row
  formError.value = ''
  const conf = supplierModules[key] || {}
  const details = {}
  for (const f of conf.fields || [])
    details[f.key] = f.default ?? (f.type === 'checkbox' ? false : '')
  if (conf.checks) details.checks = {}
  Object.assign(form, {
    title: '',
    customer_id: '',
    vehicle_id: '',
    parent_id: '',
    date: new Date().toLocaleDateString('en-CA'),
    end_date: '',
    amount: 0,
    details,
    email: '',
    phone: '',
    address: '',
    password: '',
    role: 'viewer',
  })
  if (key === 'contracts') {
    const end = new Date()
    end.setFullYear(end.getFullYear() + 1)
    form.end_date = end.toLocaleDateString('en-CA')
    form.details.quantity = 1
  }
  if (row)
    Object.assign(form, {
      title: row.title || row.name || '',
      customer_id: row.customer_id ? String(row.customer_id) : '',
      vehicle_id: row.vehicle_id || '',
      parent_id: row.parent_id ? String(row.parent_id) : '',
      date: row.date?.slice(0, 10) || form.date,
      end_date: row.end_date || '',
      amount: row.amount || 0,
      details: { ...details, ...JSON.parse(JSON.stringify(row.details || {})) },
      email: row.email || '',
      phone: row.phone || '',
      address: row.address || '',
      role: row.role || 'viewer',
    })
  showForm.value = true
  nextTick(() =>
    document
      .querySelector('.sw-form-modal input:not([disabled]),.sw-form-modal select:not([disabled])')
      ?.focus(),
  )
}
async function openCreate() {
  initForm(section.value)
  if (route.query.new === '1')
    await router.replace({ path: route.path, query: { ...route.query, new: undefined } })
  if (section.value === 'customers')
    try {
      directory.value = await supplierApi('/directory')
    } catch (e) {
      formError.value = e.message
    }
}
function openHgs(v) {
  initForm('hgs')
  form.vehicle_id = v.id
  form.title = `${v.plate} HGS işlemi`
  form.details.hgs_no = v.hgs_no || ''
}
function openEdit() {
  initForm(
    selected.value.source === 'user'
      ? 'users'
      : selected.value.source === 'customer'
        ? 'customers'
        : kindSection(selected.value.kind),
    selected.value,
  )
}
function syncDirectory() {
  const c = directory.value.find((c) => String(c.id) === form.customer_id)
  if (c) form.title = c.company_name
  else form.title = ''
}
function syncCostSource() {
  const all = [...data.value.fuel, ...data.value.hgs, ...data.value.service, ...data.value.records]
  const source = all.find(
    (r) =>
      (r.source === 'operation' ? `${r.kind}:${r.id}` : r.id) === form.details.source_reference,
  )
  if (source) {
    form.vehicle_id = source.vehicle_id
    form.customer_id = source.customer_id ? String(source.customer_id) : form.customer_id
    form.details.direction = 'gider'
  }
}
function syncParent() {
  const r = data.value.records.find((r) => String(r.id) === String(form.parent_id))
  if (r) {
    form.customer_id = String(r.customer_id || '')
    form.vehicle_id = r.vehicle_id || ''
    if (modalSection.value === 'payment') form.amount = r.balance
  }
}
function fieldOptions(field) {
  if (field.dynamic === 'vehicleDocuments')
    return data.value.files
      .filter((f) => f.category === 'document' && f.vehicle_id === form.vehicle_id)
      .map((f) => ({ value: f.id, label: f.original_name }))
  if (field.dynamic === 'maintenanceProviders')
    return data.value.providers
      .filter((p) => p.type === 'servis')
      .map((p) => ({ value: String(p.id), label: p.name }))
  if (field.dynamic === 'providers')
    return data.value.providers
      .filter((p) => p.type === (form.details.type || 'servis'))
      .map((p) => ({ value: String(p.id), label: p.name }))
  if (field.dynamic === 'costSources')
    return [
      ...data.value.fuel,
      ...data.value.hgs.filter((r) => r.details.type === 'Geçiş'),
      ...data.value.service,
      ...data.value.records.filter(
        (r) => ['policy', 'damage', 'fine'].includes(r.kind) && r.source === 'operation',
      ),
    ].map((r) => ({
      value: r.source === 'operation' ? `${r.kind}:${r.id}` : r.id,
      label: `${r.number} · ${r.plate || ''} · ${money(r.amount)}`,
    }))
  return field.options || []
}
async function saveForm() {
  saving.value = true
  formError.value = ''
  try {
    let row
    if (modalSection.value === 'users') {
      const body = {
        name: form.title,
        email: form.email,
        role: form.role,
        is_active: editing.value?.is_active ?? true,
      }
      if (form.password) body.password = form.password
      row = await supplierApi(editing.value ? `/users/${editing.value.id}` : '/users', {
        method: editing.value ? 'PUT' : 'POST',
        body,
      })
    } else if (modalSection.value === 'customers') {
      row = await supplierApi(editing.value ? `/customers/${editing.value.id}` : '/customers', {
        method: editing.value ? 'PUT' : 'POST',
        body: {
          company_name: form.title,
          customer_id: form.customer_id ? Number(form.customer_id) : null,
          email: form.email || null,
          phone: form.phone || null,
          address: form.address || null,
          details: form.details,
        },
      })
    } else if (modalCfg.value.shared) {
      row = await supplierApi(`/shared/${modalSection.value}`, {
        method: 'POST',
        body: {
          vehicle_id: form.vehicle_id,
          date: form.date,
          amount: num(form.amount),
          title: form.title,
          details: form.details,
        },
      })
    } else {
      const body = {
        title: form.title,
        customer_id: form.customer_id ? Number(form.customer_id) : null,
        vehicle_id: form.vehicle_id || null,
        parent_id: form.parent_id ? Number(form.parent_id) : null,
        date: form.date,
        end_date: form.end_date || null,
        amount: num(form.amount),
        details: form.details,
      }
      if (editing.value) body.version = editing.value.version
      row = await supplierApi(
        editing.value ? `/records/${editing.value.id}` : `/records/${modalCfg.value.kind}`,
        { method: editing.value ? 'PUT' : 'POST', body },
      )
    }
    showForm.value = false
    notice.value = 'Kayıt kaydedildi.'
    if (row?.kind && row.source === 'operation' && row.kind !== cfg.value.kind) {
      await router.push(recordLink(row))
      return
    }
    await load()
    if (row?.id) {
      const fresh = rows.value.find((r) => r.id === row.id)
      if (fresh) await selectRow(fresh)
    }
  } catch (e) {
    formError.value = e.message
  } finally {
    saving.value = false
  }
}
async function mutate(path, body, success) {
  saving.value = true
  error.value = ''
  try {
    const r = await supplierApi(path, { method: 'POST', body })
    notice.value = success
    await load()
    const fresh = data.value.records.find((x) => x.id === r.id)
    if (fresh) await selectRow(fresh)
    return r
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
function transition(status) {
  return mutate(
    `/records/${selected.value.id}/status`,
    { status, version: selected.value.version },
    'İşlem durumu güncellendi.',
  )
}
async function convertRecord(kind) {
  if (kind === 'contract') {
    conversion.value = {
      id: selected.value.id,
      version: selected.value.version,
      quantity: Number(selected.value.details.quantity) || 1,
    }
    conversionVehicles.value = []
    conversionVehicle.value = selected.value.vehicle_id || ''
    return
  }
  if (kind === 'delivery' && (selected.value.details.vehicle_ids || []).length > 1) {
    initForm('deliveries')
    form.parent_id = String(selected.value.id)
    form.customer_id = String(selected.value.customer_id)
    form.vehicle_id = ''
    form.title = `${selected.value.number} / Teslimat`
    return
  }
  const r = await mutate(
    `/records/${selected.value.id}/convert`,
    { kind, version: selected.value.version },
    'Bağlantılı kayıt oluşturuldu.',
  )
  if (r) router.push(recordLink(r))
}
async function confirmConversion() {
  const r = await mutate(
    `/records/${conversion.value.id}/convert`,
    {
      kind: 'contract',
      version: conversion.value.version,
      vehicle_id: conversion.value.quantity > 1 ? null : conversionVehicle.value,
      vehicle_ids: conversion.value.quantity > 1 ? conversionVehicles.value : undefined,
    },
    'Sözleşme taslağı oluşturuldu.',
  )
  if (r) {
    conversion.value = null
    router.push(recordLink(r))
  }
}
function openPayment() {
  const invoice = selected.value
  initForm('payment')
  form.title = `${invoice.number} ${invoice.details.direction === 'gelir' ? 'tahsilatı' : 'ödemesi'}`
  form.parent_id = String(invoice.id)
  form.customer_id = String(invoice.customer_id)
  form.vehicle_id = invoice.vehicle_id || ''
  form.amount = invoice.balance
}
function requestApproval() {
  return mutate(
    `/records/${selected.value.id}/request-approval`,
    undefined,
    'Onay talebi oluşturuldu.',
  )
}
async function toggleUser() {
  saving.value = true
  try {
    await supplierApi(`/users/${selected.value.id}`, {
      method: 'PUT',
      body: {
        name: selected.value.name,
        email: selected.value.email,
        role: selected.value.role,
        is_active: !selected.value.is_active,
      },
    })
    notice.value = 'Kullanıcı durumu güncellendi.'
    selected.value = null
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
async function saveSettings() {
  saving.value = true
  try {
    await supplierApi('/settings', { method: 'PUT', body: settingsForm })
    notice.value = 'Ayarlar kaydedildi.'
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
function exportLedger() {
  if (!data.value?.session?.capabilities?.export_report) return
  downloadSupplierCsv(
    [
      ['Tarih', 'Kaynak', 'Plaka', 'Müşteri', 'Kategori', 'Tutar'],
      ...reportRows.value.map((r) => [
        r.date,
        r.number,
        r.plate,
        r.customer_name,
        r.category,
        r.amount,
      ]),
    ],
    'fleetrent-mali-defter.csv',
  )
}
function exportRows() {
  if (!data.value?.session?.capabilities?.export_report) return
  if (['home', 'reports'].includes(section.value)) {
    exportLedger()
    return
  }
  if (section.value === 'savings') {
    downloadSupplierCsv(
      [
        ['Kategori', 'Tespit', 'Kanıt', 'İncelenecek Tutar'],
        ...findings.value.map((r) => [r.category, r.title, r.evidence, r.amount]),
      ],
      'fleetrent-tespitler.csv',
    )
    return
  }
  downloadSupplierCsv(
    [
      ['No', 'Başlık', 'Plaka', 'Müşteri', 'Tarih', 'Bitiş', 'Tutar', 'Durum'],
      ...filteredRows.value.map((r) => [
        r.number || r.name,
        r.title || r.email,
        r.plate,
        r.customer_name,
        r.date,
        r.end_date,
        r.amount,
        r.status,
      ]),
    ],
    `fleetrent-${section.value}.csv`,
  )
}
function syncInvoiceTax(key) {
  if (key === 'occurred_at' && form.details.occurred_at)
    form.date = form.details.occurred_at.slice(0, 10)
  if (
    modalCfg.value.kind === 'invoice' &&
    ['net_amount', 'tax_rate'].includes(key) &&
    form.details.net_amount !== '' &&
    form.details.tax_rate !== ''
  )
    form.amount =
      Math.round(num(form.details.net_amount) * (1 + num(form.details.tax_rate) / 100) * 100) / 100
}
function reportQuery(format = 'json') {
  const values = {
    ...reportFilters,
    customer: filters.customer,
    vehicle: filters.vehicle,
    start: filters.start,
    end: filters.end,
    status: filters.status,
    format,
  }
  return new URLSearchParams(
    Object.entries(values).filter(([, v]) => v !== '' && v != null),
  ).toString()
}
async function reflectCost() {
  const row = selected.value
  const record = await mutate(
    `/responsibility/${row.kind}/${row.source_id || row.id}/reflect`,
    undefined,
    'Yansıtma fatura taslağı oluşturuldu.',
  )
  if (record) router.push(recordLink(record))
}
async function loadServerReport() {
  try {
    serverReport.value = await supplierApi(`/reports/${serverReportKey.value}?${reportQuery()}`)
  } catch (e) {
    error.value = e.message
  }
}
async function exportServerReport(format) {
  saving.value = true
  try {
    await downloadApi(
      `/api/supplier-workspace/reports/${serverReportKey.value}?${reportQuery(format)}`,
      { account: 'supplier', filename: `fleetrent-${serverReportKey.value}.${format}` },
    )
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
function printSelected() {
  window.print()
}
watch(
  () => route.fullPath,
  () => {
    selected.value = null
    notice.value = ''
    clearFilters()
    filters.search = String(route.query.search || '')
    filters.status = String(route.query.status || '')
    globalSearch.value = String(route.query.search || '')
    load()
  },
)
let refreshTimer
async function refreshBackground() {
  if (document.hidden || showForm.value || conversion.value || saving.value || loading.value) return
  try {
    const latest = await supplierApi('/snapshot')
    data.value = latest
    if (selected.value?.source === 'operation') {
      const fresh = latest.records.find((r) => r.id === selected.value.id)
      if (fresh && fresh.version !== selected.value.version) {
        const tab = detailTab.value
        await selectRow(fresh)
        detailTab.value = tab
      }
    }
  } catch (e) {
    if (e.status === 401) {
      error.value = e.message
      unauthorized.value = true
    }
  }
}
onMounted(() => {
  globalSearch.value = String(route.query.search || '')
  filters.status = String(route.query.status || '')
  load()
  refreshTimer = setInterval(refreshBackground, 30000)
})
onUnmounted(() => clearInterval(refreshTimer))
</script>
<style src="../supplier-workspace.css"></style>
