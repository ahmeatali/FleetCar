<template>
  <form class="vf" novalidate @submit.prevent="submit">
    <header class="vf-head">
      <div>
        <h2 class="vf-title">Yeni Araç Ekle</h2>
        <p class="vf-sub">
          Yıldızlı alanlar zorunlu. Diğerlerini şimdi ya da daha sonra araç kartından
          doldurabilirsiniz.
        </p>
        <p v-if="note" class="vf-sub vf-info">{{ note }}</p>
      </div>
      <nav class="vf-steps" aria-label="Form bölümleri">
        <a
          v-for="s in visibleSections"
          :key="s.id"
          :href="`#vf-${s.id}`"
          :class="[
            'vf-step',
            { done: sectionDone(s.id), missing: showErrors && sectionMissing(s.id) },
          ]"
          @click.prevent="jump(s.id)"
          >{{ s.title }}</a
        >
      </nav>
    </header>

    <div ref="body" class="vf-body">
      <!-- 1. Temel bilgiler -->
      <section id="vf-basic" class="vf-section">
        <h3>Araç Bilgileri</h3>
        <div class="vf-grid">
          <UiField label="Plaka" required :error="err('plate')" :hint="plateHint" v-slot="{ id }">
            <input
              :id="id"
              v-model="form.plate"
              class="vf-input vf-plate"
              autocomplete="off"
              placeholder="34 ABC 123"
              maxlength="15"
              @blur="form.plate = formatPlate(form.plate)"
            />
          </UiField>
          <UiField v-if="isSupplier" label="Lokasyon" :hint="branchHint" v-slot="{ id }">
            <select :id="id" v-model="branchId" class="vf-input" :disabled="!branches.length">
              <option value="">
                {{ branches.length ? 'Lokasyon seçin' : 'Şube tanımlı değil' }}
              </option>
              <option v-for="b in branches" :key="b.id" :value="String(b.id)">
                {{ b.name }}{{ b.city ? ` · ${b.city}` : '' }}
              </option>
            </select>
          </UiField>
          <UiField label="Durum" hint="Kiralama açılınca Kirada, servise girince Serviste olur.">
            <span class="vf-static"
              ><span class="vf-dot" aria-hidden="true"></span>Havuz (müsait)</span
            >
          </UiField>
          <UiField label="Segment" required v-slot="{ id }">
            <select :id="id" v-model="form.vehicle_segment" class="vf-input">
              <option v-for="s in SEGMENTS" :key="s" :value="s">{{ s }} Segmenti</option>
            </select>
          </UiField>
          <UiField label="Model Yılı" required :error="err('year')" v-slot="{ id }">
            <select :id="id" v-model.number="form.year" class="vf-input">
              <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
            </select>
          </UiField>
          <UiField label="Marka" required :error="err('brand')" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.brand"
              class="vf-input"
              list="vf-brands"
              placeholder="Örn. Audi"
              autocomplete="off"
            />
            <datalist id="vf-brands">
              <option v-for="b in BRANDS" :key="b" :value="b" />
            </datalist>
          </UiField>
          <UiField label="Tip (Model)" required :error="err('model')" v-slot="{ id }">
            <input :id="id" v-model.trim="form.model" class="vf-input" placeholder="Örn. A6" />
          </UiField>
          <UiField label="Alt Tip (Versiyon)" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.version"
              class="vf-input"
              placeholder="Örn. 2.0 TFSI 200kW quattro"
            />
          </UiField>
          <UiField label="İç Tip Kodu" hint="Kendi tip/donanım kodunuz varsa." v-slot="{ id }">
            <input :id="id" v-model.trim="form.trim_code" class="vf-input" />
          </UiField>
        </div>
      </section>

      <!-- 2. Teknik -->
      <section id="vf-tech" class="vf-section">
        <h3>Teknik Özellikler</h3>
        <div class="vf-grid">
          <UiField label="Yakıt" required v-slot="{ id }">
            <select :id="id" v-model="form.fuel" class="vf-input">
              <option v-for="f in FUELS" :key="f">{{ f }}</option>
            </select>
          </UiField>
          <UiField label="Şanzıman" v-slot="{ id }">
            <select :id="id" v-model="form.transmission" class="vf-input">
              <option value="">Seçin</option>
              <option v-for="t in TRANSMISSIONS" :key="t">{{ t }}</option>
            </select>
          </UiField>
          <UiField label="Çekiş" v-slot="{ id }">
            <select :id="id" v-model="form.drive_type" class="vf-input">
              <option value="">Seçin</option>
              <option v-for="d in DRIVES" :key="d">{{ d }}</option>
            </select>
          </UiField>
          <UiField label="Kasa Tipi" required v-slot="{ id }">
            <select :id="id" v-model="form.vehicle_type" class="vf-input">
              <option v-for="b in BODIES" :key="b">{{ b }}</option>
            </select>
          </UiField>
          <UiField label="Renk" v-slot="{ id }">
            <input :id="id" v-model.trim="form.color" class="vf-input" list="vf-colors" />
            <datalist id="vf-colors">
              <option v-for="c in COLORS" :key="c" :value="c" />
            </datalist>
          </UiField>
          <UiField label="Koltuk Sayısı" v-slot="{ id }">
            <input
              :id="id"
              v-model.number="form.seat_count"
              type="number"
              min="1"
              max="60"
              class="vf-input"
            />
          </UiField>
          <UiField
            label="Şase No (VIN)"
            required
            :error="err('chassis_no')"
            :hint="vinHint"
            v-slot="{ id }"
          >
            <input
              :id="id"
              v-model="form.chassis_no"
              class="vf-input vf-mono"
              maxlength="17"
              autocomplete="off"
              @input="form.chassis_no = form.chassis_no.toUpperCase().replace(/\s/g, '')"
            />
          </UiField>
          <UiField label="Motor No" v-slot="{ id }">
            <input :id="id" v-model.trim="form.engine_no" class="vf-input vf-mono" />
          </UiField>
          <UiField label="Motor Hacmi" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.engine_cc"
                type="number"
                min="0"
                class="vf-input"
              /><em>cc</em></span
            >
          </UiField>
          <UiField label="Motor Gücü" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.horsepower"
                type="number"
                min="0"
                class="vf-input"
              /><em>hp</em></span
            >
          </UiField>
          <UiField label="Silindir Sayısı" v-slot="{ id }">
            <input
              :id="id"
              v-model.number="form.cylinder_count"
              type="number"
              min="0"
              max="16"
              class="vf-input"
            />
          </UiField>
          <UiField label="Ağırlık" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.weight_kg"
                type="number"
                min="0"
                class="vf-input"
              /><em>kg</em></span
            >
          </UiField>
        </div>
      </section>

      <!-- 3. Kilometre, yakıt, lastik -->
      <section id="vf-usage" class="vf-section">
        <h3>Kilometre, Yakıt ve Lastik</h3>
        <div class="vf-grid">
          <UiField label="Güncel KM" required :error="err('mileage')" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.mileage"
                type="number"
                min="0"
                class="vf-input"
              /><em>km</em></span
            >
          </UiField>
          <UiField label="Giriş KM" hint="Araç filoya girdiğindeki kilometre." v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.entry_mileage"
                type="number"
                min="0"
                class="vf-input"
              /><em>km</em></span
            >
          </UiField>
          <UiField label="Yakıt Durumu">
            <div class="vf-segmented" role="radiogroup" aria-label="Yakıt durumu">
              <button
                v-for="l in FUEL_LEVELS"
                :key="l"
                type="button"
                role="radio"
                :aria-checked="form.fuel_level === l"
                :class="{ on: form.fuel_level === l }"
                @click="form.fuel_level = form.fuel_level === l ? '' : l"
              >
                {{ l }}
              </button>
            </div>
          </UiField>
          <UiField label="Lastik" v-slot="{ id }">
            <select :id="id" v-model="form.tire_season" class="vf-input">
              <option v-for="t in TIRE_SEASONS" :key="t">{{ t }}</option>
            </select>
          </UiField>
          <UiField label="Lastik Ölçüleri" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.tire_size"
              class="vf-input"
              placeholder="225/55 R17"
            />
          </UiField>
        </div>
      </section>

      <!-- 4. Tescil -->
      <section id="vf-registry" class="vf-section">
        <h3>Tescil ve Muayene</h3>
        <div class="vf-grid">
          <UiField label="Alınma Tarihi" v-slot="{ id }">
            <input :id="id" v-model="form.purchase_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="İlk Tescil Tarihi" v-slot="{ id }">
            <input :id="id" v-model="form.registration_date" type="date" class="vf-input" />
          </UiField>
          <UiField
            label="Tescil (Ruhsat) Seri No"
            required
            :error="err('license_serial_no')"
            v-slot="{ id }"
          >
            <input
              :id="id"
              v-model="form.license_serial_no"
              class="vf-input vf-mono"
              placeholder="GA 123456"
              @blur="form.license_serial_no = form.license_serial_no.toUpperCase().trim()"
            />
          </UiField>
          <UiField
            label="Muayene Bitiş Tarihi"
            required
            :error="err('inspection_date')"
            v-slot="{ id }"
          >
            <input :id="id" v-model="form.inspection_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="Araç Ruhsat Sahibi" class="vf-wide" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.registration_owner"
              class="vf-input"
              placeholder="Ruhsatta yazan unvan"
            />
          </UiField>
        </div>
      </section>

      <!-- 5. Satın alma -->
      <section id="vf-purchase" class="vf-section">
        <h3>Tedarik ve Finans</h3>
        <div class="vf-grid">
          <UiField label="Tedarik Türü" v-slot="{ id }">
            <select :id="id" v-model="form.supply_type" class="vf-input">
              <option value="">Seçin</option>
              <option v-for="s in SUPPLY_TYPES" :key="s">{{ s }}</option>
            </select>
          </UiField>
          <UiField label="Alındığı Yer" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.purchased_from"
              class="vf-input"
              placeholder="Bayi / firma"
            />
          </UiField>
          <UiField label="Aylık Kiralama Tutarı" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.monthly_rent"
                type="number"
                min="0"
                step="0.01"
                class="vf-input"
              /><em>₺</em></span
            >
          </UiField>
          <UiField label="Alış KDV Oranı" v-slot="{ id }">
            <select :id="id" v-model.number="form.purchase_vat_rate" class="vf-input">
              <option v-for="r in VAT_RATES" :key="r" :value="r">%{{ r }} KDV</option>
            </select>
          </UiField>
          <UiField label="Alış Faiz Oranı (Aylık)" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.purchase_interest_rate"
                type="number"
                min="0"
                step="0.01"
                class="vf-input"
              /><em>%</em></span
            >
          </UiField>
        </div>
      </section>

      <!-- 6. Özel bilgiler (tedarikçi) -->
      <section v-if="isSupplier" id="vf-reserved" class="vf-section">
        <h3>Özel Bilgiler</h3>
        <p class="vf-note">
          Müşteri seçilirse araç yalnızca bu müşteriye satılabilir; başka müşteriye satılamaz.
        </p>
        <div class="vf-grid">
          <UiField label="Müşteri Türü">
            <div class="vf-segmented" role="radiogroup" aria-label="Müşteri türü">
              <button
                v-for="t in ['Bireysel', 'Kurumsal']"
                :key="t"
                type="button"
                role="radio"
                :aria-checked="form.reserved_buyer_type === t"
                :class="{ on: form.reserved_buyer_type === t }"
                @click="form.reserved_buyer_type = t"
              >
                {{ t }}
              </button>
            </div>
          </UiField>
          <UiField v-if="form.reserved_buyer_type === 'Kurumsal'" label="Müşteri" v-slot="{ id }">
            <select :id="id" v-model="form.reserved_customer_id" class="vf-input">
              <option :value="null">Müşteri yok</option>
              <option v-for="c in customers" :key="c.id" :value="c.id">
                {{ c.company_name || c.title }}
              </option>
            </select>
          </UiField>
          <UiField v-else label="Müşteri Adı Soyadı" v-slot="{ id }">
            <input
              :id="id"
              v-model.trim="form.reserved_buyer_name"
              class="vf-input"
              placeholder="Boş bırakılabilir"
            />
          </UiField>
          <UiField label="KM" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.reserved_km"
                type="number"
                min="0"
                class="vf-input"
              /><em>km</em></span
            >
          </UiField>
        </div>
      </section>

      <!-- 7. İsteğe bağlı ayrıntılar -->
      <section id="vf-more" class="vf-section">
        <h3>Sözleşme, Bakım ve Takip <small>İsteğe bağlı</small></h3>
        <div class="vf-grid">
          <UiField label="Sözleşme Başlangıcı" v-slot="{ id }">
            <input :id="id" v-model="form.contract_start_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="Sözleşme Bitişi" v-slot="{ id }">
            <input :id="id" v-model="form.contract_end_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="Aylık KM Limiti" v-slot="{ id }">
            <span class="vf-unit"
              ><input
                :id="id"
                v-model.number="form.monthly_km_limit"
                type="number"
                min="0"
                class="vf-input"
              /><em>km</em></span
            >
          </UiField>
          <UiField
            label="Son Servis Tarihi"
            hint="Boşsa alınma tarihi kabul edilir."
            v-slot="{ id }"
          >
            <input :id="id" v-model="form.last_service_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="Son Servis KM" hint="Boşsa giriş KM kabul edilir." v-slot="{ id }">
            <input
              :id="id"
              v-model.number="form.last_service_mileage"
              type="number"
              min="0"
              class="vf-input"
            />
          </UiField>
          <UiField label="Son Lastik Değişimi" v-slot="{ id }">
            <input :id="id" v-model="form.tire_change_date" type="date" class="vf-input" />
          </UiField>
          <UiField label="GPS Cihaz Kodu / IMEI" v-slot="{ id }">
            <input :id="id" v-model.trim="form.gps_device_id" class="vf-input" />
          </UiField>
          <UiField label="UTTS Kodu" v-slot="{ id }">
            <input :id="id" v-model.trim="form.utts_code" class="vf-input" />
          </UiField>
        </div>
        <UiField label="Açıklama" class="vf-block" v-slot="{ id }">
          <textarea
            :id="id"
            v-model.trim="form.notes"
            rows="3"
            class="vf-input"
            placeholder="Araçla ilgili not"
          ></textarea>
        </UiField>
      </section>
    </div>

    <footer class="vf-foot">
      <p class="vf-progress" aria-live="polite">
        <span class="vf-bar"
          ><span :style="{ width: `${(filledRequired / REQUIRED.length) * 100}%` }"></span
        ></span>
        Zorunlu alanlar {{ filledRequired }}/{{ REQUIRED.length }}
      </p>
      <div class="vf-actions">
        <button type="button" class="vf-btn" :disabled="saving" @click="$emit('cancel')">
          Vazgeç
        </button>
        <button type="submit" class="vf-btn primary" :disabled="saving">
          {{ saving ? 'Kaydediliyor…' : 'Aracı Kaydet' }}
        </button>
      </div>
    </footer>
  </form>
