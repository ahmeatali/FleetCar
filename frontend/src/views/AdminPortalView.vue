<template>
  <div class="portal-layout fleet-dashboard admin-portal">
    <Sidebar admin />

    <main class="portal-main adm">
      <!-- 1. QUOTES -->
      <template v-if="activeTab === 'quotes'">
        <PageHeader
          eyebrow="Yönetici Paneli"
          title="Müşteri Kiralama Teklifleri"
          description="Ana sayfadan gelen teklif taleplerini inceleyin, tedarikçi tekliflerini görün veya yeni talep oluşturun."
        >
          <template #actions>
            <UiButton class="adm-btn primary" @click="showAddQuoteModal = true"
              ><NavIcon name="plus" size="16" />Yeni Teklif Talebi</UiButton
            >
          </template>
        </PageHeader>

        <div class="adm-kpis">
          <KpiCard label="Toplam Talep" :value="quotes.length" icon="document" tone="blue" />
          <KpiCard
            label="Gelen Tedarikçi Teklifi"
            :value="totalSupplierBidsCount"
            icon="store"
            tone="teal"
          />
          <KpiCard
            label="Kabul / İmzalandı"
            :value="acceptedQuotesCount"
            icon="check"
            tone="green"
          />
          <KpiCard label="Reddedilen" :value="rejectedQuotesCount" icon="x-circle" tone="red" />
          <KpiCard label="Silinen" :value="deletedQuotesCount" icon="trash" tone="gray" />
        </div>

        <section class="adm-panel">
          <div class="adm-toolbar">
            <label class="adm-search">
              <NavIcon name="search" size="16" />
              <input
                v-model="quoteFilter.search"
                type="search"
                aria-label="Teklif ara"
                placeholder="Şirket adı veya e-posta ara"
              />
            </label>
            <div class="adm-chips" role="group" aria-label="Durum">
              <span class="adm-chips-label">Durum</span>
              <button
                v-for="s in [
                  'Tümü',
                  'Teklif Bekleniyor',
                  'Teklif Geldi',
                  'Sözleşme Yapıldı',
                  'Silinen',
                ]"
                :key="s"
                type="button"
                class="adm-chip"
                :aria-pressed="quoteFilter.status === s"
                @click="quoteFilter.status = s"
              >
                {{ s }}
              </button>
            </div>
            <div class="adm-chips" role="group" aria-label="Segment">
              <span class="adm-chips-label">Segment</span>
              <button
                v-for="seg in ['Tümü', 'A', 'B', 'C', 'D', 'E']"
                :key="seg"
                type="button"
                class="adm-chip"
                :aria-pressed="quoteFilter.segment === seg"
                @click="quoteFilter.segment = seg"
              >
                {{ seg }}
              </button>
            </div>
            <span class="adm-count">{{ filteredQuotes.length }} / {{ quotes.length }} teklif</span>
          </div>

          <p v-if="loading" class="adm-loading">Yükleniyor…</p>
          <EmptyState
            v-else-if="filteredQuotes.length === 0"
            icon="document"
            title="Kriterlere uygun teklif yok"
            :text="
              quotes.length ? 'Filtreleri değiştirmeyi deneyin.' : 'Henüz teklif talebi gelmedi.'
            "
          />
          <div v-else class="adm-table-wrap">
            <table class="custom-table adm-table">
              <thead>
                <tr>
                  <th>Şirket</th>
                  <th>Talep</th>
                  <th>Süre / KM</th>
                  <th>Aylık Bedel</th>
                  <th>Durum</th>
                  <th class="adm-actions-col">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="quote in filteredQuotes"
                  :key="quote.id"
                  :class="{ 'is-muted': isDeletedQuote(quote) }"
                >
                  <td>
                    <div class="adm-cell-title">{{ quote.company_name }}</div>
                    <div class="adm-cell-sub">#{{ quote.id }} · {{ quote.email }}</div>
                    <div v-if="quote.phone" class="adm-cell-sub">{{ quote.phone }}</div>
                  </td>
                  <td>
                    <span class="adm-badge tone-blue">{{ quote.vehicle_count }} araç</span>
                    <div class="adm-cell-sub">
                      {{ quote.vehicle_segment }} · {{ quote.vehicle_type }}
                    </div>
                  </td>
                  <td>
                    <div>{{ quote.duration_months }} ay</div>
                    <div class="adm-cell-sub">
                      {{ quote.estimated_annual_mileage?.toLocaleString('tr-TR') }} km/yıl
                    </div>
                  </td>
                  <td>
                    <div class="adm-money">{{ money(quote.monthly_price_try) }}</div>
                    <div class="adm-cell-sub">
                      {{
                        quote.bids?.length
                          ? `${quote.bids.length} tedarikçi teklifi`
                          : 'Tedarikçi teklifi yok'
                      }}
                    </div>
                  </td>
                  <td>
                    <select
                      v-model="quote.status"
                      class="adm-status"
                      :class="`tone-${quoteTone(quote.status)}`"
                      :aria-label="`${quote.company_name} teklif durumu`"
                      @change="onStatusChange(quote.id, quote.status)"
                    >
                      <option v-for="s in QUOTE_STATUSES" :key="s" :value="s">{{ s }}</option>
                    </select>
                  </td>
                  <td class="adm-actions-col">
                    <div class="adm-actions">
                      <UiButton class="adm-btn sm" @click="openQuoteBidsModal(quote)"
                        ><NavIcon name="store" size="15" />Teklifler ({{
                          quote.bids?.length || 0
                        }})</UiButton
                      >
                      <UiButton
                        class="adm-btn sm ghost"
                        :aria-label="`${quote.company_name} talebini düzenle`"
                        @click="openEditQuoteModal(quote)"
                        ><NavIcon name="edit" size="15" />Düzenle</UiButton
                      >
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- 2. CUSTOMERS -->
      <template v-if="activeTab === 'customers' && !showCustomerDetailsModal">
        <PageHeader
          eyebrow="Yönetici Paneli"
          title="Aktif Müşteriler"
          description="Kiralama sözleşmesi imzalanmış ve onaylanmış kurumsal müşteriler."
        >
          <template #actions>
            <UiButton class="adm-btn primary" @click="showAddCustomerModal = true"
              ><NavIcon name="plus" size="16" />Yeni Müşteri</UiButton
            >
          </template>
        </PageHeader>

        <div class="adm-kpis">
          <KpiCard
            label="Sözleşmeli Şirket"
            :value="customers.length"
            icon="briefcase"
            tone="blue"
          />
          <KpiCard
            label="Toplam Filo Aracı"
            :value="totalCustomerVehicles"
            icon="car"
            tone="teal"
          />
          <KpiCard
            label="Aylık Sözleşme Cirosu"
            :value="`₺${totalCustomerRevenue.toLocaleString('tr-TR')}`"
            icon="wallet"
            tone="green"
          />
        </div>

        <section class="adm-panel">
          <div class="adm-toolbar">
            <label class="adm-search">
              <NavIcon name="search" size="16" />
              <input
                v-model="customerFilter.search"
                type="search"
                aria-label="Müşteri ara"
                placeholder="Şirket adı, e-posta veya telefon"
              />
            </label>
            <div class="adm-chips" role="group" aria-label="Filo durumu">
              <span class="adm-chips-label">Filo</span>
              <button
                v-for="f in ['Tümü', 'Eksikli', 'Tam']"
                :key="f"
                type="button"
                class="adm-chip"
                :aria-pressed="customerFilter.fleetStatus === f"
                @click="customerFilter.fleetStatus = f"
              >
                {{ f }}
              </button>
            </div>
            <span class="adm-count"
              >{{ filteredCustomers.length }} / {{ customers.length }} müşteri</span
            >
          </div>

          <p v-if="loading" class="adm-loading">Yükleniyor…</p>
          <EmptyState
            v-else-if="filteredCustomers.length === 0"
            icon="users"
            title="Kriterlere uygun müşteri yok"
            :text="
              customers.length
                ? 'Filtreleri değiştirmeyi deneyin.'
                : 'Sözleşmesi imzalanan müşteriler burada listelenir.'
            "
          />
          <div v-else class="adm-table-wrap">
            <table class="custom-table adm-table">
              <thead>
                <tr>
                  <th>Şirket</th>
                  <th>İletişim</th>
                  <th>Filo</th>
                  <th>Aylık Bedel</th>
                  <th>Portal</th>
                  <th class="adm-actions-col">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="c in filteredCustomers"
                  :key="c.id"
                  class="is-clickable"
                  @click="openCustomerDetails(c)"
                >
                  <td>
                    <div class="adm-entity">
                      <span class="adm-avatar" aria-hidden="true">{{
                        c.company_name?.charAt(0)
                      }}</span>
                      <span>
                        <button type="button" class="adm-link" @click.stop="openCustomerDetails(c)">
                          {{ c.company_name }}
                        </button>
                        <span class="adm-cell-sub"
                          >#{{ c.id
                          }}<template v-if="c.legal_title"> · {{ c.legal_title }}</template></span
                        >
                      </span>
                    </div>
                  </td>
                  <td>
                    <div>{{ c.email }}</div>
                    <div class="adm-cell-sub">{{ c.phone }}</div>
                  </td>
                  <td>
                    <div>{{ c.actual_vehicle_count }} / {{ c.registered_vehicles_count }} araç</div>
                    <span v-if="c.vehicle_deficit > 0" class="adm-badge tone-amber"
                      >{{ c.vehicle_deficit }} eksik</span
                    >
                    <span v-else class="adm-badge tone-green">Tam</span>
                  </td>
                  <td>
                    <div class="adm-money">{{ money(c.contract_amount) }}</div>
                    <div v-if="c.signed_at" class="adm-cell-sub">
                      İmza {{ formatDate(c.signed_at) }}
                    </div>
                  </td>
                  <td>
                    <span class="adm-badge" :class="`tone-${inviteTone(c.invitation_status)}`">{{
                      inviteLabel(c.invitation_status)
                    }}</span>
                  </td>
                  <td class="adm-actions-col">
                    <div class="adm-actions">
                      <UiButton
                        class="adm-btn sm teal"
                        title="Destek için bu müşterinin portalına gir"
                        @click.stop="enterAccount('customer', c.id, c.company_name)"
                        ><NavIcon name="login" size="15" />Hesaba Gir</UiButton
                      >
                      <UiButton class="adm-btn sm ghost" @click.stop="sendCustomerInvite(c)"
                        ><NavIcon name="mail" size="15" />{{
                          c.invitation_status === 'Davet Gönderildi' ? 'Yeniden Davet' : 'Davet Et'
                        }}</UiButton
                      >
                      <UiButton
                        class="adm-btn sm ghost icon"
                        :aria-label="`${c.company_name} müşterisini düzenle`"
                        title="Düzenle"
                        @click.stop="openEditCustomerModal(c)"
                        ><NavIcon name="edit" size="15"
                      /></UiButton>
                      <UiButton
                        class="adm-btn sm danger icon"
                        :aria-label="`${c.company_name} müşterisini sil`"
                        title="Sil"
                        @click.stop="deleteCustomer(c)"
                        ><NavIcon name="trash" size="15"
                      /></UiButton>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- Customer detail -->
      <template
        v-if="activeTab === 'customers' && showCustomerDetailsModal && selectedCustomerDetails"
      >
        <button type="button" class="adm-back" @click="closeCustomerDetails">
          <NavIcon name="arrow-left" size="16" />Müşteri listesi
        </button>
        <PageHeader
          :title="selectedCustomerDetails.company_name"
          :description="selectedCustomerDetails.legal_title"
          eyebrow="Müşteri"
        >
          <template #actions>
            <UiButton
              class="adm-btn teal"
              @click="
                enterAccount(
                  'customer',
                  selectedCustomerDetails.id,
                  selectedCustomerDetails.company_name,
                )
              "
              ><NavIcon name="login" size="16" />Hesaba Gir</UiButton
            >
            <UiButton class="adm-btn ghost" @click="openEditCustomerModal(selectedCustomerDetails)"
              ><NavIcon name="edit" size="16" />Düzenle</UiButton
            >
          </template>
        </PageHeader>
        <ul class="adm-contact">
          <li v-if="selectedCustomerDetails.email">
            <NavIcon name="mail" size="15" />{{ selectedCustomerDetails.email }}
          </li>
          <li v-if="selectedCustomerDetails.phone">
            <NavIcon name="phone" size="15" />{{ selectedCustomerDetails.phone }}
          </li>
          <li v-if="selectedCustomerDetails.address">
            <NavIcon name="pin" size="15" />{{ selectedCustomerDetails.address }}
          </li>
        </ul>
        <div class="adm-kpis">
          <KpiCard label="Kayıtlı Araç" :value="customerVehicles.length" icon="car" tone="blue" />
          <KpiCard
            label="Aylık Sözleşme"
            :value="`₺${(selectedCustomerDetails.contract_amount || 0).toLocaleString('tr-TR')}`"
            icon="wallet"
            tone="green"
          />
          <KpiCard
            label="İmza Tarihi"
            :value="formatDate(selectedCustomerDetails.signed_at)"
            icon="calendar"
            tone="violet"
          />
          <KpiCard
            label="Servis Kaydı"
            :value="customerServices.length"
            icon="wrench"
            tone="amber"
          />
        </div>

        <section class="adm-panel">
          <div class="adm-tabs" role="tablist" aria-label="Müşteri ayrıntıları">
            <button
              type="button"
              role="tab"
              :aria-selected="detailTab === 'vehicles'"
              class="adm-tab"
              @click="detailTab = 'vehicles'"
            >
              Araçlar <span>{{ customerVehicles.length }}</span>
            </button>
            <button
              type="button"
              role="tab"
              :aria-selected="detailTab === 'services'"
              class="adm-tab"
              @click="detailTab = 'services'"
            >
              Servis Geçmişi <span>{{ customerServices.length }}</span>
            </button>
          </div>

          <template v-if="detailTab === 'vehicles'">
            <EmptyState
              v-if="customerVehicles.length === 0"
              icon="car"
              title="Bu müşteriye ait kayıtlı araç yok"
            />
            <div v-else class="adm-vehicle-grid">
              <article v-for="v in customerVehicles" :key="v.id" class="adm-vehicle">
                <header>
                  <span class="adm-plate">{{ v.plate }}</span>
                  <span class="adm-badge" :class="`tone-${vehicleTone(v.status)}`">{{
                    v.status
                  }}</span>
                </header>
                <h3>
                  {{ v.brand }} {{ v.model }} <small>{{ v.year }}</small>
                </h3>
                <dl>
                  <dt>Segment / Tip</dt>
                  <dd>{{ v.vehicle_segment }} / {{ v.vehicle_type }}</dd>
                  <dt>Yakıt</dt>
                  <dd>{{ v.fuel }}</dd>
                  <dt>Kilometre</dt>
                  <dd>{{ v.mileage?.toLocaleString('tr-TR') }} km</dd>
                  <dt>Muayene</dt>
                  <dd>{{ v.inspection_date || '—' }}</dd>
                  <dt>Son Servis</dt>
                  <dd>{{ v.last_service_date || '—' }}</dd>
                  <dt>Şase No</dt>
                  <dd class="adm-mono">{{ v.chassis_no }}</dd>
                </dl>
              </article>
            </div>
          </template>

          <template v-else>
            <EmptyState
              v-if="customerServices.length === 0"
              icon="wrench"
              title="Bu müşteriye ait servis kaydı yok"
            />
            <div v-else class="adm-table-wrap">
              <table class="custom-table adm-table">
                <thead>
                  <tr>
                    <th>Araç</th>
                    <th>Tedarikçi / Servis</th>
                    <th>Hizmet</th>
                    <th>Açıklama</th>
                    <th>Durum</th>
                    <th>Tarih</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in customerServices" :key="s.id">
                    <td>
                      <div class="adm-cell-title">{{ s.vehicle_plate }}</div>
                      <div class="adm-cell-sub">#{{ s.id }} · {{ s.vehicle_brand_model }}</div>
                    </td>
                    <td>{{ s.supplier_name }}</td>
                    <td>
                      <span class="adm-badge" :class="`tone-${categoryTone(s.type)}`">{{
                        getTypeName(s.type)
                      }}</span>
                    </td>
                    <td class="adm-wrap">{{ s.description }}</td>
                    <td>
                      <span class="adm-badge" :class="`tone-${serviceTone(s.status)}`">{{
                        s.status
                      }}</span>
                    </td>
                    <td>{{ s.created_at }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </section>
      </template>

      <!-- 3. VEHICLES -->
      <template v-if="activeTab === 'vehicles' && !showVehicleDetailsModal">
        <PageHeader
          eyebrow="Yönetici Paneli"
          title="Tüm Araçlar"
          description="Sistemdeki araçların kiralama, servis ve kullanım durumu."
        />

        <div class="adm-kpis">
          <KpiCard label="Kayıtlı Araç" :value="vehicles.length" icon="car" tone="blue" />
          <KpiCard
            label="Aktif Kullanımda"
            :value="activeVehiclesCount"
            icon="check"
            tone="green"
          />
          <KpiCard
            label="Serviste / Bakımda"
            :value="serviceVehiclesCount"
            icon="wrench"
            tone="amber"
          />
        </div>

        <section class="adm-panel">
          <div class="adm-toolbar">
            <label class="adm-search">
              <NavIcon name="search" size="16" />
              <input
                v-model="vehicleFilter.search"
                type="search"
                aria-label="Araç ara"
                placeholder="Plaka, marka veya model ara"
              />
            </label>
            <div class="adm-chips" role="group" aria-label="Durum">
              <span class="adm-chips-label">Durum</span>
              <button
                v-for="st in ['Tümü', 'Aktif', 'Serviste', 'Lastik Değişiminde', 'Yol Yardımında']"
                :key="st"
                type="button"
                class="adm-chip"
                :aria-pressed="vehicleFilter.status === st"
                @click="vehicleFilter.status = st"
              >
                {{ st }}
              </button>
            </div>
            <div class="adm-chips" role="group" aria-label="Yakıt">
              <span class="adm-chips-label">Yakıt</span>
              <button
                v-for="f in ['Tümü', 'Elektrik', 'Hibrit', 'Dizel', 'Benzin']"
                :key="f"
                type="button"
                class="adm-chip"
                :aria-pressed="vehicleFilter.fuel === f"
                @click="vehicleFilter.fuel = f"
              >
                {{ f }}
              </button>
            </div>
            <span class="adm-count"
              >{{ filteredVehicles.length }} / {{ vehicles.length }} araç</span
            >
          </div>

          <p v-if="loading" class="adm-loading">Yükleniyor…</p>
          <EmptyState
            v-else-if="filteredVehicles.length === 0"
            icon="car"
            title="Kriterlere uygun araç yok"
            :text="
              vehicles.length ? 'Filtreleri değiştirmeyi deneyin.' : 'Sisteme henüz araç eklenmedi.'
            "
          />
          <div v-else class="adm-table-wrap">
            <table class="custom-table adm-table">
              <thead>
                <tr>
                  <th>Plaka</th>
                  <th>Araç</th>
                  <th>Müşteri</th>
                  <th>Tedarikçi</th>
                  <th>Kilometre</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="v in filteredVehicles"
                  :key="v.id"
                  class="is-clickable"
                  @click="openVehicleDetails(v)"
                >
                  <td>
                    <button
                      type="button"
                      class="adm-plate adm-plate-btn"
                      @click.stop="openVehicleDetails(v)"
                    >
                      {{ v.plate }}
                    </button>
                  </td>
                  <td>
                    <div class="adm-cell-title">{{ v.brand }} {{ v.model }}</div>
                    <div class="adm-cell-sub">
                      {{ v.year }} · {{ v.vehicle_segment }} segment · {{ v.fuel }}
                    </div>
                  </td>
                  <td>{{ v.customer_name || '—' }}</td>
                  <td>{{ v.supplier_name || '—' }}</td>
                  <td>{{ v.mileage?.toLocaleString('tr-TR') }} km</td>
                  <td>
                    <span class="adm-badge" :class="`tone-${vehicleTone(v.status)}`">{{
                      v.status
                    }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- Vehicle detail -->
      <template
        v-if="activeTab === 'vehicles' && showVehicleDetailsModal && selectedVehicleDetails"
      >
        <button type="button" class="adm-back" @click="closeVehicleDetails">
          <NavIcon name="arrow-left" size="16" />Araç listesi
        </button>
        <header class="adm-vehicle-head">
          <span class="adm-plate lg">{{ selectedVehicleDetails.plate }}</span>
          <div>
            <h1>{{ selectedVehicleDetails.brand }} {{ selectedVehicleDetails.model }}</h1>
            <p>
              {{ selectedVehicleDetails.year }} · Şase
              <span class="adm-mono">{{ selectedVehicleDetails.chassis_no }}</span>
            </p>
          </div>
          <span class="adm-badge" :class="`tone-${vehicleTone(selectedVehicleDetails.status)}`">{{
            selectedVehicleDetails.status
          }}</span>
        </header>
        <div class="adm-kpis">
          <KpiCard
            label="Kilometre"
            :value="`${(selectedVehicleDetails.mileage || 0).toLocaleString('tr-TR')} km`"
            icon="road"
            tone="blue"
          />
          <KpiCard
            label="Yakıt / Segment"
            :value="`${selectedVehicleDetails.fuel} / ${selectedVehicleDetails.vehicle_segment}`"
            icon="fuel"
            tone="teal"
          />
          <KpiCard
            label="Muayene"
            :value="selectedVehicleDetails.inspection_date || 'Belirtilmemiş'"
            icon="calendar"
            tone="violet"
          />
        </div>

        <div class="adm-two">
          <section class="adm-panel">
            <h2 class="adm-panel-title">Kiralama</h2>
            <dl v-if="selectedVehicleDetails.customer_name" class="adm-dl">
              <dt>Kiracı müşteri</dt>
              <dd>{{ selectedVehicleDetails.customer_name }}</dd>
              <dt>Durum</dt>
              <dd>Sözleşmeli kiralama</dd>
            </dl>
            <p v-else class="adm-muted">Bu araç şu anda bir müşteriye kiralanmamış.</p>
          </section>
          <section class="adm-panel">
            <h2 class="adm-panel-title">Tedarikçi</h2>
            <dl v-if="selectedVehicleDetails.supplier_name" class="adm-dl">
              <dt>Tedarikçi firma</dt>
              <dd>{{ selectedVehicleDetails.supplier_name }}</dd>
              <dt>Temin türü</dt>
              <dd>Tedarikçi ortaklığı</dd>
            </dl>
            <p v-else class="adm-muted">Bu araç için atanmış bir tedarikçi yok.</p>
          </section>
        </div>

        <section class="adm-panel">
          <h2 class="adm-panel-title">Servis ve Hizmet Geçmişi</h2>
          <EmptyState
            v-if="vehicleServices.length === 0"
            icon="wrench"
            title="Servis, arıza veya bakım kaydı yok"
            compact
          />
          <div v-else class="adm-table-wrap">
            <table class="custom-table adm-table">
              <thead>
                <tr>
                  <th>Talep</th>
                  <th>Servis / Tedarikçi</th>
                  <th>Hizmet</th>
                  <th>Açıklama</th>
                  <th>Tarih</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in vehicleServices" :key="s.id">
                  <td>#{{ s.id }}</td>
                  <td class="adm-cell-title">{{ s.supplier_name }}</td>
                  <td>
                    <span class="adm-badge" :class="`tone-${categoryTone(s.type)}`">{{
                      getTypeName(s.type)
                    }}</span>
                  </td>
                  <td class="adm-wrap">{{ s.description }}</td>
                  <td>{{ formatDate(s.created_at) }}</td>
                  <td>
                    <span class="adm-badge" :class="`tone-${serviceTone(s.status)}`">{{
                      s.status
                    }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- 4. SUPPLIERS -->
      <template v-if="activeTab === 'suppliers'">
        <PageHeader
          eyebrow="Yönetici Paneli"
          title="Tedarikçiler"
          description="Sistemde çalışan servis, lastik, yol yardım ve ikame araç sağlayıcıları."
        >
          <template #actions>
            <UiButton class="adm-btn primary" @click="showAddSupplierModal = true"
              ><NavIcon name="plus" size="16" />Yeni Tedarikçi</UiButton
            >
          </template>
        </PageHeader>

        <div class="adm-kpis">
          <KpiCard label="Toplam Tedarikçi" :value="suppliers.length" icon="store" tone="blue" />
          <KpiCard label="Yetkili" :value="authorizedSuppliersCount" icon="shield" tone="green" />
          <KpiCard
            label="Anlaşmalı"
            :value="contractedSuppliersCount"
            icon="briefcase"
            tone="teal"
          />
        </div>

        <section class="adm-panel">
          <div class="adm-toolbar">
            <label class="adm-search">
              <NavIcon name="search" size="16" />
              <input
                v-model="supplierFilter.search"
                type="search"
                aria-label="Tedarikçi ara"
                placeholder="Tedarikçi adı, il veya ilçe"
              />
            </label>
            <div class="adm-chips" role="group" aria-label="Kategori">
              <span class="adm-chips-label">Kategori</span>
              <button
                v-for="t in [
                  { k: 'Tümü', l: 'Tümü' },
                  { k: 'servis', l: 'Servis' },
                  { k: 'lastik', l: 'Lastik' },
                  { k: 'yol_yardim', l: 'Yol Yardım' },
                  { k: 'ikame_arac', l: 'İkame Araç' },
                ]"
                :key="t.k"
                type="button"
                class="adm-chip"
                :aria-pressed="supplierFilter.type === t.k"
                @click="supplierFilter.type = t.k"
              >
                {{ t.l }}
              </button>
            </div>
            <div class="adm-chips" role="group" aria-label="Sözleşme">
              <span class="adm-chips-label">Sözleşme</span>
              <button
                v-for="ct in ['Tümü', 'Yetkili', 'Anlaşmalı']"
                :key="ct"
                type="button"
                class="adm-chip"
                :aria-pressed="supplierFilter.contractType === ct"
                @click="supplierFilter.contractType = ct"
              >
                {{ ct }}
              </button>
            </div>
            <span class="adm-count"
              >{{ filteredSuppliers.length }} / {{ suppliers.length }} tedarikçi</span
            >
          </div>

          <p v-if="loading" class="adm-loading">Yükleniyor…</p>
          <EmptyState
            v-else-if="filteredSuppliers.length === 0"
            icon="store"
            title="Kriterlere uygun tedarikçi yok"
            :text="
              suppliers.length ? 'Filtreleri değiştirmeyi deneyin.' : 'Henüz tedarikçi eklenmedi.'
            "
          />
          <div v-else class="adm-table-wrap">
            <table class="custom-table adm-table">
              <thead>
                <tr>
                  <th>Tedarikçi</th>
                  <th>Kategori</th>
                  <th>Konum</th>
                  <th>İletişim</th>
                  <th>Portal</th>
                  <th>Hizmetler</th>
                  <th class="adm-actions-col">İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in filteredSuppliers" :key="s.id">
                  <td>
                    <div class="adm-cell-title">{{ s.name }}</div>
                    <div class="adm-cell-sub">
                      #{{ s.id
                      }}<template v-if="s.contract_type"> · {{ s.contract_type }}</template>
                    </div>
                  </td>
                  <td>
                    <span class="adm-badge" :class="`tone-${categoryTone(s.type)}`">{{
                      getTypeName(s.type)
                    }}</span>
                  </td>
                  <td>{{ [s.city, s.district].filter(Boolean).join(' / ') || '—' }}</td>
                  <td>
                    <div>{{ s.phone || '—' }}</div>
                    <div class="adm-cell-sub">{{ s.email || 'E-posta yok' }}</div>
                  </td>
                  <td>
                    <span class="adm-badge" :class="`tone-${inviteTone(s.invitation_status)}`">{{
                      inviteLabel(s.invitation_status)
                    }}</span>
                  </td>
                  <td>
                    <div class="adm-tags">
                      <span v-for="serv in s.services" :key="serv" class="adm-tag">{{ serv }}</span>
                    </div>
                  </td>
                  <td class="adm-actions-col">
                    <div class="adm-actions">
                      <UiButton
                        class="adm-btn sm teal"
                        title="Destek için bu tedarikçinin portalına gir"
                        @click="enterAccount('supplier', s.id, s.name)"
                        ><NavIcon name="login" size="15" />Hesaba Gir</UiButton
                      >
                      <UiButton class="adm-btn sm ghost" @click="sendSupplierInvite(s)"
                        ><NavIcon name="mail" size="15" />{{
                          s.invitation_status === 'Davet Gönderildi' ? 'Yeniden Davet' : 'Davet Et'
                        }}</UiButton
                      >
                      <UiButton
                        class="adm-btn sm danger icon"
                        :aria-label="`${s.name} tedarikçisini sil`"
                        title="Sil"
                        @click="deleteSupplier(s)"
                        ><NavIcon name="trash" size="15"
                      /></UiButton>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- 5. SUPPORT ACCESS LOG -->
      <template v-if="activeTab === 'support'">
        <PageHeader
          eyebrow="Yönetici Paneli"
          title="Destek Kayıtları"
          description="Yöneticilerin destek için girdiği firma hesapları. Bu kayıtları firmalar görmez."
        >
          <template #actions>
            <UiButton class="adm-btn ghost" :disabled="supportLoading" @click="loadSupportLog"
              ><NavIcon name="refresh" size="16" />Yenile</UiButton
            >
          </template>
        </PageHeader>
        <p v-if="supportError" class="admin-support-error" role="alert">{{ supportError }}</p>
        <section class="adm-panel">
          <p v-if="supportLoading && !supportLog.length" class="adm-loading">Yükleniyor…</p>
          <EmptyState
            v-else-if="!supportLog.length"
            icon="shield"
            title="Henüz destek girişi yapılmadı"
            text="Bir firmanın hesabına Hesaba Gir ile girdiğinizde kayıt burada görünür."
          />
          <div v-else class="adm-table-wrap">
            <table class="data-table adm-table">
              <thead>
                <tr>
                  <th>Firma</th>
                  <th>Portal</th>
                  <th>Yönetici</th>
                  <th>Giriş</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in supportLog" :key="row.id">
                  <td class="adm-cell-title">{{ row.subject_name || '#' + row.subject_id }}</td>
                  <td>{{ row.portal === 'supplier' ? 'Tedarikçi' : 'Müşteri' }}</td>
                  <td>{{ row.admin_email }}</td>
                  <td>{{ formatDateTime(row.started_at) }}</td>
                  <td>
                    <span class="adm-badge" :class="row.active ? 'tone-amber' : 'tone-gray'">{{
                      row.active ? 'Açık' : `Kapandı · ${formatDateTime(row.ended_at)}`
                    }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
      <ManualSignatureInbox v-if="activeTab !== 'support'" account="admin" />
    </main>
  </div>

  <!-- Add Quote Modal -->
  <UiModal v-if="showAddQuoteModal" class="modal-overlay" @close="showAddQuoteModal = false">
    <div class="glass-panel modal-content adm-modal" style="max-width: 550px; padding: 30px">
      <h2 class="adm-modal-title">Yeni Teklif Talebi Oluştur</h2>

      <form @submit.prevent="addQuote">
        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Şirket Adı</UiField>
          <input
            type="text"
            v-model="newQuoteForm.company_name"
            required
            class="form-input"
            placeholder="Örn: Beta Lojistik Ltd."
          />
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">E-posta</UiField>
            <input
              type="email"
              v-model="newQuoteForm.email"
              required
              class="form-input"
              placeholder="info@betalojistik.com"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Telefon</UiField>
            <input
              type="text"
              v-model="newQuoteForm.phone"
              required
              class="form-input"
              placeholder="+90 216 444 0222"
            />
          </div>
        </div>

        <div
          class="grid-3"
          style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px"
        >
          <div class="form-group">
            <UiField class="form-label">Araç Sayısı</UiField>
            <input
              type="number"
              min="1"
              v-model.number="newQuoteForm.vehicle_count"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Kiralama Süresi (Ay)</UiField>
            <select v-model.number="newQuoteForm.duration_months" required class="form-select">
              <option :value="12">12 Ay</option>
              <option :value="24">24 Ay</option>
              <option :value="36">36 Ay</option>
              <option :value="48">48 Ay</option>
            </select>
          </div>
          <div class="form-group">
            <UiField class="form-label">Yıllık KM Sınırı</UiField>
            <select
              v-model.number="newQuoteForm.estimated_annual_mileage"
              required
              class="form-select"
            >
              <option :value="10000">10,000 km</option>
              <option :value="20000">20,000 km</option>
              <option :value="30000">30,000 km</option>
              <option :value="40000">40,000 km</option>
            </select>
          </div>
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 25px">
          <div class="form-group">
            <UiField class="form-label">Araç Segmenti</UiField>
            <select v-model="newQuoteForm.vehicle_segment" required class="form-select">
              <option value="A">A Segmenti (Mikro/Şehir)</option>
              <option value="B">B Segmenti (Küçük/Hatchback)</option>
              <option value="C">C Segmenti (Orta/Sedan)</option>
              <option value="D">D Segmenti (Üst/Prestij)</option>
              <option value="E">E Segmenti (Premium/Lüks)</option>
            </select>
          </div>
          <div class="form-group">
            <UiField class="form-label">Araç Tipi</UiField>
            <select v-model="newQuoteForm.vehicle_type" required class="form-select">
              <option value="Sedan">Sedan</option>
              <option value="SUV">SUV</option>
              <option value="Hatchback">Hatchback</option>
              <option value="Hafif Ticari">Hafif Ticari</option>
              <option value="Station Wagon">Station Wagon</option>
            </select>
          </div>
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
          <UiButton type="button" @click="showAddQuoteModal = false" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: var(--fr-primary); color: #fff; border: none"
          >
            Teklifi Kaydet
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Edit Quote Modal -->
  <UiModal v-if="showEditQuoteModal" class="modal-overlay" @close="showEditQuoteModal = false">
    <div class="glass-panel modal-content adm-modal" style="max-width: 550px; padding: 30px">
      <h2 class="adm-modal-title">Teklif Talebi Düzenle</h2>

      <form @submit.prevent="submitEditQuote">
        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Şirket Adı</UiField>
          <input type="text" v-model="editQuoteForm.company_name" required class="form-input" />
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">E-posta</UiField>
            <input type="email" v-model="editQuoteForm.email" required class="form-input" />
          </div>
          <div class="form-group">
            <UiField class="form-label">Telefon</UiField>
            <input type="text" v-model="editQuoteForm.phone" required class="form-input" />
          </div>
        </div>

        <div
          class="grid-3"
          style="gap: 15px; grid-template-columns: 1fr 1fr 1fr; margin-bottom: 15px"
        >
          <div class="form-group">
            <UiField class="form-label">Araç Sayısı</UiField>
            <input
              type="number"
              min="1"
              v-model.number="editQuoteForm.vehicle_count"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Kiralama Süresi (Ay)</UiField>
            <select v-model.number="editQuoteForm.duration_months" required class="form-select">
              <option :value="12">12 Ay</option>
              <option :value="24">24 Ay</option>
              <option :value="36">36 Ay</option>
              <option :value="48">48 Ay</option>
            </select>
          </div>
          <div class="form-group">
            <UiField class="form-label">Yıllık KM Sınırı</UiField>
            <select
              v-model.number="editQuoteForm.estimated_annual_mileage"
              required
              class="form-select"
            >
              <option :value="10000">10,000 km</option>
              <option :value="20000">20,000 km</option>
              <option :value="30000">30,000 km</option>
              <option :value="40000">40,000 km</option>
            </select>
          </div>
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">Araç Segmenti</UiField>
            <select v-model="editQuoteForm.vehicle_segment" required class="form-select">
              <option value="A">A Segmenti</option>
              <option value="B">B Segmenti</option>
              <option value="C">C Segmenti</option>
              <option value="D">D Segmenti</option>
              <option value="E">E Segmenti</option>
            </select>
          </div>
          <div class="form-group">
            <UiField class="form-label">Araç Tipi</UiField>
            <select v-model="editQuoteForm.vehicle_type" required class="form-select">
              <option value="Sedan">Sedan</option>
              <option value="SUV">SUV</option>
              <option value="Hatchback">Hatchback</option>
              <option value="Hafif Ticari">Hafif Ticari</option>
              <option value="Station Wagon">Station Wagon</option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 25px">
          <UiField class="form-label">Aylık Toplam Bedel (₺)</UiField>
          <input
            type="number"
            min="0"
            v-model.number="editQuoteForm.monthly_price_try"
            required
            class="form-input"
          />
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
          <UiButton type="button" @click="showEditQuoteModal = false" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: var(--fr-primary); color: #fff; border: none"
          >
            Değişiklikleri Kaydet
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Edit Customer Modal -->
  <UiModal
    v-if="showEditCustomerModal"
    class="modal-overlay"
    @close="showEditCustomerModal = false"
  >
    <div class="glass-panel modal-content adm-modal" style="max-width: 550px; padding: 30px">
      <h2 class="adm-modal-title">Müşteri Bilgilerini Düzenle</h2>

      <form @submit.prevent="submitEditCustomer">
        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Şirket Adı</UiField>
          <input type="text" v-model="editCustomerForm.company_name" required class="form-input" />
        </div>

        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Ticari Unvan</UiField>
          <input type="text" v-model="editCustomerForm.legal_title" required class="form-input" />
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">E-posta</UiField>
            <input type="email" v-model="editCustomerForm.email" required class="form-input" />
          </div>
          <div class="form-group">
            <UiField class="form-label">Telefon</UiField>
            <input type="text" v-model="editCustomerForm.phone" required class="form-input" />
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Adres</UiField>
          <input type="text" v-model="editCustomerForm.address" required class="form-input" />
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 25px">
          <div class="form-group">
            <UiField class="form-label">Kayıtlı Araç Sayısı</UiField>
            <input
              type="number"
              min="0"
              v-model.number="editCustomerForm.registered_vehicles_count"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Aylık Sözleşme Bedeli (₺)</UiField>
            <input
              type="number"
              min="0"
              v-model.number="editCustomerForm.contract_amount"
              required
              class="form-input"
            />
          </div>
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
          <UiButton type="button" @click="showEditCustomerModal = false" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: #047857; color: #fff; border: none"
          >
            Değişiklikleri Kaydet
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Contract Amount Prompt Modal -->
  <UiModal v-if="showAmountModal" class="modal-overlay" @close="cancelContractSigning">
    <div class="glass-panel modal-content adm-modal" style="max-width: 450px; padding: 30px">
      <h2 class="adm-modal-title">Sözleşme İmzalama İşlemi</h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px">
        Teklif onaylandı ve sözleşme imzalanma aşamasına geçildi. Lütfen sözleşmenin kesinleşen
        **Aylık Toplam İmza Tutarını (₺)** giriniz:
      </p>

      <form @submit.prevent="confirmContractSigning">
        <div class="form-group" style="margin-bottom: 25px">
          <UiField class="form-label">Sözleşme Aylık Bedeli (₺)</UiField>
          <input
            type="number"
            min="0"
            v-model.number="contractAmountInput"
            required
            class="form-input"
            placeholder="Örn: 425000"
          />
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
          <UiButton type="button" @click="cancelContractSigning" class="btn btn-secondary"
            >Vazgeç</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: #047857; color: #fff; border: none"
          >
            Sözleşmeyi İmzala & Müşteriyi Aktifleştir
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Supplier Bids List Modal (Admin view) -->
  <UiModal v-if="showBidsModal" class="modal-overlay" @close="showBidsModal = false">
    <div class="glass-panel modal-content adm-modal" style="max-width: 800px; padding: 30px">
      <div
        style="
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 15px;
          margin-bottom: 20px;
        "
      >
        <h2 class="adm-modal-title">Tedarikçi Teklifleri (Bids)</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 5px">
          <strong>{{ selectedQuoteForBids?.company_name }}</strong> firmasının
          {{ selectedQuoteForBids?.vehicle_count }} adet
          {{ selectedQuoteForBids?.vehicle_segment }} Segment
          {{ selectedQuoteForBids?.vehicle_type }} kiralama talebi için tedarikçilerden gelen
          teklifler.
        </p>
      </div>

      <div v-if="bidsLoading" class="text-center" style="padding: 30px 0">Yükleniyor...</div>
      <div v-else-if="selectedQuoteBids.length === 0" class="empty-state" style="padding: 30px 0">
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
              <th style="width: 150px">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="bid in selectedQuoteBids" :key="bid.id">
              <td>
                <strong>{{ bid.supplier_name }}</strong>
              </td>
              <td>
                <strong style="color: #047857"
                  >₺{{ bid.monthly_price_try?.toLocaleString() }}</strong
                >
              </td>
              <td style="font-size: 0.8rem; max-width: 250px; white-space: normal">
                {{ bid.notes }}
              </td>
              <td style="font-size: 0.8rem">{{ formatDate(bid.created_at) }}</td>
              <td>
                <span
                  class="badge"
                  :class="getBidBadgeClass(bid.status)"
                  style="font-size: 0.75rem; padding: 4px 8px"
                >
                  {{ bid.status }}
                </span>
              </td>
              <td>
                <div v-if="bid.status === 'Beklemede'" style="display: flex; gap: 6px">
                  <UiButton
                    @click="acceptSupplierBid(bid.id)"
                    class="btn btn-secondary"
                    style="
                      padding: 4px 8px;
                      font-size: 0.75rem;
                      background: rgba(16, 185, 129, 0.1);
                      color: #047857;
                      border-color: rgba(16, 185, 129, 0.2);
                    "
                  >
                    Kabul Et
                  </UiButton>
                  <UiButton
                    @click="rejectSupplierBid(bid.id)"
                    class="btn btn-secondary"
                    style="
                      padding: 4px 8px;
                      font-size: 0.75rem;
                      background: rgba(239, 68, 68, 0.1);
                      color: #dc2626;
                      border-color: rgba(239, 68, 68, 0.2);
                    "
                  >
                    ✕ Reddet
                  </UiButton>
                </div>
                <span v-else style="color: var(--text-muted); font-size: 0.8rem">İşlem Tamam</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div
        style="
          display: flex;
          justify-content: flex-end;
          border-top: 1px solid var(--border-color);
          padding-top: 15px;
          margin-top: 20px;
        "
      >
        <UiButton @click="showBidsModal = false" class="btn btn-secondary">Kapat</UiButton>
      </div>
    </div>
  </UiModal>

  <!-- Add Supplier Modal -->
  <UiModal v-if="showAddSupplierModal" class="modal-overlay" @close="closeAddSupplierModal">
    <div class="glass-panel modal-content adm-modal" style="max-width: 620px; padding: 30px">
      <div
        style="
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 22px;
        "
      >
        <h2 class="adm-modal-title">Yeni Tedarikçi Ekle</h2>
        <UiButton
          @click="closeAddSupplierModal"
          style="
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.4rem;
            cursor: pointer;
            line-height: 1;
          "
          >✕</UiButton
        >
      </div>

      <form @submit.prevent="submitAddSupplier">
        <!-- Tedarikçi Adı -->
        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Tedarikçi Adı *</UiField>
          <input
            type="text"
            v-model="newSupplierForm.name"
            required
            class="form-input"
            placeholder="Örn: OtoPratik Bağcılar"
          />
        </div>

        <!-- Kategori & Servis Tipi -->
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">Kategori *</UiField>
            <select v-model="newSupplierForm.type" required class="form-select">
              <option value="">Seçiniz...</option>
              <option value="servis">Yetkili / Anlaşmalı Servis</option>
              <option value="lastik">Lastik Bayi</option>
              <option value="yol_yardim">Yol Yardım</option>
              <option value="ikame_arac">İkame Araç</option>
            </select>
          </div>
          <div class="form-group">
            <UiField class="form-label">Sözleşme Tipi *</UiField>
            <select v-model="newSupplierForm.contract_type" required class="form-select">
              <option value="">Seçiniz...</option>
              <option value="Yetkili">Yetkili Servis</option>
              <option value="Anlaşmalı">Anlaşmalı Servis</option>
            </select>
          </div>
        </div>

        <!-- İl & İlçe -->
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">İl *</UiField>
            <input
              type="text"
              v-model="newSupplierForm.city"
              required
              class="form-input"
              placeholder="Örn: İstanbul"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">İlçe *</UiField>
            <input
              type="text"
              v-model="newSupplierForm.district"
              required
              class="form-input"
              placeholder="Örn: Bağcılar"
            />
          </div>
        </div>

        <!-- Telefon & E-posta -->
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">Telefon *</UiField>
            <input
              type="text"
              v-model="newSupplierForm.phone"
              required
              class="form-input"
              placeholder="+90 212 555 0000"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">E-posta Adresi (Portal Girişi İçin)</UiField>
            <input
              type="email"
              v-model="newSupplierForm.email"
              class="form-input"
              placeholder="yetkili@servis.com"
            />
          </div>
        </div>

        <!-- Davetiye Gönder Seçeneği -->
        <div
          v-if="newSupplierForm.email"
          class="form-group"
          style="
            margin-bottom: 18px;
            background: rgba(0, 100, 255, 0.05);
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid rgba(0, 100, 255, 0.15);
          "
        >
          <UiField
            style="
              display: flex;
              align-items: center;
              gap: 10px;
              cursor: pointer;
              font-size: 0.88rem;
              font-weight: 600;
              color: var(--fr-primary);
              margin: 0;
            "
          >
            <input
              type="checkbox"
              v-model="newSupplierForm.send_invite"
              style="width: 18px; height: 18px; accent-color: var(--fr-primary)"
            />
            <span>Tedarikçiye şifre oluşturma davetiye e-postası gönderilsin</span>
          </UiField>
        </div>

        <!-- Hizmetler (tag input) -->
        <div class="form-group" style="margin-bottom: 22px">
          <UiField class="form-label">Sunduğu Hizmetler</UiField>
          <div class="supplier-tag-input-wrap">
            <div class="supplier-tags">
              <span v-for="(svc, i) in newSupplierForm.services" :key="i" class="supplier-tag-chip">
                {{ svc }}
                <UiButton type="button" @click="removeService(i)" class="chip-remove">✕</UiButton>
              </span>
              <input
                v-model="serviceInput"
                @keydown="handleServiceTagKeydown"
                class="tag-bare-input"
                placeholder="Hizmet yazıp Enter'a basın..."
              />
            </div>
          </div>
          <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 6px">
            Örn: Periyodik Bakım · Fren Sistemi · Akü Değişimi
          </p>
        </div>

        <div
          style="
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            border-top: 1px solid var(--border-color);
            padding-top: 15px;
          "
        >
          <UiButton type="button" @click="closeAddSupplierModal" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: var(--fr-primary); border: none"
          >
            Tedarikçiyi Kaydet
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Add Customer Modal -->
  <UiModal v-if="showAddCustomerModal" class="modal-overlay" @close="showAddCustomerModal = false">
    <div class="glass-panel modal-content adm-modal" style="max-width: 620px; padding: 30px">
      <div
        style="
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 22px;
        "
      >
        <h2 class="adm-modal-title">Yeni Müşteri Kaydı Ekle</h2>
        <UiButton
          @click="showAddCustomerModal = false"
          style="
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.4rem;
            cursor: pointer;
            line-height: 1;
          "
          >✕</UiButton
        >
      </div>

      <form @submit.prevent="submitNewCustomer">
        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">Şirket Adı *</UiField>
            <input
              type="text"
              v-model="newCustomerForm.company_name"
              required
              class="form-input"
              placeholder="Örn: Tekno Holding"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Ticari Unvan *</UiField>
            <input
              type="text"
              v-model="newCustomerForm.legal_title"
              required
              class="form-input"
              placeholder="Tekno Holding A.Ş."
            />
          </div>
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 15px">
          <div class="form-group">
            <UiField class="form-label">E-posta Adresi *</UiField>
            <input
              type="email"
              v-model="newCustomerForm.email"
              required
              class="form-input"
              placeholder="info@teknoholding.com"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Telefon Numarası *</UiField>
            <input
              type="tel"
              v-model="newCustomerForm.phone"
              required
              class="form-input"
              placeholder="+90 212 555 0000"
            />
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 15px">
          <UiField class="form-label">Adres *</UiField>
          <input
            type="text"
            v-model="newCustomerForm.address"
            required
            class="form-input"
            placeholder="Maslak Plazalar No: 18, Şişli, İstanbul"
          />
        </div>

        <div class="grid-2" style="gap: 15px; grid-template-columns: 1fr 1fr; margin-bottom: 20px">
          <div class="form-group">
            <UiField class="form-label">Sözleşmeli Araç Sayısı *</UiField>
            <input
              type="number"
              v-model.number="newCustomerForm.registered_vehicles_count"
              required
              min="1"
              class="form-input"
              placeholder="10"
            />
          </div>
          <div class="form-group">
            <UiField class="form-label">Aylık Sözleşme Bedeli (₺) *</UiField>
            <input
              type="number"
              v-model.number="newCustomerForm.contract_amount"
              required
              min="0"
              class="form-input"
              placeholder="250000"
            />
          </div>
        </div>

        <div
          class="form-group"
          style="
            margin-bottom: 25px;
            background: rgba(16, 185, 129, 0.05);
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid rgba(16, 185, 129, 0.2);
          "
        >
          <UiField
            style="
              display: flex;
              align-items: center;
              gap: 10px;
              cursor: pointer;
              margin: 0;
              color: var(--text-main);
              font-weight: 600;
              font-size: 0.88rem;
            "
          >
            <input
              type="checkbox"
              v-model="newCustomerForm.send_invite"
              style="width: 18px; height: 18px; accent-color: #10b981; cursor: pointer"
            />
            <span
              >Müşteriye Kurumsal Giriş Daveti Gönder (E-posta ile Şifre Belirleme Bağlantısı)</span
            >
          </UiField>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end">
          <UiButton type="button" @click="showAddCustomerModal = false" class="btn btn-secondary"
            >İptal</UiButton
          >
          <UiButton
            type="submit"
            class="btn btn-primary"
            style="background: var(--fr-primary); border: none"
          >
            Müşteriyi Kaydet
          </UiButton>
        </div>
      </form>
    </div>
  </UiModal>

  <!-- Supplier Invite Link Result Modal -->
  <UiModal v-if="showInviteModal" class="modal-overlay" @close="showInviteModal = false">
    <div
      class="glass-panel modal-content adm-modal"
      style="max-width: 560px; padding: 30px; border-radius: 20px"
    >
      <div
        style="
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
        "
      >
        <h2 class="adm-modal-title">Tedarikçi Davet Bağlantısı</h2>
        <UiButton
          @click="showInviteModal = false"
          style="
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.4rem;
            cursor: pointer;
            line-height: 1;
          "
          >✕</UiButton
        >
      </div>

      <!-- E-posta Gönderim Durum Bildirimi -->
      <div
        v-if="inviteResult.email_sent"
        style="
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 12px;
          padding: 14px 16px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 12px;
        "
      >
        <NavIcon name="check" size="22" style="color: var(--fr-success)" />
        <div>
          <strong style="color: #047857; font-size: 0.92rem"
            >E-Posta Adresine Başarıyla Gönderildi!</strong
          >
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px">
            Davetiye e-postası {{ inviteResult.email }} adresine iletildi.
          </div>
        </div>
      </div>

      <div
        v-else
        style="
          background: rgba(245, 158, 11, 0.08);
          border: 1px solid rgba(245, 158, 11, 0.25);
          border-radius: 12px;
          padding: 14px 16px;
          margin-bottom: 20px;
          display: flex;
          align-items: flex-start;
          gap: 12px;
        "
      >
        <NavIcon name="alert" size="22" style="color: var(--fr-warning)" />
        <div>
          <strong style="color: #b45309; font-size: 0.92rem"
            >Davet Bağlantısı Hazırlandı (Manuel İletilebilir)</strong
          >
          <div
            style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; line-height: 1.4"
          >
            SMTP e-posta ayarları yapılmadığı için e-posta doğrudan ulaştırılamadı. Aşağıdaki davet
            bağlantısını kopyalayarak WhatsApp veya e-posta ile doğrudan iletebilirsiniz.
          </div>
        </div>
      </div>

      <!-- Tedarikçi Detay Kartı -->
      <div
        style="
          background: rgba(0, 100, 255, 0.04);
          border: 1px solid rgba(0, 100, 255, 0.12);
          border-radius: 12px;
          padding: 14px 16px;
          margin-bottom: 20px;
        "
      >
        <div style="font-size: 0.88rem; margin-bottom: 4px; color: var(--text-main)">
          <strong>Tedarikçi / Servis:</strong> {{ inviteResult.supplier_name }}
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted)">
          <strong>E-posta:</strong> {{ inviteResult.email }}
        </div>
      </div>

      <!-- Davet Linki Input Kutusu -->
      <div class="form-group" style="margin-bottom: 22px">
        <UiField class="form-label" style="font-weight: 600; color: #334155"
          >Şifre Oluşturma Davet Bağlantısı</UiField
        >
        <div style="display: flex; gap: 8px">
          <input
            type="text"
            readonly
            :value="inviteResult.invite_url"
            class="form-input"
            style="font-family: monospace; font-size: 0.82rem; background: #f8fafc; color: #0f172a"
          />
          <UiButton
            @click="copyInviteUrl"
            class="btn"
            style="
              white-space: nowrap;
              border-color: var(--fr-primary);
              color: #ffffff;
              background: var(--fr-primary);
              font-weight: 600;
              padding: 0 16px;
            "
          >
            {{ copied ? 'Kopyalandı!' : 'Linki Kopyala' }}
          </UiButton>
        </div>
      </div>

      <!-- WhatsApp / Manuel Paylaşım -->
      <div
        style="
          display: flex;
          gap: 12px;
          justify-content: space-between;
          border-top: 1px solid var(--border-color);
          padding-top: 18px;
        "
      >
        <a
          :href="whatsappShareUrl"
          target="_blank"
          class="btn"
          style="
            background: #25d366;
            color: #ffffff;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 0.88rem;
            border-radius: 10px;
            padding: 10px 18px;
            box-shadow: 0 4px 12px rgba(37, 211, 102, 0.25);
          "
        >
          WhatsApp İle Gönder
        </a>
        <UiButton @click="showInviteModal = false" class="btn btn-secondary"
          >Tamam / Kapat</UiButton
        >
      </div>
    </div>
  </UiModal>
