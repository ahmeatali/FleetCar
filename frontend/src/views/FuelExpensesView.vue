<template>
  <div class="portal-layout">
    <Sidebar />
    <main class="portal-main fuel-page" :aria-busy="loading">
      <header class="fuel-topbar">
        <UiField class="fuel-search"
          ><span aria-hidden="true">⌕</span
          ><input
            v-model="search"
            type="search"
            aria-label="Yakıt kayıtlarında ara"
            placeholder="Araç, plaka, marka, model, yakıt fişi, istasyon, tarih…"
        /></UiField>
        <div class="fuel-account">
          <NotificationBell /><span class="avatar">{{ initials }}</span>
          <div>
            <strong>{{ customerName }}</strong
            ><small>Filo Yöneticisi</small>
          </div>
        </div>
      </header>
      <section class="fuel-heading">
        <div class="heading-title">
          <span class="heading-icon" aria-hidden="true"><FuelIcon kind="amount" /></span>
          <div>
            <h1>Yakıt Giderleri</h1>
            <p>
              Araçlarınızın yakıt tüketimi, maliyetleri ve istasyon bilgilerini detaylı olarak takip
              edin.
            </p>
          </div>
        </div>
        <div class="heading-actions">
          <UiButton class="outline" @click="openCreate">＋ Yakıt Kaydı</UiButton
          ><UiButton class="primary" :disabled="!data || loading || !!error" @click="printReport"
            >⇩ Rapor Oluştur</UiButton
          >
        </div>
      </section>
      <form class="fuel-filters card" @submit.prevent="loadOverview">
        <UiField
          >Başlangıç Tarihi<input
            v-model="filters.start_date"
            aria-label="Başlangıç Tarihi"
            type="date"
            required /></UiField
        ><UiField
          >Bitiş Tarihi<input
            v-model="filters.end_date"
            aria-label="Bitiş Tarihi"
            type="date"
            required
        /></UiField>
        <UiField
          >Araç Grubu<select v-model="filters.vehicle_group" aria-label="Araç Grubu">
            <option value="">Tümü</option>
            <option v-for="group in options.groups" :key="group">{{ group }}</option>
          </select></UiField
        >
        <UiField
          >Araç<select v-model="filters.vehicle_id" aria-label="Araç">
            <option value="">Tümü</option>
            <option v-for="v in options.vehicles" :key="v.id" :value="v.id">
              {{ v.plate }} · {{ v.brand }} {{ v.model }}
            </option>
          </select></UiField
        >
        <UiField
          >Yakıt Türü<select v-model="filters.fuel_type" aria-label="Yakıt Türü">
            <option value="">Tümü</option>
            <option v-for="fuel in options.fuel_types" :key="fuel">{{ fuel }}</option>
          </select></UiField
        >
        <UiField
          >İstasyon<select v-model="filters.station" aria-label="İstasyon">
            <option value="">Tümü</option>
            <option v-for="station in options.stations" :key="station">{{ station }}</option>
          </select></UiField
        >
        <UiButton class="primary" :disabled="loading">{{
          loading ? 'Yükleniyor…' : '⌕ Filtrele'
        }}</UiButton>
      </form>
      <UiAlert v-if="loading" class="notice" as="p" tone="info"
        >Yakıt bilgileri yükleniyor…</UiAlert
      >
      <UiAlert v-if="error" class="error" as="div" tone="error"
        >{{ error }} <UiButton class="outline" @click="loadOverview">Tekrar Dene</UiButton></UiAlert
      >
      <template v-if="data && !error">
        <p class="period">
          {{ dateOnly(data.period.start) }} – {{ dateOnly(data.period.end) }}
          <span
            >Karşılaştırma: {{ dateOnly(data.period.previous_start) }} –
            {{ dateOnly(data.period.previous_end) }}</span
          >
        </p>
        <section class="fuel-stats" aria-label="Yakıt özeti">
          <article v-for="metric in metrics" :key="metric.key" class="card stat">
            <span class="stat-icon" aria-hidden="true"><FuelIcon :kind="metric.key" /></span>
            <div>
              <small>{{ metric.label }}</small
              ><strong>{{ metric.value }}</strong
              ><span class="comparison" :class="changeClass(metric.key)">{{
                changeText(metric.key)
              }}</span>
            </div>
          </article>
        </section>
        <p v-if="data.summary.missing_liters" class="data-note">
          {{ data.summary.missing_liters }} kayıtta litre bilgisi yok. Litre ve birim fiyat
          hesaplarına yalnızca litre bilgisi olan kayıtlar dahil edilir.
        </p>
        <section class="fuel-charts">
          <article class="card spending-chart">
            <h2>Yakıt Giderleri ve Alım Miktarı</h2>
            <div class="chart-legend">
              <span><i class="blue-dot"></i>Yakıt gideri (₺)</span
              ><span><i class="green-dot"></i>Yakıt alımı (L)</span>
            </div>
            <svg
              v-if="data.records.length"
              viewBox="0 0 540 220"
              role="img"
              aria-label="Seçili dönemdeki yakıt gideri ve litre grafiği"
            >
              <g v-for="tick in [0, 1, 2, 3, 4]" :key="tick">
                <line
                  x1="60"
                  x2="482"
                  :y1="174 - tick * 36"
                  :y2="174 - tick * 36"
                  stroke="#e7eef7"
                />
                <text x="54" :y="178 - tick * 36" text-anchor="end">
                  {{ compact((amountMax * tick) / 4) }}
                </text>
                <text x="490" :y="178 - tick * 36">{{ compact((litersMax * tick) / 4) }}</text>
              </g>
              <g v-for="bucket in data.chart" :key="bucket.start">
                <rect
                  :x="chartX(i) - barWidth / 2"
                  :y="174 - (bucket.amount / amountMax) * 144"
                  :width="barWidth"
                  :height="(bucket.amount / amountMax) * 144"
                  rx="3"
                  fill="#328af7"
                >
                  <title>
                    {{ dateOnly(bucket.start) }} – {{ dateOnly(bucket.end) }}:
                    {{ money(bucket.amount) }}
                  </title>
                </rect>
                <text :x="chartX(i)" y="202" text-anchor="middle">
                  {{ shortDate(bucket.start) }}
                </text>
              </g>
              <polyline
                v-if="data.summary.liters !== null"
                :points="litersPoints"
                fill="none"
                stroke="#17a999"
                stroke-width="2.5"
              />
              <circle
                v-for="bucket in data.chart.filter((b) => b.liters !== null)"
                :key="bucket.start"
                :cx="chartX(data.chart.indexOf(bucket))"
                :cy="174 - (bucket.liters / litersMax) * 144"
                r="4"
                fill="#17a999"
              >
                <title>{{ dateOnly(bucket.start) }}: {{ number(bucket.liters) }} L</title>
              </circle>
            </svg>
            <div v-else class="empty">Seçili dönemde yakıt alımı bulunmuyor.</div>
          </article>
          <article class="card distribution">
            <h2>Yakıt Türlerine Göre Dağılım</h2>
            <div class="distribution-content">
              <div class="donut" :style="{ background: donutBackground }">
                <div>
                  <small>Toplam</small
                  ><strong
                    >{{ number(data.summary.liters)
                    }}<span v-if="data.summary.liters !== null"> L</span></strong
                  >
                </div>
              </div>
              <ul>
                <li v-for="(item, i) in data.breakdown" :key="item.fuel_type">
                  <i :style="{ background: colors[i % colors.length] }"></i
                  ><span>{{ item.fuel_type }}</span
                  ><b>{{
                    item.liters === null || !data.summary.liters
                      ? '—'
                      : number((item.liters / data.summary.liters) * 100, 0) + '%'
                  }}</b
                  ><small
                    >{{ number(item.liters)
                    }}<template v-if="item.liters !== null"> L</template></small
                  >
                </li>
              </ul>
            </div>
            <p v-if="!data.breakdown.length" class="data-note">
              Yakıt türü dağılımı için kayıt bulunmuyor.
            </p>
          </article>
          <article class="card map-card">
            <div class="panel-title">
              <h2>Yakıt Tüketim Haritası</h2>
              <select v-model="mapPeriod" aria-label="Harita dönemi">
                <option value="30">Son 30 Gün</option>
                <option value="all">Seçili Dönem</option>
              </select>
            </div>
            <template v-if="activeMarker"
              ><iframe
                :src="mapUrl"
                title="Seçili yakıt dolumunun konumu"
                loading="lazy"
                referrerpolicy="no-referrer"
              ></iframe>
              <div class="map-locations">
                <UiButton
                  v-for="marker in mapMarkers"
                  :key="marker.id"
                  :class="{ active: activeMarker.id === marker.id }"
                  @click="markerId = marker.id"
                  ><i :class="markerTone(marker)"></i>{{ marker.station }} ·
                  {{ marker.plate }}</UiButton
                >
              </div>
              <p class="data-note">
                {{ dateOnly(activeMarker.date) }} ·
                {{
                  activeMarker.consumption === null
                    ? 'Tüketim hesaplanamadı'
                    : number(activeMarker.consumption, 1) + ' L/100 km'
                }}
              </p></template
            >
            <div v-else class="empty">Bu dönemde konumu kayıtlı yakıt alımı yok.</div>
            <div class="map-legend">
              <span><i class="green-dot"></i>Düşük</span><span><i class="amber-dot"></i>Normal</span
              ><span><i class="red-dot"></i>Yüksek</span
              ><span><i class="gray-dot"></i>Veri yok</span>
            </div>
            <small class="data-note"
              >Tüketim sınıfları filo ortalamasına göre ±%10 aralığıyla hesaplanır.</small
            >
          </article>
        </section>
        <section class="fuel-record-grid">
          <article class="card purchases">
            <div class="panel-title">
              <h2>Yakıt Alım Kayıtları</h2>
              <UiButton class="outline" :disabled="!data.records.length" @click="exportCsv"
                >⇩ Dışa Aktar{{ selectedIds.length ? ` (${selectedIds.length})` : '' }}</UiButton
              >
            </div>
            <UiTable class="table-scroll"
              ><table>
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        aria-label="Bu sayfadaki kayıtları seç"
                        :checked="allSelected"
                        @change="toggleSelection"
                      />
                    </th>
                    <th>Tarih / Saat</th>
                    <th>Araç / Plaka</th>
                    <th>Yakıt Türü</th>
                    <th>Alınan Yakıt (L)</th>
                    <th>Birim Fiyat (₺/L)</th>
                    <th>Toplam Tutar (₺)</th>
                    <th>İstasyon</th>
                    <th>Kilometre</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!pageRecords.length">
                    <td colspan="10" class="empty">Filtrelere uygun yakıt kaydı bulunamadı.</td>
                  </tr>
                  <tr v-for="r in pageRecords" :key="r.id">
                    <td>
                      <input
                        v-model="selectedIds"
                        type="checkbox"
                        :value="r.id"
                        :aria-label="`${r.plate} ${dateOnly(r.date)} kaydını seç`"
                      />
                    </td>
                    <td>{{ dateTime(r.date) }}</td>
                    <td>
                      <router-link :to="`/dashboard/vehicles/${encodeURIComponent(r.vehicle_id)}`"
                        >{{ r.brand }} {{ r.model }}<small>{{ r.plate }}</small></router-link
                      >
                    </td>
                    <td>{{ r.fuel_type }}</td>
                    <td>{{ number(r.liters) }}</td>
                    <td>{{ money(r.unit_price) }}</td>
                    <td>
                      <b>{{ money(r.amount) }}</b>
                    </td>
                    <td>{{ r.station }}</td>
                    <td>{{ number(r.mileage, 0) }}</td>
                    <td><UiButton class="detail-button" @click="openDetail(r)">Detay</UiButton></td>
                  </tr>
                </tbody>
              </table></UiTable
            >
            <footer class="table-footer">
              <span
                >{{ data.records.length }} kayıt · {{ pageStart }}–{{ pageEnd }} gösteriliyor.</span
              >
              <div class="pagination">
                <UiButton :disabled="page === 1" aria-label="Önceki sayfa" @click="page--"
                  >‹</UiButton
                ><UiButton
                  v-for="p in visiblePages"
                  :key="p"
                  :class="{ active: page === p }"
                  @click="page = p"
                  >{{ p }}</UiButton
                ><UiButton
                  :disabled="page === totalPages"
                  aria-label="Sonraki sayfa"
                  @click="page++"
                  >›</UiButton
                >
              </div>
            </footer>
          </article>
          <article class="card ranking">
            <div class="panel-title">
              <h2>En Çok Yakıt Tüketen Araçlar</h2>
              <select v-model="rankingGroup" aria-label="Tüketim sıralaması araç grubu">
                <option value="">Tümü</option>
                <option v-for="group in options.groups" :key="group">{{ group }}</option>
              </select>
            </div>
            <ol>
              <li v-for="(v, i) in rankedVehicles" :key="v.vehicle_id">
                <span class="rank-number">{{ i + 1 }}</span
                ><img v-if="v.vehicle_photo" :src="v.vehicle_photo" alt="" /><span
                  v-else
                  class="vehicle-symbol"
                  aria-hidden="true"
                  >▱</span
                >
                <div>
                  <router-link :to="`/dashboard/vehicles/${encodeURIComponent(v.vehicle_id)}`"
                    >{{ v.brand }} {{ v.model }}</router-link
                  ><small>{{ v.plate }}</small>
                  <div class="rank-track">
                    <i
                      :style="{
                        width:
                          (v.consumption === null ? 0 : (v.consumption / rankingMax) * 100) + '%',
                        background: colors[i % colors.length],
                      }"
                    ></i>
                  </div>
                </div>
                <span class="rank-value"
                  ><b>{{
                    v.consumption === null ? 'Veri yok' : number(v.consumption, 1) + ' L/100 km'
                  }}</b
                  ><small>{{ money(v.amount) }}</small></span
                >
              </li>
            </ol>
            <p v-if="!rankedVehicles.length" class="empty">Araç kaydı bulunmuyor.</p>
            <p class="data-note">
              Tüketim için en az iki tam depo dolumu ve artan kilometre gerekir. Eksik tüketim
              verisi olan araçlar listenin sonunda gösterilir.
            </p>
          </article>
        </section>
        <section class="card fuel-insights">
          <article>
            <span class="stat-icon"><FuelIcon kind="amount" /></span>
            <div>
              <small>En Çok Yakıt Alınan İstasyon</small
              ><strong>{{ data.insights.top_station?.station || 'Veri yok' }}</strong
              ><small v-if="data.insights.top_station"
                >{{ data.insights.top_station.count }} alım ·
                {{ number(data.insights.top_station.liters) }} L</small
              >
            </div>
          </article>
          <article>
            <span class="stat-icon"><FuelIcon kind="liters" /></span>
            <div>
              <small>Ortalama Dolum Miktarı</small
              ><strong
                >{{ number(data.summary.average_fill, 1)
                }}<template v-if="data.summary.average_fill !== null"> L</template></strong
              ><small>{{ changeText('average_fill') }}</small>
            </div>
          </article>
          <article>
            <span class="stat-icon"><FuelIcon kind="unit_price" /></span>
            <div>
              <small>En Ekonomik İstasyon</small
              ><strong>{{ data.insights.cheapest_station?.station || 'Veri yok' }}</strong
              ><small v-if="data.insights.cheapest_station"
                >{{ money(data.insights.cheapest_station.unit_price) }} / L · ağırlıklı
                ortalama</small
              >
            </div>
          </article>
        </section>
      </template>
    </main>
  </div>
  <UiModal v-if="showCreate" class="fuel-overlay" @close="closeCreate" @keydown.esc="closeCreate"
    ><section
      ref="createDialog"
      class="fuel-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="fuel-create-title"
      tabindex="-1"
      @keydown="trapFocus"
    >
      <header>
        <h2 id="fuel-create-title">Yakıt Alımı Ekle</h2>
        <UiButton aria-label="Kapat" @click="closeCreate">×</UiButton>
      </header>
      <form @submit.prevent="saveRecord">
        <div class="form-grid">
          <UiField
            >Araç<select
              v-model="form.vehicle_id"
              aria-label="Araç"
              required
              @change="
                form.fuel_type = options.vehicles.find((v) => v.id === form.vehicle_id)?.fuel || ''
              "
            >
              <option value="" disabled>Araç seçin</option>
              <option
                v-for="v in options.vehicles.filter((v) => v.is_active)"
                :key="v.id"
                :value="v.id"
              >
                {{ v.plate }} · {{ v.brand }} {{ v.model }}
              </option>
            </select></UiField
          ><UiField
            >Tarih / Saat<input
              v-model="form.date"
              aria-label="Tarih / Saat"
              type="datetime-local"
              required /></UiField
          ><UiField
            >Yakıt Türü<input
              v-model.trim="form.fuel_type"
              aria-label="Yakıt Türü"
              list="fuel-types"
              required /><datalist id="fuel-types">
              <option
                v-for="fuel in [
                  ...new Set(['Dizel', 'Benzin', 'LPG', 'Hibrit', ...options.fuel_types]),
                ]"
                :key="fuel"
                :value="fuel"
              /></datalist></UiField
          ><UiField
            >İstasyon<input
              v-model.trim="form.station"
              aria-label="İstasyon"
              list="fuel-stations"
              required /><datalist id="fuel-stations">
              <option
                v-for="station in options.stations"
                :key="station"
                :value="station"
              /></datalist></UiField
          ><UiField
            >Alınan Yakıt (L)<input
              v-model.number="form.liters"
              aria-label="Alınan Yakıt (L)"
              type="number"
              min="0.01"
              step="0.01"
              required /></UiField
          ><UiField
            >Toplam Tutar (₺)<input
              v-model.number="form.amount"
              aria-label="Toplam Tutar (₺)"
              type="number"
              min="0.01"
              step="0.01"
              required /></UiField
          ><UiField
            >Kilometre<input
              v-model.number="form.mileage"
              aria-label="Kilometre"
              type="number"
              min="0"
              step="1"
              required /></UiField
          ><UiField
            >Fiş Numarası<input v-model.trim="form.receipt_no" aria-label="Fiş Numarası" /></UiField
          ><UiField
            >Dolum Enlemi (isteğe bağlı)<input
              v-model="form.latitude"
              aria-label="Dolum Enlemi (isteğe bağlı)"
              type="number"
              min="-90"
              max="90"
              step="any" /></UiField
          ><UiField
            >Dolum Boylamı (isteğe bağlı)<input
              v-model="form.longitude"
              aria-label="Dolum Boylamı (isteğe bağlı)"
              type="number"
              min="-180"
              max="180"
              step="any"
          /></UiField>
        </div>
        <UiField class="full-tank"
          ><input v-model="form.full_tank" type="checkbox" /> Bu dolumda depo tamamen
          dolduruldu.</UiField
        ><UiField
          >Not<textarea v-model.trim="form.note" aria-label="Not" rows="2"></textarea></UiField
        ><UiAlert v-if="saveError" class="error" as="p" tone="error">{{ saveError }}</UiAlert>
        <footer>
          <UiButton type="button" class="outline" :disabled="saving" @click="closeCreate"
            >Vazgeç</UiButton
          ><UiButton class="primary" :disabled="saving">{{
            saving ? 'Kaydediliyor…' : 'Kaydet'
          }}</UiButton>
        </footer>
      </form>
    </section></UiModal
  >
  <UiModal v-if="detailOpen" class="fuel-overlay" @close="closeDetail" @keydown.esc="closeDetail"
    ><section
      ref="detailDialog"
      class="fuel-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="fuel-detail-title"
      tabindex="-1"
      @keydown="trapFocus"
    >
      <header>
        <h2 id="fuel-detail-title">Yakıt Kaydı Detayı</h2>
        <UiButton aria-label="Kapat" @click="closeDetail">×</UiButton>
      </header>
      <UiAlert v-if="detailLoading" as="p" tone="info">Kayıt yükleniyor…</UiAlert
      ><UiAlert v-if="detailError" class="error" as="p" tone="error">{{ detailError }}</UiAlert>
      <dl v-if="detail">
        <template v-for="item in detailItems" :key="item.label"
          ><dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd></template
        >
      </dl>
      <footer><UiButton class="outline" @click="closeDetail">Kapat</UiButton></footer>
    </section></UiModal
  >