</template>

<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import { UiField } from '../ui/index.js'
import { formatPlate, isTurkishPlate } from '../../utils/plate.js'

const props = defineProps({
  isSupplier: Boolean,
  saving: Boolean,
  branches: { type: Array, default: () => [] },
  customers: { type: Array, default: () => [] },
  // Preset values, e.g. segment and body type from a planning link.
  initial: { type: Object, default: () => ({}) },
  note: { type: String, default: '' },
})
const emit = defineEmits(['submit', 'cancel'])

const SEGMENTS = ['A', 'B', 'C', 'D', 'E', 'F']
const FUELS = ['Benzin', 'Dizel', 'Hibrit', 'Elektrik', 'LPG', 'Benzin + LPG']
const TRANSMISSIONS = ['Manuel', 'Otomatik', 'Yarı Otomatik']
const DRIVES = ['Önden Çekiş', 'Arkadan İtiş', 'Dört Çeker (4x4)']
const BODIES = [
  'Sedan',
  'Hatchback',
  'SUV',
  'Station Wagon',
  'Coupe',
  'Cabrio',
  'MPV',
  'Pick-up',
  'Panelvan',
  'Minibüs',
  'Hafif Ticari',
]
const FUEL_LEVELS = ['Boş', '1/4', '1/2', '3/4', 'Dolu']
const TIRE_SEASONS = ['Dört Mevsim', 'Yaz', 'Kış']
const SUPPLY_TYPES = [
  'Satın Alma',
  'Finansal Kiralama (Leasing)',
  'Operasyonel Kiralama',
  'Konsinye',
]
const VAT_RATES = [20, 10, 1, 0]
const BRANDS = [
  'Audi',
  'BMW',
  'BYD',
  'Citroen',
  'Cupra',
  'Dacia',
  'Fiat',
  'Ford',
  'Honda',
  'Hyundai',
  'Kia',
  'Mercedes-Benz',
  'MG',
  'Mini',
  'Nissan',
  'Opel',
  'Peugeot',
  'Renault',
  'Seat',
  'Skoda',
  'Tesla',
  'Togg',
  'Toyota',
  'Volkswagen',
  'Volvo',
]
const COLORS = [
  'Beyaz',
  'Siyah',
  'Gri',
  'Gümüş',
  'Lacivert',
  'Mavi',
  'Kırmızı',
  'Bej',
  'Kahverengi',
  'Yeşil',
]
const REQUIRED = [
  'plate',
  'brand',
  'model',
  'year',
  'mileage',
  'chassis_no',
  'license_serial_no',
  'inspection_date',
]
const SECTIONS = [
  { id: 'basic', title: 'Araç', fields: ['plate', 'brand', 'model', 'year'] },
  { id: 'tech', title: 'Teknik', fields: ['chassis_no'] },
  { id: 'usage', title: 'KM & Lastik', fields: ['mileage'] },
  { id: 'registry', title: 'Tescil', fields: ['license_serial_no', 'inspection_date'] },
  { id: 'purchase', title: 'Tedarik', fields: [] },
  { id: 'reserved', title: 'Özel', fields: [], supplierOnly: true },
  { id: 'more', title: 'Diğer', fields: [] },
]