</template>

<script setup>
import { askText, confirmAction, notify } from '../utils/feedback.js'
import {
  EmptyState,
  KpiCard,
  PageHeader,
  UiButton,
  UiField,
  UiModal,
} from '../components/ui/index.js'
import Sidebar from '../components/Sidebar.vue'

import { ref, reactive, computed, onMounted, watch } from 'vue'
import ManualSignatureInbox from '../components/ManualSignatureInbox.vue'
import { useRoute, useRouter } from 'vue-router'
import { startImpersonation } from '../api/impersonation.js'
import { apiRequest } from '../api/http.js'
import NavIcon from '../components/NavIcon.vue'

const router = useRouter()
const route = useRoute()

// The section lives in the address (?tab=), so the shared sidebar, the back button and
// reloads all land on the same tab.
const ADMIN_TABS = ['quotes', 'customers', 'vehicles', 'suppliers', 'support']
const activeTab = computed(() =>
  ADMIN_TABS.includes(route.query.tab) ? route.query.tab : 'quotes',
)
const QUOTE_STATUSES = [
  'Teklif Bekleniyor',
  'Teklif Verildi',
  'Değerlendirmede',
  'Kabul Edildi',
  'Sözleşme İmzalandı',
  'Reddedildi',
  'İstek Silindi',
]
const money = (value) =>
  value === null || value === undefined || value === ''
    ? '—'
    : `₺${Number(value).toLocaleString('tr-TR')}`