</template>

<script setup>
import { downloadCsv } from '../utils/downloads.js'

import { UiAlert, UiButton, UiField, UiModal, UiTable } from '../components/ui/index.js'

import { computed, h, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import NotificationBell from '../components/NotificationBell.vue'
const FuelIcon = (props) => {
  const paths = {
    amount: [
      'M4 21V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v17M3 21h12M6 6h6v5H6z',
      'M14 12h2a2 2 0 0 1 2 2v4a2 2 0 0 0 4 0V9l-4-4M19 6v4h3',
    ],
    liters: ['M12 3C9 7 5 11 5 15a7 7 0 0 0 14 0c0-4-4-8-7-12Z', 'M8 15a4 4 0 0 0 4 4'],
    consumption: [
      'M4 21V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v17M3 21h12M6 6h6v5H6z',
      'M14 12h2a2 2 0 0 1 2 2v4a2 2 0 0 0 4 0V9l-4-4',
    ],
    unit_price: [
      'M14 6c0 1.7-2.7 3-6 3S2 7.7 2 6s2.7-3 6-3 6 1.3 6 3ZM2 6v5c0 1.7 2.7 3 6 3',
      'M2 11v5c0 1.7 2.7 3 6 3M10 13c0 1.7 2.7 3 6 3s6-1.3 6-3-2.7-3-6-3-6 1.3-6 3ZM10 13v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5',
    ],
  }
  return h(
    'svg',
    {
      viewBox: '0 0 24 24',
      width: 26,
      height: 26,
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 1.8,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'aria-hidden': 'true',
    },
    (paths[props.kind] || paths.amount).map((d) => h('path', { d })),
  )
}
FuelIcon.props = ['kind']
const customerId =
  localStorage.getItem('fleetcar_customer_id') || localStorage.getItem('customer_id')
const customerName = localStorage.getItem('fleetcar_customer_name') || 'Filo Yöneticisi'
const initials = customerName
  .split(/\s+/)
  .map((s) => s[0])
  .slice(0, 2)
  .join('')
  .toLocaleUpperCase('tr-TR')
const localDay = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(
  new Date(),
)
const filters = reactive({
  start_date: localDay.slice(0, 7) + '-01',
  end_date: localDay,
  vehicle_group: '',
  vehicle_id: '',
  fuel_type: '',
  station: '',
})
const search = ref(''),
  data = ref(null),
  loading = ref(false),
  error = ref('')
const options = computed(
  () => data.value?.options || { vehicles: [], groups: [], fuel_types: [], stations: [] },
)
const number = (n, digits = 2) =>
  n == null ? 'Veri yok' : Number(n).toLocaleString('tr-TR', { maximumFractionDigits: digits })
const money = (n) =>
  n == null ? 'Veri yok' : Number(n).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })
const dateOnly = (value) =>
  value
    ? new Date(value.slice(0, 10) + 'T12:00:00').toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : '—'
const dateTime = (value) =>
  value?.length > 10
    ? new Date(value).toLocaleString('tr-TR', {
        timeZone: 'Europe/Istanbul',
        dateStyle: 'short',
        timeStyle: 'short',
      })
    : dateOnly(value)
const shortDate = (value) => dateOnly(value).slice(0, 5)
const compact = (n) =>
  Number(n).toLocaleString('tr-TR', { notation: 'compact', maximumFractionDigits: 1 })
const metrics = computed(() => [
  { key: 'amount', label: 'Toplam Yakıt Gideri', value: money(data.value?.summary.amount) },
  {
    key: 'liters',
    label: 'Toplam Yakıt Alımı',
    value: number(data.value?.summary.liters) + (data.value?.summary.liters == null ? '' : ' L'),
  },
  {
    key: 'consumption',
    label: 'Ortalama Tüketim',
    value:
      number(data.value?.summary.consumption, 1) +
      (data.value?.summary.consumption == null ? '' : ' L/100 km'),
  },
  {
    key: 'unit_price',
    label: 'Ortalama Yakıt Fiyatı',
    value:
      money(data.value?.summary.unit_price) +
      (data.value?.summary.unit_price == null ? '' : ' / L'),
  },
])
const changeText = (key) =>
  data.value?.changes[key] == null
    ? 'Önceki dönemle karşılaştırma yok'
    : `${data.value.changes[key] > 0 ? '↑' : data.value.changes[key] < 0 ? '↓' : '↔'} %${number(Math.abs(data.value.changes[key]), 1)} · önceki döneme göre`