const today = new Date().toISOString().slice(0, 10)
const thisYear = new Date().getFullYear()
const years = Array.from({ length: thisYear + 2 - 1990 }, (_, i) => thisYear + 1 - i)

const form = reactive({
  plate: '',
  vehicle_segment: 'C',
  year: thisYear,
  brand: '',
  model: '',
  version: '',
  trim_code: '',
  fuel: 'Benzin',
  transmission: '',
  drive_type: '',
  vehicle_type: 'Sedan',
  color: '',
  seat_count: 5,
  chassis_no: '',
  engine_no: '',
  engine_cc: null,
  horsepower: null,
  cylinder_count: null,
  weight_kg: null,
  mileage: null,
  entry_mileage: null,
  fuel_level: '',
  tire_season: 'Dört Mevsim',
  tire_size: '',
  purchase_date: today,
  registration_date: today,
  license_serial_no: '',
  inspection_date: '',
  registration_owner: '',
  supply_type: '',
  purchased_from: '',
  monthly_rent: null,
  purchase_vat_rate: 20,
  purchase_interest_rate: null,
  reserved_buyer_type: 'Bireysel',
  reserved_customer_id: null,
  reserved_buyer_name: '',
  reserved_km: null,
  contract_start_date: '',
  contract_end_date: '',
  monthly_km_limit: null,
  last_service_date: '',
  last_service_mileage: null,
  tire_change_date: '',
  gps_device_id: '',
  utts_code: '',
  notes: '',
})
for (const [key, value] of Object.entries(props.initial)) if (key in form) form[key] = value
const branchId = ref('')
const showErrors = ref(false)
const body = ref(null)