const isDeletedQuote = (quote) => ['İstek Silindi', 'Silindi'].includes(quote.status)
// One colour vocabulary for every badge on the page (matches KpiCard tones).
const quoteTone = (status) =>
  ({
    'Teklif Bekleniyor': 'amber',
    'Teklif Verildi': 'blue',
    Değerlendirmede: 'violet',
    'Kabul Edildi': 'green',
    'Sözleşme İmzalandı': 'green',
    Reddedildi: 'red',
    'İstek Silindi': 'gray',
    Silindi: 'gray',
  })[status] || 'gray'
const vehicleTone = (status) =>
  ({ Aktif: 'green', Serviste: 'amber', 'Lastik Değişiminde': 'blue', 'Yol Yardımında': 'red' })[
    status
  ] || 'gray'
const serviceTone = (status) =>
  status === 'Tamamlandı' ? 'green' : status === 'Beklemede' ? 'amber' : 'blue'
const categoryTone = (type) =>
  ({ servis: 'blue', lastik: 'teal', yol_yardim: 'red', ikame_arac: 'violet' })[type] || 'gray'
const inviteTone = (status) =>
  status === 'Aktif' ? 'green' : status === 'Davet Gönderildi' ? 'amber' : 'gray'
const inviteLabel = (status) =>
  status === 'Aktif'
    ? 'Aktif'
    : status === 'Davet Gönderildi'
      ? 'Davet gönderildi'
      : 'Davet edilmedi'