const changeClass = (key) =>
  data.value?.changes[key] == null
    ? ''
    : key === 'liters'
      ? 'neutral'
      : data.value.changes[key] > 0
        ? 'increase'
        : 'decrease'
let requestSequence = 0,
  searchTimer,
  previousFocus
async function loadOverview() {
  const sequence = ++requestSequence
  error.value = ''
  loading.value = true
  try {
    if (!customerId)
      throw new Error('Yakıt bilgilerini görmek için müşteri hesabınızla giriş yapın.')
    if (filters.start_date > filters.end_date)
      throw new Error('Başlangıç tarihi bitiş tarihinden sonra olamaz.')
    const query = new URLSearchParams({
      customer_id: customerId,
      ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
      ...(search.value.trim() ? { search: search.value.trim() } : {}),
    })
    const res = await fetch('/api/fuel-overview?' + query)
    if (!res.ok) throw new Error(await responseError(res, 'Yakıt bilgileri yüklenemedi.'))
    const result = await res.json()
    if (sequence !== requestSequence) return
    data.value = result
    page.value = 1
    selectedIds.value = []
    markerId.value = null
  } catch (e) {
    if (sequence === requestSequence) error.value = e.message
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}
async function responseError(res, fallback) {
  try {
    const body = await res.json()
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadOverview, 300)
})
onMounted(loadOverview)
onUnmounted(() => {
  clearTimeout(searchTimer)
  requestSequence++
  document.body.style.overflow = previousOverflow
})
const colors = ['#0064ff', '#ffad32', '#a64bdd', '#19b393', '#e9556a']
const amountMax = computed(() => Math.max(1, ...(data.value?.chart.map((b) => b.amount) || [])))
const litersMax = computed(() =>
  Math.max(1, ...(data.value?.chart.map((b) => b.liters || 0) || [])),
)
const chartX = (i) => 60 + ((i + 0.5) * 422) / (data.value?.chart.length || 1)
const barWidth = computed(() => Math.min(48, 280 / (data.value?.chart.length || 1)))
const litersPoints = computed(() =>
  (data.value?.chart || [])
    .filter((b) => b.liters !== null)
    .map(
      (b) => `${chartX(data.value.chart.indexOf(b))},${174 - (b.liters / litersMax.value) * 144}`,
    )
    .join(' '),
)
const donutBackground = computed(() => {
  if (!data.value?.summary.liters) return '#e7eff8'
  let offset = 0
  return (
    'conic-gradient(' +
    data.value.breakdown
      .filter((b) => b.liters != null)
      .map((b) => {
        const i = data.value.breakdown.indexOf(b)
        const start = offset
        offset += (b.liters / data.value.summary.liters) * 100
        return `${colors[i % colors.length]} ${start}% ${offset}%`
      })
      .join(', ') +
    ')'
  )
})
const mapPeriod = ref('30'),
  markerId = ref(null)