const visibleSections = computed(() => SECTIONS.filter((s) => props.isSupplier || !s.supplierOnly))
const filled = (key) =>
  form[key] !== null && form[key] !== undefined && String(form[key]).trim() !== ''
const filledRequired = computed(() => REQUIRED.filter(filled).length)

const errors = computed(() => {
  const e = {}
  for (const key of REQUIRED) if (!filled(key)) e[key] = 'Bu alan zorunlu.'
  if (filled('mileage') && form.mileage < 0) e.mileage = 'Kilometre negatif olamaz.'
  return e
})
const err = (key) => (showErrors.value ? errors.value[key] || '' : '')
const sectionMissing = (id) => SECTIONS.find((s) => s.id === id).fields.some((f) => errors.value[f])
const sectionDone = (id) => {
  const fields = SECTIONS.find((s) => s.id === id).fields
  return fields.length > 0 && fields.every((f) => !errors.value[f])
}

const plateHint = computed(() => {
  if (!form.plate) return 'Boşluklu yazılır: 34 ABC 123'
  if (!isTurkishPlate(form.plate)) return 'Türk plaka biçimine uymuyor; doğruysa böyle kaydedilir.'
  return `Kaydedilecek: ${formatPlate(form.plate)}`
})
const vinHint = computed(() => {
  const n = form.chassis_no.length
  if (n && n !== 17) return `Şase numaraları genelde 17 karakterdir; şu an ${n}.`
  return `17 karakter · ${n}/17`
})
const branchHint = computed(() =>
  props.branches.length ? 'Aracın bağlı olduğu şube.' : 'Şubeleri Lokasyonlar bölümünden ekleyin.',
)