const supportLog = ref([]),
  supportLoading = ref(false),
  supportError = ref('')
async function loadSupportLog() {
  supportLoading.value = true
  supportError.value = ''
  try {
    supportLog.value = await apiRequest('/api/admin/impersonation-log', { account: 'admin' })
  } catch (error) {
    supportError.value = error?.message || 'Destek kayıtları yüklenemedi.'
  } finally {
    supportLoading.value = false
  }
}
function openTab(id) {
  if (activeTab.value !== id)
    router.push({ path: '/admin-portal', query: id === 'quotes' ? {} : { tab: id } })
}
watch(
  activeTab,
  (tab) => {
    if (tab === 'support') loadSupportLog()
  },
  { immediate: true },
)
const formatDateTime = (value) =>
  value
    ? new Date(value).toLocaleString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'

async function enterAccount(portal, subjectId, name) {
  const label = portal === 'supplier' ? 'tedarikçi' : 'müşteri'
  if (
    !(await confirmAction(
      `${name} adlı ${label} hesabına destek için gireceksiniz. Devam edilsin mi?`,
      { confirmText: 'Hesaba Gir' },
    ))
  )
    return
  try {
    const path = await startImpersonation(portal, subjectId)
    router.push(path)
  } catch (error) {
    notify(error?.message || 'Hesaba girilemedi.')
  }
}