const mapMarkers = computed(() => {
  if (!data.value) return []
  const end = new Date(data.value.period.end + 'T12:00:00')
  end.setDate(end.getDate() - 29)
  return data.value.map_markers.filter(
    (m) => mapPeriod.value === 'all' || new Date(m.date.slice(0, 10) + 'T12:00:00') >= end,
  )
})
const activeMarker = computed(
  () => mapMarkers.value.find((m) => m.id === markerId.value) || mapMarkers.value[0],
)
const mapUrl = computed(() => {
  const m = activeMarker.value
  if (!m) return ''
  const lat = Math.max(-84.9, Math.min(84.9, m.latitude)),
    lng = m.longitude
  const query = new URLSearchParams({
    bbox: `${Math.max(-180, lng - 0.08)},${Math.max(-85, lat - 0.04)},${Math.min(180, lng + 0.08)},${Math.min(85, lat + 0.04)}`,
    layer: 'mapnik',
    marker: `${lat},${lng}`,
  })
  return 'https://www.openstreetmap.org/export/embed.html?' + query
})
const markerTone = (m) =>
  m.consumption == null || !data.value?.summary.consumption
    ? 'gray-dot'
    : m.consumption < data.value.summary.consumption * 0.9
      ? 'green-dot'
      : m.consumption > data.value.summary.consumption * 1.1
        ? 'red-dot'
        : 'amber-dot'
const rankingGroup = ref('')
const rankedVehicles = computed(() =>
  (data.value?.ranking || [])
    .filter((v) => !rankingGroup.value || v.vehicle_group === rankingGroup.value)
    .slice(0, 5),
)
const rankingMax = computed(() =>
  Math.max(1, ...rankedVehicles.value.map((v) => v.consumption || 0)),
)
const page = ref(1),
  pageSize = 7,
  selectedIds = ref([]),
  printing = ref(false)
const totalPages = computed(() =>
  Math.max(1, Math.ceil((data.value?.records.length || 0) / pageSize)),
)
const pageRecords = computed(() =>
  printing.value
    ? data.value?.records || []
    : (data.value?.records || []).slice((page.value - 1) * pageSize, page.value * pageSize),
)
const pageStart = computed(() => (data.value?.records.length ? (page.value - 1) * pageSize + 1 : 0))
const pageEnd = computed(() => Math.min(page.value * pageSize, data.value?.records.length || 0))
const visiblePages = computed(() =>
  Array.from(
    { length: Math.min(5, totalPages.value) },
    (_, i) => Math.max(1, Math.min(page.value - 2, totalPages.value - 4)) + i,
  ),
)
const allSelected = computed(
  () =>
    pageRecords.value.length > 0 &&
    pageRecords.value.every((r) => selectedIds.value.includes(r.id)),
)
const toggleSelection = (event) => {
  const ids = pageRecords.value.map((r) => r.id)
  selectedIds.value = event.target.checked
    ? [...new Set([...selectedIds.value, ...ids])]
    : selectedIds.value.filter((id) => !ids.includes(id))
}
function exportCsv() {
  const rows = data.value.records.filter(
    (r) => !selectedIds.value.length || selectedIds.value.includes(r.id),
  )
  const headers = [
    'Tarih / Saat',
    'Araç',
    'Plaka',
    'Yakıt Türü',
    'Alınan Yakıt (L)',
    'Birim Fiyat (TL/L)',
    'Toplam Tutar (TL)',
    'İstasyon',
    'Kilometre',
    'Fiş No',
    'Tam Depo',
    'Enlem',
    'Boylam',
    'Not',
  ]
  const values = rows.map((r) => [
    r.date,
    `${r.brand || ''} ${r.model || ''}`,
    r.plate,
    r.fuel_type,
    r.liters,
    r.unit_price,
    r.amount,
    r.station,
    r.mileage,
    r.receipt_no,
    r.full_tank ? 'Evet' : 'Hayır',
    r.latitude,
    r.longitude,
    r.note,
  ])
  downloadCsv(
    [headers, ...values],
    `FleetRent_Yakit_${data.value.period.start}_${data.value.period.end}.csv`,
  )
}
const beforePrint = () => {
  printing.value = true
}
const afterPrint = () => {
  printing.value = false
}
onMounted(() => {
  window.addEventListener('beforeprint', beforePrint)
  window.addEventListener('afterprint', afterPrint)
})
onUnmounted(() => {
  window.removeEventListener('beforeprint', beforePrint)
  window.removeEventListener('afterprint', afterPrint)
})
const printReport = async () => {
  printing.value = true
  await nextTick()
  window.print()
  printing.value = false
}
const showCreate = ref(false),
  saving = ref(false),
  saveError = ref(''),
  createDialog = ref(null)