function jump(id) {
  body.value?.querySelector(`#vf-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function submit() {
  form.plate = formatPlate(form.plate)
  showErrors.value = true
  if (Object.keys(errors.value).length) {
    await nextTick()
    const first = body.value?.querySelector('.ui-field__error')
    first?.closest('label')?.querySelector('input,select,textarea')?.focus()
    first?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }
  // Send only what was entered; the server fills service history from the purchase day.
  const payload = {}
  for (const [key, value] of Object.entries(form)) {
    if (value === '' || value === null || value === undefined) continue
    payload[key] = value
  }
  if (!props.isSupplier) {
    for (const key of [
      'reserved_buyer_type',
      'reserved_customer_id',
      'reserved_buyer_name',
      'reserved_km',
    ])
      delete payload[key]
  } else if (payload.reserved_buyer_type === 'Kurumsal') {
    delete payload.reserved_buyer_name
  } else {
    delete payload.reserved_customer_id
  }
  // Nothing reserved: no buyer type either.
  if (!payload.reserved_customer_id && !payload.reserved_buyer_name)
    delete payload.reserved_buyer_type
  emit('submit', payload, branchId.value ? Number(branchId.value) : null)
}
</script>

<style scoped>
.vf {
  display: flex;
  flex-direction: column;
  width: min(980px, calc(100vw - 32px));
  max-height: min(88vh, 920px);
  background: var(--fr-surface);
  border-radius: var(--fr-radius-lg, 14px);
  box-shadow: var(--fr-shadow);
  overflow: hidden;
  color: var(--fr-ink);
}
.vf-head {
  padding: 20px 24px 0;
  border-bottom: 1px solid var(--fr-border);
}
.vf-title {
  margin: 0;
  font-size: var(--fr-text-xl);
}
.vf-sub {
  margin: 4px 0 12px;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.vf-info {
  margin-top: -6px;
  color: var(--fr-info);
}
.vf-steps {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}
.vf-step {
  flex: none;
  padding: 8px 12px;
  border-bottom: 2px solid transparent;
  font-size: var(--fr-text-sm);
  font-weight: 600;
  color: var(--fr-muted);
  text-decoration: none;
  white-space: nowrap;
}
.vf-step:hover {
  color: var(--fr-primary);
}
.vf-step.done::after {
  content: ' ✓';
  color: var(--fr-success);
}
.vf-step.missing {
  color: var(--fr-danger);
  border-bottom-color: var(--fr-danger);
}
.vf-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 24px 24px;
  background: var(--fr-bg, #f6f9fc);
  scroll-padding-top: 12px;
}
.vf-section {
  margin-top: 16px;
  padding: 18px 20px 20px;
  background: var(--fr-surface);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius);
}
.vf-section h3 {
  margin: 0 0 14px;
  font-size: var(--fr-text-md);
  font-weight: 700;
}
.vf-section h3 small {
  margin-left: 6px;
  font-size: var(--fr-text-xs);
  font-weight: 500;
  color: var(--fr-muted);
}
.vf-note {
  margin: -6px 0 14px;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.vf-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 16px;
}
.vf-grid :deep(label),
.vf-block {
  display: grid;
  gap: 5px;
  align-content: start;
  min-width: 0;
  font-size: var(--fr-text-sm);
  font-weight: 600;
  color: var(--fr-ink);
}
.vf-block {
  margin-top: 14px;
}
.vf-wide {
  grid-column: span 2;
}
.vf :deep(.ui-field__hint),
.vf :deep(.ui-field__error) {
  font-size: var(--fr-text-xs);
  font-weight: 400;
}
.vf :deep(.ui-field__hint) {
  color: var(--fr-muted);
}
.vf :deep(.ui-field__error) {
  color: var(--fr-danger);
}
.vf-input {
  width: 100%;
  min-height: 40px;
  box-sizing: border-box;
  padding: 8px 11px;
  border: 1px solid var(--fr-border-strong);
  border-radius: 8px;
  background: #fff;
  color: var(--fr-ink);
  font: inherit;
  font-size: var(--fr-text-md);
  font-weight: 400;
}
textarea.vf-input {
  resize: vertical;
}
.vf-input:focus {
  outline: none;
  border-color: var(--fr-primary);
  box-shadow: 0 0 0 3px var(--fr-primary-soft);
}
.vf-input:disabled {
  background: #f3f6fa;
  color: var(--fr-muted);
}
label:has(.ui-field__error) .vf-input {
  border-color: var(--fr-danger);
}
.vf-plate {
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.vf-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.vf-unit {
  position: relative;
  display: block;
}
.vf-unit .vf-input {
  padding-right: 42px;
}
.vf-unit em {
  position: absolute;
  right: 11px;
  top: 50%;
  transform: translateY(-50%);
  font-style: normal;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
  pointer-events: none;
}
.vf-static {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  font-weight: 500;
}
.vf-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--fr-success);
}
.vf-segmented {
  display: flex;
  min-height: 40px;
  border: 1px solid var(--fr-border-strong);
  border-radius: 8px;
  overflow: hidden;
}
.vf-segmented button {
  flex: 1;
  border: 0;
  border-right: 1px solid var(--fr-border);
  background: #fff;
  color: var(--fr-ink);
  font: inherit;
  font-size: var(--fr-text-sm);
  cursor: pointer;
}
.vf-segmented button:last-child {
  border-right: 0;
}
.vf-segmented button.on {
  background: var(--fr-primary);
  color: #fff;
  font-weight: 600;
}
.vf-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-top: 1px solid var(--fr-border);
  background: var(--fr-surface);
}
.vf-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.vf-bar {
  width: 120px;
  height: 6px;
  border-radius: 3px;
  background: var(--fr-border);
  overflow: hidden;
}
.vf-bar span {
  display: block;
  height: 100%;
  background: var(--fr-success);
  transition: width 0.2s ease;
}
.vf-actions {
  display: flex;
  gap: 10px;
}
.vf-btn {
  min-height: 40px;
  padding: 0 18px;
  border: 1px solid var(--fr-border-strong);
  border-radius: 8px;
  background: #fff;
  color: var(--fr-ink);
  font: inherit;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}
.vf-btn.primary {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
}
.vf-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
@media (max-width: 860px) {
  .vf-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 560px) {
  .vf {
    width: 100vw;
    max-height: 100dvh;
    height: 100dvh;
    border-radius: 0;
  }
  .vf-head,
  .vf-body,
  .vf-foot {
    padding-left: 16px;
    padding-right: 16px;
  }
  .vf-grid {
    grid-template-columns: 1fr;
  }
  .vf-wide {
    grid-column: auto;
  }
  .vf-foot {
    flex-direction: column;
    align-items: stretch;
  }
  .vf-actions .vf-btn {
    flex: 1;
  }
}
</style>