// ── Filter state ─────────────────────────────────────────────────────────
const quoteFilter = reactive({ search: '', status: 'Tümü', segment: 'Tümü' })
const customerFilter = reactive({ search: '', fleetStatus: 'Tümü' })
const supplierFilter = reactive({ search: '', type: 'Tümü', contractType: 'Tümü' })

const getQuoteTierPriority = (status) => {
  if (['Teklif Bekleniyor', 'Teklif Geldi', 'Teklif Verildi', 'Değerlendirmede'].includes(status))
    return 1
  if (['Kabul Edildi', 'Sözleşme İmzalandı', 'Sözleşme Yapıldı'].includes(status)) return 2
  if (['İstek Silindi', 'Silindi', 'Reddedildi'].includes(status)) return 3
  return 1
}

const filteredQuotes = computed(() => {
  const list = quotes.value.filter((q) => {
    const matchSearch =
      !quoteFilter.search ||
      q.company_name?.toLowerCase().includes(quoteFilter.search.toLowerCase()) ||
      q.email?.toLowerCase().includes(quoteFilter.search.toLowerCase())

    let matchStatus
    if (quoteFilter.status === 'Tümü') matchStatus = true
    else if (quoteFilter.status === 'Teklif Bekleniyor')
      matchStatus = q.status === 'Teklif Bekleniyor'
    else if (quoteFilter.status === 'Teklif Geldi')
      matchStatus =
        q.status === 'Teklif Geldi' ||
        q.status === 'Teklif Verildi' ||
        (q.bids &&
          q.bids.length > 0 &&
          ![
            'Kabul Edildi',
            'Sözleşme İmzalandı',
            'Sözleşme Yapıldı',
            'İstek Silindi',
            'Silindi',
            'Reddedildi',
          ].includes(q.status))
    else if (quoteFilter.status === 'Sözleşme Yapıldı')
      matchStatus = ['Sözleşme Yapıldı', 'Kabul Edildi', 'Sözleşme İmzalandı'].includes(q.status)
    else if (quoteFilter.status === 'Silinen')
      matchStatus = ['İstek Silindi', 'Silindi', 'Reddedildi'].includes(q.status)
    else matchStatus = q.status === quoteFilter.status

    const matchSegment = quoteFilter.segment === 'Tümü' || q.vehicle_segment === quoteFilter.segment
    return matchSearch && matchStatus && matchSegment
  })

  return [...list].sort((a, b) => {
    const priorityA = getQuoteTierPriority(a.status)
    const priorityB = getQuoteTierPriority(b.status)
    if (priorityA !== priorityB) {
      return priorityA - priorityB
    }
    const timeA = a.created_at ? new Date(a.created_at).getTime() : a.id || 0
    const timeB = b.created_at ? new Date(b.created_at).getTime() : b.id || 0
    return timeB - timeA
  })
})