const form = reactive({
  vehicle_id: '',
  date: '',
  fuel_type: '',
  station: '',
  liters: '',
  amount: '',
  mileage: '',
  receipt_no: '',
  latitude: '',
  longitude: '',
  full_tank: false,
  note: '',
})
const detailOpen = ref(false),
  detail = ref(null),
  detailLoading = ref(false),
  detailError = ref(''),
  detailDialog = ref(null)
let previousOverflow = document.body.style.overflow,
  detailSequence = 0
function trapFocus(event) {
  if (event.key !== 'Tab') return
  const nodes = [
    ...event.currentTarget.querySelectorAll('button,input,select,textarea,a[href]'),
  ].filter((el) => !el.disabled)
  const first = nodes[0],
    last = nodes.at(-1)
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}
async function openCreate() {
  previousFocus = document.activeElement
  Object.assign(form, {
    vehicle_id: '',
    date: new Intl.DateTimeFormat('sv-SE', {
      timeZone: 'Europe/Istanbul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
      .format(new Date())
      .replace(' ', 'T'),
    fuel_type: '',
    station: '',
    liters: '',
    amount: '',
    mileage: '',
    receipt_no: '',
    latitude: '',
    longitude: '',
    full_tank: false,
    note: '',
  })
  saveError.value = ''
  showCreate.value = true
  await nextTick()
  createDialog.value?.focus()
}
function closeCreate() {
  if (saving.value) return
  showCreate.value = false
  previousFocus?.focus()
}
function closeDetail() {
  detailSequence++
  detailOpen.value = false
  previousFocus?.focus()
}
watch(
  () => showCreate.value || detailOpen.value,
  (open) => {
    if (open) {
      previousOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
    } else document.body.style.overflow = previousOverflow
  },
)
async function saveRecord() {
  saving.value = true
  saveError.value = ''
  try {
    if (!customerId) throw new Error('Müşteri hesabınızla giriş yapın.')
    if ((form.latitude === '') !== (form.longitude === ''))
      throw new Error('Enlem ve boylam birlikte girilmelidir.')
    const body = {
      ...form,
      kind: 'Yakıt',
      date: form.date + ':00+03:00',
      latitude: form.latitude === '' ? null : Number(form.latitude),
      longitude: form.longitude === '' ? null : Number(form.longitude),
    }
    const res = await fetch('/api/vehicle-expenses?customer_id=' + encodeURIComponent(customerId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok)
      throw new Error(await responseError(res, 'Yakıt kaydı kaydedilemedi. Alanları kontrol edin.'))
    // Include the saved record in the refreshed view even when its date was outside the old filter.
    const day = form.date.slice(0, 10)
    if (day < filters.start_date) filters.start_date = day
    if (day > filters.end_date) filters.end_date = day
    filters.vehicle_id = ''
    filters.vehicle_group = ''
    filters.station = ''
    filters.fuel_type = ''
    search.value = ''
    clearTimeout(searchTimer)
    showCreate.value = false
    previousFocus?.focus()
    await loadOverview()
  } catch (e) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}
async function openDetail(row) {
  const sequence = ++detailSequence
  previousFocus = document.activeElement
  detail.value = null
  detailError.value = ''
  detailOpen.value = true
  detailLoading.value = true
  await nextTick()
  detailDialog.value?.focus()
  try {
    const res = await fetch(
      `/api/vehicle-expenses/${row.id}?customer_id=${encodeURIComponent(customerId)}`,
    )
    if (!res.ok) throw new Error(await responseError(res, 'Kayıt yüklenemedi.'))
    const record = await res.json()
    if (sequence === detailSequence)
      detail.value = {
        ...row,
        ...record,
        fuel_type: record.fuel_type || row.fuel_type,
        station: record.station || row.station,
      }
  } catch (e) {
    if (sequence === detailSequence) detailError.value = e.message
  } finally {
    if (sequence === detailSequence) detailLoading.value = false
  }
}
const detailItems = computed(() => {
  const r = detail.value
  if (!r) return []
  return [
    { label: 'Araç / Plaka', value: `${r.brand || ''} ${r.model || ''} · ${r.plate}` },
    { label: 'Tarih / Saat', value: dateTime(r.date) },
    { label: 'Yakıt Türü', value: r.fuel_type || 'Belirtilmedi' },
    { label: 'Alınan Yakıt', value: number(r.liters) + (r.liters == null ? '' : ' L') },
    { label: 'Birim Fiyat', value: money(r.liters ? r.amount / r.liters : null) },
    { label: 'Toplam Tutar', value: money(r.amount) },
    { label: 'İstasyon', value: r.station || 'Belirtilmedi' },
    { label: 'Kilometre', value: number(r.mileage, 0) },
    { label: 'Fiş Numarası', value: r.receipt_no || 'Belirtilmedi' },
    { label: 'Tam Depo', value: r.full_tank ? 'Evet' : 'Hayır' },
    {
      label: 'Dolum Konumu',
      value: r.latitude == null ? 'Belirtilmedi' : `${r.latitude}, ${r.longitude}`,
    },
    { label: 'Not', value: r.note || '—' },
  ]
})
</script>

<style scoped>
.fuel-page {
  --ink: #10295a;
  --muted: #6d83a8;
  background: #eff7ff;
  color: var(--ink);
  padding: 0 20px 24px;
  font-size: 12px;
  min-width: 0;
}
.fuel-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 0;
  border-bottom: 1px solid #dceafa;
}
.fuel-search {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #e5f2ff;
  border: 1px solid #d8e9fa;
  border-radius: 22px;
  width: min(600px, 60%);
}
.fuel-search span {
  font-size: 22px;
  color: #0064ff;
}
.fuel-search input {
  border: 0;
  background: transparent;
  outline: 0;
  width: 100%;
  font: inherit;
  color: var(--ink);
}
.fuel-account {
  display: flex;
  align-items: center;
  gap: 10px;
}
.fuel-account strong,
.fuel-account small {
  display: block;
}
.fuel-account small {
  margin-top: 4px;
  color: var(--muted);
}
.avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  background: #0064ff;
  color: #fff;
  border-radius: 50%;
}
.fuel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  margin: 22px 0 18px;
}
.heading-title {
  display: flex;
  align-items: center;
  gap: 14px;
}
.heading-icon {
  display: flex;
  color: #0045be;
}
.heading-icon svg {
  width: 34px;
  height: 34px;
}
h1 {
  font-size: 24px;
  line-height: 1.2;
  margin: 0 0 6px;
}
p {
  margin: 0;
}
.heading-title p {
  font-size: 12px;
  color: var(--muted);
}
.heading-actions {
  display: flex;
  gap: 10px;
}
.card {
  background: #fff;
  border: 1px solid #e4edf7;
  border-radius: 9px;
  min-width: 0;
}
button,
input,
select,
textarea {
  font: inherit;
}
button {
  cursor: pointer;
}
button:disabled {
  opacity: 0.55;
  cursor: default;
}
.primary,
.outline {
  border: 1px solid #d6e6f7;
  border-radius: 6px;
  padding: 10px 14px;
  min-height: 38px;
  white-space: nowrap;
}
.primary {
  background: #0064ff;
  color: #fff;
  border-color: #0064ff;
}
.outline {
  background: #fff;
  color: #276fbe;
}
label {
  display: grid;
  gap: 6px;
  color: var(--muted);
}
input,
select,
textarea {
  min-width: 0;
  box-sizing: border-box;
  border: 1px solid #dfeaf6;
  border-radius: 5px;
  padding: 9px;
  background: #fff;
  color: var(--ink);
  width: 100%;
  min-height: 38px;
}
input[type='checkbox'] {
  width: 14px;
  min-height: 14px;
  accent-color: #0064ff;
}
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
button:focus-visible,
a:focus-visible {
  outline: 2px solid #0064ff;
  outline-offset: 2px;
}
.fuel-filters {
  display: grid;
  grid-template-columns: repeat(2, minmax(140px, 1.1fr)) repeat(4, minmax(100px, 1fr)) auto;
  gap: 12px;
  align-items: end;
  padding: 14px;
  margin-bottom: 12px;
}
.period {
  font-size: 11px;
  color: var(--muted);
  margin: 0 0 10px;
}
.period span {
  margin-left: 15px;
}
.fuel-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.stat {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 18px 14px;
}
.stat-icon {
  display: grid;
  place-items: center;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  background: #e6f4ff;
  color: #003fb9;
  font-size: 24px;
}
.stat small {
  display: block;
  color: var(--muted);
  font-size: 11px;
}
.stat strong {
  display: block;
  font-size: 21px;
  margin: 7px 0;
  white-space: nowrap;
}
.comparison {
  font-size: 10px;
  color: var(--muted);
}
.increase {
  color: #e45464;
}
.decrease {
  color: #14a874;
}
.neutral {
  color: #437ca8;
}
.fuel-charts {
  display: grid;
  grid-template-columns: 1.5fr 1.15fr 1.05fr;
  gap: 12px;
  margin-bottom: 12px;
}
.fuel-charts > .card {
  padding: 15px;
}
h2 {
  font-size: 13px;
  margin: 0 0 14px;
  color: var(--ink);
}
.chart-legend,
.map-legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 10px;
}
.chart-legend span,
.map-legend span {
  display: flex;
  align-items: center;
  gap: 5px;
}
.chart-legend {
  margin-bottom: 8px;
}
i.blue-dot,
i.green-dot,
i.amber-dot,
i.red-dot,
i.gray-dot,
.distribution li > i {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.blue-dot {
  background: #0064ff;
}
.green-dot {
  background: #17b48a;
}
.amber-dot {
  background: #ffb330;
}
.red-dot {
  background: #ef5267;
}
.gray-dot {
  background: #a0adc0;
}
.spending-chart svg {
  display: block;
  width: 100%;
  min-height: 180px;
}
.spending-chart svg text {
  font-size: 10px;
  fill: #6983a6;
}
.distribution-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  min-height: 180px;
}
.donut {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  padding: 22px;
  box-sizing: border-box;
  flex-shrink: 0;
}
.donut > div {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  border-radius: 50%;
  background: #fff;
}
.donut small {
  color: var(--muted);
}
.donut strong {
  margin-top: 7px;
  font-size: 14px;
}
.distribution ul {
  list-style: none;
  margin: 0;
  padding: 0;
  min-width: 0;
  flex: 1;
}
.distribution li {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 16px 0;
  font-size: 10px;
}
.distribution li span {
  flex: 1;
}
.distribution li small {
  color: var(--muted);
}
.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}
.panel-title h2 {
  margin: 0;
}
.panel-title select {
  max-width: 105px;
  font-size: 10px;
  padding: 5px;
  min-height: 28px;
}
.map-card iframe {
  width: 100%;
  height: 160px;
  border: 0;
  border-radius: 6px;
}
.map-locations {
  display: flex;
  gap: 5px;
  overflow: auto;
  max-height: 64px;
  margin: 7px 0;
}
.map-locations button {
  border: 1px solid #dce8f5;
  border-radius: 4px;
  padding: 5px;
  background: #fff;
  white-space: nowrap;
  font-size: 10px;
  color: #3b638e;
}
.map-locations button.active {
  border-color: #0064ff;
  background: #eff6ff;
}
.map-locations i {
  margin-right: 4px;
}
.map-legend {
  gap: 10px;
  margin-top: 10px;
}
.data-note {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.5;
  margin: 8px 0;
}
.fuel-record-grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(275px, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.purchases > .panel-title {
  padding: 12px 14px 0;
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  white-space: nowrap;
  font-size: 10px;
}
th,
td {
  text-align: left;
  padding: 12px 8px;
  border-bottom: 1px solid #edf3fa;
}
th {
  background: #f4f9ff;
  color: #617da3;
  font-size: 9px;
  font-weight: 600;
}
td {
  color: #335582;
}
td small {
  display: block;
  margin-top: 5px;
  color: #5484bd;
  font-size: 9px;
}
a {
  color: inherit;
  text-decoration: none;
}
.detail-button {
  border: 1px solid #dce8f5;
  color: #267ce0;
  background: #f8fcff;
  border-radius: 4px;
  font-size: 10px;
  padding: 4px 8px;
}
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  gap: 10px;
  color: var(--muted);
  font-size: 10px;
}
.pagination {
  display: flex;
  gap: 4px;
}
.pagination button {
  border: 1px solid #e2ecf8;
  border-radius: 5px;
  background: #fff;
  color: #367bcc;
  min-width: 27px;
  min-height: 28px;
}
.pagination .active {
  background: #0064ff;
  color: #fff;
}
.ranking {
  padding: 14px;
}
.ranking ol {
  padding: 0;
  margin: 0;
  list-style: none;
}
.ranking li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  border-bottom: 1px solid #e9f0f8;
}
.rank-number {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  color: #fff;
  background: #3285e8;
  font-size: 10px;
}
.ranking li:first-child .rank-number {
  background: #ee5770;
}
.ranking li:nth-child(2) .rank-number {
  background: #eeb13f;
}
.ranking li:nth-child(3) .rank-number {
  background: #17ae91;
}
.ranking img,
.vehicle-symbol {
  width: 38px;
  height: 28px;
  object-fit: contain;
  flex-shrink: 0;
}
.vehicle-symbol {
  display: grid;
  place-items: center;
  background: #edf5ff;
  color: #488bd8;
  border-radius: 5px;
  font-size: 24px;
}
.ranking li > div {
  flex: 1;
  min-width: 0;
  font-size: 10px;
}
.ranking small {
  display: block;
  font-size: 9px;
  color: var(--muted);
  margin-top: 4px;
}
.rank-value {
  text-align: right;
  font-size: 9px;
  white-space: nowrap;
}
.rank-track {
  height: 4px;
  border-radius: 4px;
  background: #e7f0f9;
  margin-top: 9px;
}
.rank-track i {
  display: block;
  height: 4px;
  border-radius: 4px;
}
.fuel-insights {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 15px;
  gap: 18px;
}
.fuel-insights article {
  display: flex;
  gap: 12px;
  align-items: center;
}
.fuel-insights article + article {
  border-left: 1px solid #e4edf7;
  padding-left: 18px;
}
.fuel-insights small,
.fuel-insights strong {
  display: block;
}
.fuel-insights small {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.6;
}
.fuel-insights strong {
  font-size: 12px;
  margin: 5px 0;
}
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 160px;
  color: var(--muted);
  text-align: center;
  padding: 12px;
  white-space: normal;
}
td.empty {
  display: table-cell;
}
.error {
  background: #fff1f2;
  color: #b42340;
  padding: 12px;
  border-radius: 6px;
  margin: 12px 0;
}
.notice {
  color: #276fbe;
  margin-bottom: 12px;
}
.fuel-overlay {
  position: fixed;
  inset: 0;
  background: #03182699;
  display: grid;
  place-items: center;
  z-index: 1000;
  padding: 20px;
}
.fuel-dialog {
  box-sizing: border-box;
  width: min(650px, 100%);
  max-height: 90dvh;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  color: #10295a;
  font-size: 13px;
}
.fuel-dialog header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.fuel-dialog h2 {
  margin: 0;
  font-size: 20px;
}
.fuel-dialog header button {
  border: 0;
  background: transparent;
  font-size: 26px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.fuel-dialog label {
  margin-bottom: 12px;
}
.full-tank {
  display: flex;
  align-items: center;
  margin-top: 10px;
}
.fuel-dialog footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
.fuel-dialog dl {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 12px;
}
.fuel-dialog dt {
  color: #6d83a8;
}
.fuel-dialog dd {
  margin: 0;
  overflow-wrap: anywhere;
}
@media (max-width: 1400px) {
  .fuel-filters {
    grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
  }
  .fuel-stats .stat strong {
    font-size: 18px;
  }
  .fuel-charts {
    grid-template-columns: 1.2fr 1fr;
  }
  .map-card {
    grid-column: 1/-1;
  }
  .map-card iframe {
    height: 220px;
  }
  .distribution-content {
    gap: 10px;
  }
  .fuel-record-grid {
    grid-template-columns: minmax(0, 2.5fr) minmax(260px, 1fr);
  }
}
@media (max-width: 1000px) {
  .fuel-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .fuel-record-grid {
    grid-template-columns: 1fr;
  }
  .ranking ol {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 20px;
  }
  .fuel-insights {
    grid-template-columns: 1fr;
  }
  .fuel-insights article + article {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid #e4edf7;
    padding-top: 12px;
  }
}
@media (max-width: 700px) {
  .fuel-page {
    padding: 0 12px 20px;
  }
  .fuel-topbar {
    gap: 10px;
    flex-wrap: wrap;
  }
  .fuel-search {
    width: 100%;
    box-sizing: border-box;
    order: 2;
  }
  .fuel-account {
    margin-left: auto;
  }
  .fuel-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .heading-actions {
    width: 100%;
  }
  .heading-actions button {
    flex: 1;
  }
  .heading-icon {
    display: none;
  }
  .fuel-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .fuel-filters button {
    grid-column: 1/-1;
  }
  .fuel-charts {
    grid-template-columns: 1fr;
  }
  .map-card {
    grid-column: auto;
  }
  .stat {
    padding: 12px 8px;
    gap: 8px;
  }
  .stat-icon {
    width: 32px;
    height: 32px;
    font-size: 20px;
  }
  .fuel-stats .stat strong {
    font-size: 15px;
    white-space: normal;
  }
  .period span {
    display: block;
    margin: 5px 0 0;
  }
  .ranking ol {
    display: block;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
  .fuel-dialog {
    padding: 18px;
  }
  .fuel-dialog input,
  .fuel-dialog select,
  .fuel-dialog textarea,
  .fuel-filters input,
  .fuel-filters select {
    font-size: 16px;
  }
  .fuel-dialog dl {
    grid-template-columns: 110px 1fr;
  }
  .table-footer {
    flex-wrap: wrap;
  }
  .fuel-dialog button {
    min-height: 44px;
  }
}
@media print {
  :global(.customer-navigation),
  :global(.mobile-navigation-bar),
  .fuel-topbar,
  .fuel-filters,
  .heading-actions,
  .panel-title button,
  .table-footer,
  .map-card {
    display: none !important;
  }
  :global(.portal-layout) {
    display: block !important;
  }
  :global(.portal-layout > .fuel-page) {
    margin: 0 !important;
    width: 100% !important;
    max-width: none !important;
    padding: 0;
    background: #fff;
    font-size: 10px;
  }
  .fuel-charts {
    grid-template-columns: 1fr 1fr;
  }
  .fuel-record-grid {
    display: block;
  }
  .ranking {
    margin-top: 16px;
  }
  .card {
    break-inside: avoid;
  }
  .purchases {
    break-inside: auto;
  }
  tr {
    break-inside: avoid;
  }
  thead {
    display: table-header-group;
  }
  .table-scroll {
    overflow: visible;
  }
  table {
    white-space: normal;
    font-size: 9px;
  }
  .fuel-insights {
    margin-top: 14px;
  }
  .fuel-overlay {
    display: none;
  }
  .purchases th:first-child,
  .purchases td:first-child,
  .purchases th:last-child,
  .purchases td:last-child {
    display: none;
  }
}
</style>