const filteredCustomers = computed(() => {
  return customers.value.filter((c) => {
    const matchSearch =
      !customerFilter.search ||
      c.company_name?.toLowerCase().includes(customerFilter.search.toLowerCase()) ||
      c.email?.toLowerCase().includes(customerFilter.search.toLowerCase()) ||
      c.phone?.includes(customerFilter.search)
    const matchFleet =
      customerFilter.fleetStatus === 'Tümü' ||
      (customerFilter.fleetStatus === 'Eksikli' && (c.vehicle_deficit || 0) > 0) ||
      (customerFilter.fleetStatus === 'Tam' && (c.vehicle_deficit || 0) === 0)
    return matchSearch && matchFleet
  })
})

const filteredSuppliers = computed(() => {
  return suppliers.value.filter((s) => {
    const matchSearch =
      !supplierFilter.search ||
      s.name?.toLowerCase().includes(supplierFilter.search.toLowerCase()) ||
      s.city?.toLowerCase().includes(supplierFilter.search.toLowerCase()) ||
      s.district?.toLowerCase().includes(supplierFilter.search.toLowerCase())
    const matchType = supplierFilter.type === 'Tümü' || s.type === supplierFilter.type
    const matchContract =
      supplierFilter.contractType === 'Tümü' || s.contract_type === supplierFilter.contractType
    return matchSearch && matchType && matchContract
  })
})

// ── Vehicles tab state & filters ──────────────────────────────────────────
const vehicles = ref([])
const vehicleFilter = reactive({ search: '', status: 'Tümü', fuel: 'Tümü' })

const filteredVehicles = computed(() => {
  return vehicles.value.filter((v) => {
    const matchSearch =
      !vehicleFilter.search ||
      v.plate?.toLowerCase().includes(vehicleFilter.search.toLowerCase()) ||
      v.brand?.toLowerCase().includes(vehicleFilter.search.toLowerCase()) ||
      v.model?.toLowerCase().includes(vehicleFilter.search.toLowerCase()) ||
      v.chassis_no?.toLowerCase().includes(vehicleFilter.search.toLowerCase())
    const matchStatus = vehicleFilter.status === 'Tümü' || v.status === vehicleFilter.status
    const matchFuel = vehicleFilter.fuel === 'Tümü' || v.fuel === vehicleFilter.fuel
    return matchSearch && matchStatus && matchFuel
  })
})

const activeVehiclesCount = computed(() => {
  return vehicles.value.filter((v) => v.status === 'Aktif' && v.is_active).length
})

const serviceVehiclesCount = computed(() => {
  return vehicles.value.filter(
    (v) => ['Serviste', 'Lastik Değişiminde', 'Yol Yardımında'].includes(v.status) && v.is_active,
  ).length
})

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
  estimated_annual_mileage: 20000,
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
  status: '',
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
  contract_amount: 0,
})

// Customer Detail View State
const showAddCustomerModal = ref(false)
const newCustomerForm = reactive({
  company_name: '',
  legal_title: '',
  email: '',
  phone: '',
  address: '',
  registered_vehicles_count: 1,
  contract_amount: 0,
  send_invite: false,
})

const submitNewCustomer = async () => {
  const shouldInvite = newCustomerForm.send_invite
  try {
    const res = await fetch('/api/admin/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCustomerForm),
    })
    if (res.ok) {
      const added = await res.json()
      showAddCustomerModal.value = false
      await fetchCustomers()

      if (shouldInvite && added.id) {
        await sendCustomerInvite(added)
      } else {
        notify(`${newCustomerForm.company_name} başarıyla müşteri olarak eklendi!`)
      }

      Object.assign(newCustomerForm, {
        company_name: '',
        legal_title: '',
        email: '',
        phone: '',
        address: '',
        registered_vehicles_count: 1,
        contract_amount: 0,
        send_invite: false,
      })
    } else {
      const err = await res.json().catch(() => ({}))
      notify('Müşteri eklenirken bir hata oluştu: ' + (err.detail || 'Bilinmeyen hata.'))
    }
  } catch (err) {
    console.error('Müşteri ekleme hatası:', err)
    notify('Sunucuya bağlanılamadı.')
  }
}

const sendCustomerInvite = async (customer) => {
  try {
    const res = await fetch(`/api/admin/customers/${customer.id}/invite`, {
      method: 'POST',
    })
    if (res.ok) {
      const data = await res.json()
      inviteResult.email = data.email
      inviteResult.supplier_name = data.customer_name || data.company_name || customer.company_name
      inviteResult.invite_url = data.invite_url
      inviteResult.email_sent = data.email_sent
      inviteResult.smtp_configured = data.smtp_configured
      inviteResult.message = data.message

      showInviteModal.value = true
      await fetchCustomers()
    } else {
      const err = await res.json().catch(() => ({}))
      notify('Davetiye gönderilemedi: ' + (err.detail || 'Bilinmeyen hata.'))
    }
  } catch (err) {
    console.error('Error sending customer invite:', err)
    notify('Sunucuya bağlanılamadı.')
  }
}

const deleteCustomer = async (customer) => {
  if (
    !(await confirmAction(
      `'${customer.company_name}' adlı müşteriyi silmek istediğinizden emin misiniz?`,
    ))
  )
    return
  try {
    const res = await fetch(`/api/admin/customers/${customer.id}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      await fetchCustomers()
      if (showCustomerDetailsModal.value && selectedCustomerDetails.value?.id === customer.id) {
        showCustomerDetailsModal.value = false
      }
      notify(`'${customer.company_name}' müşterisi başarıyla silindi.`)
    } else {
      const err = await res.json().catch(() => ({}))
      notify('Müşteri silinemedi: ' + (err.detail || 'Bilinmeyen hata.'))
    }
  } catch (err) {
    console.error('Error deleting customer:', err)
    notify('Sunucuya bağlanılamadı.')
  }
}

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
  email: '',
  send_invite: false,
  city: '',
  district: '',
  services: [],
  contract_type: '',
})

function handleServiceTagKeydown(event) {
  if (event.key !== 'Enter' && event.key !== ',') return
  event.preventDefault()
  addService()
}

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
  Object.assign(newSupplierForm, {
    name: '',
    type: '',
    phone: '',
    email: '',
    send_invite: false,
    city: '',
    district: '',
    services: [],
    contract_type: '',
  })
  serviceInput.value = ''
}

// Invite Result Modal State
const showInviteModal = ref(false)
const copied = ref(false)
const inviteResult = reactive({
  supplier_name: '',
  email: '',
  invite_url: '',
  email_sent: false,
  smtp_configured: false,
  message: '',
})

const copyInviteUrl = () => {
  if (!inviteResult.invite_url) return
  navigator.clipboard.writeText(inviteResult.invite_url)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2500)
}

const whatsappShareUrl = computed(() => {
  const text = `Merhaba ${inviteResult.supplier_name},\n\nFleetRent Filo Yönetim Portalı davetiyeniz hazırlandı. Aşağıdaki bağlantıya tıklayarak şifrenizi belirleyebilirsiniz:\n\n${inviteResult.invite_url}`
  return `https://wa.me/?text=${encodeURIComponent(text)}`
})

const submitAddSupplier = async () => {
  // Commit any pending service input
  if (serviceInput.value.trim()) addService()
  const shouldInvite = Boolean(newSupplierForm.send_invite && newSupplierForm.email)
  try {
    const res = await fetch('/api/admin/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSupplierForm),
    })
    if (res.ok) {
      const added = await res.json()
      await fetchSuppliers()
      closeAddSupplierModal()

      if (shouldInvite && added.email) {
        // Trigger explicit invite modal feedback
        await sendSupplierInvite(added)
      } else {
        notify(`✅ ${added.name} başarıyla sisteme kaydedildi.`)
      }
    } else {
      const errData = await res.json().catch(() => ({}))
      notify(errData.detail || 'Tedarikçi eklenirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error adding supplier:', err)
    notify('Bağlantı hatası oluştu.')
  }
}

const sendSupplierInvite = async (supplier) => {
  let targetEmail = supplier.email
  if (!targetEmail) {
    const inputEmail = await askText(
      `"${supplier.name}" için davet gönderilecek e-posta adresini giriniz:`,
      '',
    )
    if (!inputEmail || !inputEmail.trim()) return
    targetEmail = inputEmail.trim()
  }

  try {
    const res = await fetch(`/api/admin/suppliers/${supplier.id}/invite`, {
      method: 'POST',
    })
    const data = await res.json()
    if (res.ok) {
      Object.assign(inviteResult, {
        supplier_name: data.supplier_name || supplier.name,
        email: data.email || targetEmail,
        invite_url: data.invite_url,
        email_sent: data.email_sent,
        smtp_configured: data.smtp_configured,
        message: data.message,
      })
      showInviteModal.value = true
      await fetchSuppliers()
    } else {
      notify(`Hata: ${data.detail || 'Davet gönderilemedi.'}`)
    }
  } catch (err) {
    console.error('Invite error:', err)
    notify('Sunucuya bağlanılamadı.')
  }
}

const deleteSupplier = async (supplier) => {
  if (
    !(await confirmAction(
      `"${supplier.name}" tedarikçisini/servisini silmek istediğinizden emin misiniz?`,
    ))
  )
    return
  try {
    const res = await fetch(`/api/admin/suppliers/${supplier.id}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchSuppliers()
      notify(`✅ ${supplier.name} başarıyla silindi.`)
    } else {
      const errData = await res.json().catch(() => ({}))
      notify(errData.detail || 'Silme işlemi sırasında hata oluştu.')
    }
  } catch (err) {
    console.error('Delete supplier error:', err)
    notify('Sunucuya bağlanılamadı.')
  }
}

// Bids modal state

const showBidsModal = ref(false)
const bidsLoading = ref(false)
const selectedQuoteForBids = ref(null)
const selectedQuoteBids = ref([])

// QUOTES COMPUTED

const totalSupplierBidsCount = computed(() => {
  return quotes.value.reduce((acc, q) => acc + (q.bids ? q.bids.length : 0), 0)
})

const acceptedQuotesCount = computed(() => {
  return quotes.value.filter(
    (q) => q.status === 'Kabul Edildi' || q.status === 'Sözleşme İmzalandı',
  ).length
})

const rejectedQuotesCount = computed(() => {
  return quotes.value.filter((q) => q.status === 'Reddedildi').length
})

const deletedQuotesCount = computed(() => {
  return quotes.value.filter((q) => q.status === 'İstek Silindi' || q.status === 'Silindi').length
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
  return suppliers.value.filter((s) => s.contract_type === 'Yetkili').length
})

// Detail Tab state for customer modal
const detailTab = ref('vehicles')

const contractedSuppliersCount = computed(() => {
  return suppliers.value.filter((s) => s.contract_type === 'Anlaşmalı').length
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
    const response = await fetch('/api/suppliers?include_unverified=true')
    if (response.ok) {
      suppliers.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching suppliers:', error)
  }
}

const fetchVehicles = async () => {
  try {
    const response = await fetch('/api/vehicles')
    if (response.ok) {
      vehicles.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching vehicles:', error)
  }
}

const addQuote = async () => {
  try {
    const res = await fetch('/api/quotes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newQuoteForm),
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
      notify('Teklif eklenirken hata oluştu.')
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(editQuoteForm),
    })
    if (res.ok) {
      await fetchQuotes()
      showEditQuoteModal.value = false
    } else {
      notify('Teklif güncellenirken hata oluştu.')
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(editCustomerForm),
    })
    if (res.ok) {
      await fetchCustomers()
      showEditCustomerModal.value = false
    } else {
      notify('Müşteri bilgileri güncellenirken hata oluştu.')
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
  openTab('customers')
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
    const quote = quotes.value.find((q) => q.id === quoteId)
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: 'Kabul Edildi' }),
    })
    if (res.ok) {
      await openQuoteBidsModal(selectedQuoteForBids.value)
      await fetchQuotes()
    } else {
      notify('Teklif kabul edilirken hata oluştu.')
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
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status: 'Reddedildi' }),
    })
    if (res.ok) {
      await openQuoteBidsModal(selectedQuoteForBids.value)
    } else {
      notify('Teklif reddedilirken hata oluştu.')
    }
  } catch (err) {
    console.error('Error rejecting bid:', err)
  }
}

const getBidBadgeClass = (status) => {
  return {
    'badge-active': status === 'Kabul Edildi',
    'badge-roadside': status === 'Beklemede',
    'badge-old-reason': status === 'Reddedildi',
  }
}

const updateStatus = async (quoteId, newStatus, contractAmount) => {
  try {
    const response = await fetch(`/api/quotes/${quoteId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status: newStatus,
        contract_amount: contractAmount,
      }),
    })

    if (response.ok) {
      console.log(`Quote #${quoteId} status set to ${newStatus}`)
      await fetchQuotes()
      await fetchCustomers()
    } else {
      notify('Durum güncellenirken hata oluştu.')
    }
  } catch (error) {
    console.error('Error updating status:', error)
  }
}

const getStatusClass = (status) => {
  return {
    'status-pending': status === 'Teklif Bekleniyor',
    'status-given': status === 'Teklif Verildi',
    'status-reviewing': status === 'Değerlendirmede',
    'status-accepted': status === 'Kabul Edildi',
    'status-signed': status === 'Sözleşme İmzalandı',
    'status-rejected': status === 'Reddedildi',
    'status-deleted': status === 'İstek Silindi' || status === 'Silindi',
  }
}

const getCategoryBadgeClass = (type) => {
  return {
    'badge-active': type === 'servis',
    'badge-service': type === 'lastik',
    'badge-roadside': type === 'yol_yardim',
    'badge-replacement': type === 'ikame_arac',
  }
}

const getTypeName = (type) => {
  const map = {
    servis: 'Yetkili Servis',
    lastik: 'Lastik Bayi',
    yol_yardim: 'Yol Yardım',
    ikame_arac: 'İkame Araç',
  }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('tr-TR')
  } catch {
    return dateStr
  }
}

const showVehicleDetailsModal = ref(false)
const selectedVehicleDetails = ref(null)
const vehicleServices = ref([])

const openVehicleDetails = async (vehicle) => {
  selectedVehicleDetails.value = vehicle
  vehicleServices.value = []
  showVehicleDetailsModal.value = true
  await fetchVehicleServices(vehicle.id)
}

const closeVehicleDetails = () => {
  showVehicleDetailsModal.value = false
  selectedVehicleDetails.value = null
  vehicleServices.value = []
}

const fetchVehicleServices = async (vehicleId) => {
  try {
    const res = await fetch(`/api/admin/vehicles/${vehicleId}/services`)
    if (res.ok) {
      vehicleServices.value = await res.json()
    }
  } catch (error) {
    console.error('Error fetching vehicle services:', error)
  }
}

const logout = async () => {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('fleetcar_admin_token') || ''}` },
    })
  } catch {
    // Logout still clears local credentials when the server is unavailable.
  }
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
  await Promise.all([fetchQuotes(), fetchCustomers(), fetchSuppliers(), fetchVehicles()])
  loading.value = false
})
</script>

<style scoped>
.status-pending {
  background: #faf5ff;
  color: #7e22ce;
  border-color: #e9d5ff;
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

.status-accepted {
  background: #f0fdf4;
  color: #15803d;
  border-color: #bbf7d0;
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

.status-deleted {
  background: #f8fafc;
  color: #64748b;
  border-color: #cbd5e1;
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
@keyframes fadeSlide {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Supplier tag input */
.supplier-tag-input-wrap {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--glass-bg, rgba(255, 255, 255, 0.04));
  padding: 8px 10px;
  transition: border-color 0.2s;
}
.supplier-tag-input-wrap:focus-within {
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
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
  background: rgba(124, 58, 237, 0.15);
  color: #9333ea;
  border: 1px solid rgba(124, 58, 237, 0.25);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 0.8rem;
  font-weight: 500;
}
.chip-remove {
  background: transparent;
  border: none;
  color: #9333ea;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
  opacity: 0.7;
  transition: opacity 0.15s;
}
.chip-remove:hover {
  opacity: 1;
}
.tag-bare-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.88rem;
  min-width: 180px;
  flex: 1;
}
.tag-bare-input::placeholder {
  color: var(--text-muted);
}
.admin-support-error {
  color: #b91c1c;
  margin: 0 0 12px;
}
</style>

<!-- Admin portal on the shared design tokens (design-tokens.css), same look as the other portals. -->
<style scoped>
.adm {
  background: var(--fr-bg);
  color: var(--fr-text);
}
.adm-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--fr-space-3);
  margin-bottom: var(--fr-space-4);
}
.adm-panel {
  margin-bottom: var(--fr-space-4);
  padding: var(--fr-space-4);
  background: var(--fr-surface);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius-lg);
  box-shadow: var(--fr-shadow-sm);
}
.adm-panel-title {
  margin: 0 0 var(--fr-space-3);
  font-size: var(--fr-text-md);
  font-weight: 700;
  color: var(--fr-ink);
}
.adm-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--fr-space-4);
}
.adm-two .adm-panel {
  margin-bottom: var(--fr-space-4);
}
.adm-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--fr-space-3) var(--fr-space-4);
  padding-bottom: var(--fr-space-4);
  margin-bottom: var(--fr-space-2);
  border-bottom: 1px solid var(--fr-border);
}
.adm-search {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 240px;
  max-width: 340px;
  min-height: 38px;
  padding: 0 12px;
  border: 1px solid var(--fr-border-strong);
  border-radius: var(--fr-radius);
  background: var(--fr-surface);
  color: var(--fr-muted);
}
.adm-search:focus-within {
  border-color: var(--fr-primary);
  box-shadow: 0 0 0 3px var(--fr-primary-soft);
}
.adm-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fr-ink);
  font: inherit;
  font-size: var(--fr-text-md);
}
.adm-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.adm-chips-label {
  margin-right: 2px;
  font-size: var(--fr-text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--fr-muted);
}
.adm-chip {
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid var(--fr-border-strong);
  border-radius: 999px;
  background: var(--fr-surface);
  color: var(--fr-text);
  font: inherit;
  font-size: var(--fr-text-sm);
  cursor: pointer;
}
.adm-chip:hover {
  border-color: var(--fr-primary);
  color: var(--fr-primary);
}
.adm-chip[aria-pressed='true'] {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
  font-weight: 600;
}
.adm-count {
  margin-left: auto;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
  white-space: nowrap;
}
.adm-loading,
.adm-muted {
  margin: 0;
  padding: var(--fr-space-4) 0;
  color: var(--fr-muted);
}
.adm-loading {
  text-align: center;
}
.adm-table-wrap {
  overflow-x: auto;
}
.adm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fr-text-md);
}
.adm-table th {
  padding: 10px 12px;
  border-bottom: 1px solid var(--fr-border);
  background: transparent;
  font-size: var(--fr-text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: left;
  text-transform: uppercase;
  color: var(--fr-muted);
  white-space: nowrap;
}
.adm-table td {
  padding: 12px;
  border-bottom: 1px solid var(--fr-border);
  vertical-align: middle;
  color: var(--fr-text);
}
.adm-table tbody tr:last-child td {
  border-bottom: 0;
}
.adm-table tbody tr:hover td {
  background: #f7faff;
}
.adm-table tr.is-clickable {
  cursor: pointer;
}
.adm-table tr.is-muted td {
  opacity: 0.6;
}
.adm-actions-col {
  text-align: right;
  width: 1%;
  white-space: nowrap;
}
.adm-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}
.adm-cell-title {
  font-weight: 600;
  color: var(--fr-ink);
}
.adm-cell-sub {
  display: block;
  margin-top: 2px;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.adm-money {
  font-weight: 700;
  color: var(--fr-ink);
  font-variant-numeric: tabular-nums;
}
.adm-wrap {
  max-width: 280px;
  white-space: normal;
  line-height: 1.45;
}
.adm-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.92em;
}
.adm-entity {
  display: flex;
  align-items: center;
  gap: 10px;
}
.adm-avatar {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: none;
  border-radius: 50%;
  background: var(--fr-primary-soft);
  color: #0052d4;
  font-weight: 700;
}
.adm-link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--fr-ink);
  font: inherit;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}
.adm-link:hover {
  color: var(--fr-primary);
  text-decoration: underline;
}
/* Badges and status: one colour vocabulary (tone-*) for the whole page. */
.adm-badge {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: var(--fr-text-xs);
  font-weight: 600;
  white-space: nowrap;
}
.tone-blue {
  background: var(--fr-info-soft);
  color: var(--fr-info);
}
.tone-green {
  background: var(--fr-success-soft);
  color: var(--fr-success);
}
.tone-amber {
  background: var(--fr-warning-soft);
  color: var(--fr-warning);
}
.tone-red {
  background: var(--fr-danger-soft);
  color: var(--fr-danger);
}
.tone-violet {
  background: var(--fr-violet-soft);
  color: var(--fr-violet);
}
.tone-teal {
  background: var(--fr-teal-soft);
  color: var(--fr-teal);
}
.tone-gray {
  background: #eef2f7;
  color: var(--fr-muted);
}
.adm-status {
  min-width: 178px;
  min-height: 34px;
  padding: 0 30px 0 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  font: inherit;
  font-size: var(--fr-text-sm);
  font-weight: 600;
  cursor: pointer;
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, currentColor 50%),
    linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position:
    calc(100% - 15px) 50%,
    calc(100% - 10px) 50%;
  background-size: 5px 5px;
  background-repeat: no-repeat;
}
.adm-status.tone-blue {
  background-color: var(--fr-info-soft);
}
.adm-status.tone-green {
  background-color: var(--fr-success-soft);
}
.adm-status.tone-amber {
  background-color: var(--fr-warning-soft);
}
.adm-status.tone-red {
  background-color: var(--fr-danger-soft);
}
.adm-status.tone-violet {
  background-color: var(--fr-violet-soft);
}
.adm-status.tone-gray {
  background-color: #eef2f7;
}
.adm-status:focus-visible {
  outline: 2px solid var(--fr-focus);
  outline-offset: 2px;
}
.adm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 240px;
}
.adm-tag {
  padding: 2px 8px;
  border: 1px solid var(--fr-border);
  border-radius: 6px;
  font-size: var(--fr-text-xs);
  color: var(--fr-text);
}
/* Buttons */
.adm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--fr-border-strong);
  border-radius: var(--fr-radius);
  background: var(--fr-surface);
  color: var(--fr-ink);
  font: inherit;
  font-size: var(--fr-text-md);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}
.adm-btn:hover {
  border-color: var(--fr-primary);
  color: var(--fr-primary);
}
.adm-btn.primary {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
}
.adm-btn.primary:hover {
  background: #0052d4;
  color: #fff;
}
.adm-btn.teal {
  border-color: var(--fr-teal);
  background: var(--fr-teal);
  color: #fff;
}
.adm-btn.teal:hover {
  filter: brightness(0.92);
  color: #fff;
}
.adm-btn.ghost {
  background: transparent;
}
.adm-btn.danger {
  color: var(--fr-danger);
}
.adm-btn.danger:hover {
  border-color: var(--fr-danger);
  background: var(--fr-danger-soft);
  color: var(--fr-danger);
}
.adm-btn.sm {
  min-height: 32px;
  padding: 0 10px;
  font-size: var(--fr-text-sm);
}
.adm-btn.icon {
  width: 32px;
  padding: 0;
}
.adm-btn:disabled {
  opacity: 0.55;
  cursor: default;
}
/* Detail views */
.adm-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: var(--fr-space-3);
  padding: 4px 0;
  border: 0;
  background: none;
  color: var(--fr-primary);
  font: inherit;
  font-size: var(--fr-text-sm);
  font-weight: 600;
  cursor: pointer;
}
.adm-contact {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  margin: calc(-1 * var(--fr-space-3)) 0 var(--fr-space-4);
  padding: 0;
  list-style: none;
  font-size: var(--fr-text-sm);
  color: var(--fr-text);
}
.adm-contact li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.adm-contact :deep(svg) {
  color: var(--fr-muted);
}
.adm-tabs {
  display: flex;
  gap: 4px;
  margin: calc(-1 * var(--fr-space-2)) 0 var(--fr-space-4);
  border-bottom: 1px solid var(--fr-border);
}
.adm-tab {
  padding: 10px 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--fr-muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.adm-tab span {
  margin-left: 4px;
  padding: 1px 7px;
  border-radius: 999px;
  background: #eef2f7;
  font-size: var(--fr-text-xs);
}
.adm-tab[aria-selected='true'] {
  border-bottom-color: var(--fr-primary);
  color: var(--fr-primary);
}
.adm-vehicle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--fr-space-3);
}
.adm-vehicle {
  padding: var(--fr-space-4);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius);
}
.adm-vehicle header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.adm-vehicle h3 {
  margin: 10px 0 8px;
  font-size: var(--fr-text-md);
  color: var(--fr-ink);
}
.adm-vehicle h3 small {
  font-weight: 400;
  color: var(--fr-muted);
}
.adm-vehicle dl,
.adm-dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 12px;
  margin: 0;
  font-size: var(--fr-text-sm);
}
.adm-vehicle dt,
.adm-dl dt {
  color: var(--fr-muted);
}
.adm-vehicle dd,
.adm-dl dd {
  margin: 0;
  text-align: right;
  color: var(--fr-ink);
  font-weight: 500;
  overflow-wrap: anywhere;
}
.adm-plate {
  display: inline-block;
  padding: 3px 9px;
  border: 1.5px solid var(--fr-ink);
  border-radius: 5px;
  background: #fff;
  color: var(--fr-ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--fr-text-sm);
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.adm-plate.lg {
  padding: 6px 12px;
  font-size: var(--fr-text-lg);
}
.adm-plate-btn {
  cursor: pointer;
}
.adm-plate-btn:hover {
  border-color: var(--fr-primary);
  color: var(--fr-primary);
}
.adm-vehicle-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--fr-space-3) var(--fr-space-4);
  margin-bottom: var(--fr-space-5);
}
.adm-vehicle-head h1 {
  margin: 0;
  font-size: var(--fr-text-2xl);
  color: var(--fr-ink);
}
.adm-vehicle-head p {
  margin: 2px 0 0;
  color: var(--fr-muted);
}
@media (max-width: 900px) {
  .adm-two {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .adm-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .adm-panel {
    padding: var(--fr-space-3);
  }
  .adm-search {
    max-width: none;
    flex-basis: 100%;
  }
  .adm-chips {
    flex-wrap: nowrap;
    overflow-x: auto;
    max-width: 100%;
    padding-bottom: 2px;
  }
  .adm-count {
    margin-left: 0;
  }
  .adm-actions-col {
    width: auto;
    white-space: normal;
    text-align: left;
  }
  .adm-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .adm-actions .adm-btn:not(.icon) {
    flex: 1 1 auto;
  }
  .adm-status {
    width: 100%;
  }
}
</style>

<style scoped>
/* Admin modals: the same surface as the rest of the product, no glass or gradients. */
.adm-modal {
  background: var(--fr-surface) !important;
  border: 1px solid var(--fr-border) !important;
  border-radius: var(--fr-radius-lg) !important;
  box-shadow: var(--fr-shadow) !important;
  color: var(--fr-text);
  backdrop-filter: none !important;
}
.adm-modal-title {
  margin: 0 0 var(--fr-space-4);
  font-size: var(--fr-text-xl);
  font-weight: 700;
  color: var(--fr-ink);
}
.adm-modal :deep(.btn-primary) {
  background: var(--fr-primary);
  border-color: var(--fr-primary);
  color: #fff;
}
</style>
