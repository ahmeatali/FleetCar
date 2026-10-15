<template>
  <div class="fp-workspace">
    <UiAlert v-if="error" tone="error"
      >{{ error }}
      <UiButton type="button" class="sw-button" @click="load">Yenile</UiButton></UiAlert
    >
    <UiAlert v-if="notice" tone="success">{{ notice }}</UiAlert>
    <p v-if="loading && !state" class="sw-muted">Operasyon bilgileri yükleniyor…</p>
    <template v-if="state">
      <section v-if="mode !== 'branches' && !compact" class="sw-card fp-toolbar">
        <UiField
          >Şube<select v-model="branchFilter" aria-label="Operasyon Şubesi">
            <option value="">Tüm şubeler ve atanmamış araçlar</option>
            <option v-for="b in state.branches" :key="b.id" :value="String(b.id)">
              {{ b.name }}{{ b.is_active ? '' : ' (Pasif)' }}
            </option>
          </select></UiField
        >
        <UiButton type="button" class="sw-button" :disabled="busy || loading" @click="load"
          >Yenile</UiButton
        >
      </section>

      <template v-if="mode === 'operations'">
        <section class="sw-card">
          <div class="sw-card-heading fp-heading">
            <div>
              <h2>{{ compact ? 'Günlük Operasyon İş Listesi' : 'Operasyon İş Listesi' }}</h2>
              <p class="sw-muted">
                Teslim, iade, servis ve rezervasyon kayıtlarından güncel işler.
              </p>
            </div>
            <router-link v-if="compact" to="/supplier-portal/operations" class="sw-button"
              >Tüm İşleri Gör</router-link
            >
          </div>
          <div v-if="!compact" class="fp-filters">
            <UiField
              >Görünüm<select aria-label="Görünüm" v-model="taskPeriod">
                <option value="today">Bugün ve gecikenler</option>
                <option value="tomorrow">Yarın</option>
                <option value="week">Önümüzdeki 7 gün</option>
                <option value="all">Tüm açık işler</option>
                <option value="done">Tamamlanan görevler</option>
              </select></UiField
            >
            <UiField
              >Kategori<select aria-label="Kategori" v-model="category">
                <option value="">Tümü</option>
                <option v-for="c in categories" :key="c">{{ c }}</option>
              </select></UiField
            >
            <UiField
              >Sorumlu<select aria-label="Sorumlu" v-model="assigneeFilter">
                <option value="">Tümü</option>
                <option value="none">Atanmamış</option>
                <option v-for="u in state.members" :key="u.id" :value="String(u.id)">
                  {{ u.name }}
                </option>
              </select></UiField
            >
          </div>
          <div class="fp-metrics">
            <span
              ><strong>{{ openTasks.length }}</strong> açık iş</span
            ><span
              ><strong>{{ lateCount }}</strong> geciken</span
            ><span
              ><strong>{{ todayCount }}</strong> bugün</span
            >
          </div>
          <UiTable class="sw-table-scroll"
            ><table class="sw-table">
              <thead>
                <tr>
                  <th>İş / Araç</th>
                  <th>Şube</th>
                  <th>Son Tarih</th>
                  <th>Sorumlu</th>
                  <th>Durum / İşlem</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in shownTasks" :key="task.key">
                  <td>
                    <strong>{{ task.title }}</strong
                    ><small>{{ plate(task.vehicle_id) }} · {{ task.category }}</small
                    ><small v-if="task.note">{{ task.note }}</small>
                  </td>
                  <td>{{ branchName(task.branch_id) }}</td>
                  <td>
                    <span
                      :class="{ 'fp-late': task.due_date < today && task.status !== 'Tamamlandı' }"
                      >{{ dayText(task.due_date) }}</span
                    >
                  </td>
                  <td>{{ memberName(task.assignee_id) }}</td>
                  <td>
                    <div class="fp-actions">
                      <span>{{ task.status }}</span
                      ><router-link v-if="task.url" class="sw-button" :to="task.url"
                        >İşi Aç</router-link
                      ><UiButton
                        v-if="canTask && !compact"
                        type="button"
                        class="sw-button"
                        :disabled="busy"
                        @click="editTask(task)"
                        >Görevi Düzenle</UiButton
                      >
                    </div>
                  </td>
                </tr>
                <tr v-if="!shownTasks.length">
                  <td colspan="5" class="sw-empty">Bu görünümde iş bulunamadı.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
        <section v-if="canTask && !compact" class="sw-card">
          <h2>{{ editingTask ? 'Görev Sorumlusu ve Notu' : 'Yeni Operasyon Görevi' }}</h2>
          <p v-if="editingTask?.derived" class="sw-muted">
            {{ editingTask.title }} — bağlı işin durumu ve son tarihi kaynak kayıttan alınır.
            Tamamlamak için “İşi Aç” bağlantısını kullanın.
          </p>
          <form class="fp-form" @submit.prevent="saveTask">
            <template v-if="!editingTask || !editingTask.derived"
              ><UiField
                >Görev Başlığı<input v-model="taskForm.title" required maxlength="200" /></UiField
              ><UiField>Son Tarih<input v-model="taskForm.due_date" type="date" required /></UiField
              ><UiField v-if="!editingTask"
                >Araç<select aria-label="Görev Aracı" v-model="taskForm.vehicle_id">
                  <option value="">Araçsız görev</option>
                  <option v-for="v in state.vehicles" :key="v.id" :value="v.id">
                    {{ v.plate }}
                  </option>
                </select></UiField
              ><UiField v-if="!editingTask"
                >Şube<select aria-label="Görev Şubesi" v-model="taskForm.branch_id">
                  <option value="">Şube seçilmedi</option>
                  <option v-for="b in activeBranches" :key="b.id" :value="b.id">
                    {{ b.name }}
                  </option>
                </select></UiField
              ></template
            >
            <UiField
              >Sorumlu Kullanıcı<select
                aria-label="Sorumlu Kullanıcı"
                v-model="taskForm.assignee_id"
              >
                <option value="">Atanmamış</option>
                <option
                  v-if="
                    editingTask?.assignee_id &&
                    !state.members.some((u) => u.id === editingTask.assignee_id)
                  "
                  :value="editingTask.assignee_id"
                >
                  Pasif kullanıcı — yeni sorumlu seçin
                </option>
                <option v-for="u in state.members" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select></UiField
            >
            <UiField v-if="editingTask && !editingTask.derived"
              >Görev Durumu<select aria-label="Görev Durumu" v-model="taskForm.status">
                <option>Açık</option>
                <option>Devam Ediyor</option>
                <option>Tamamlandı</option>
              </select></UiField
            >
            <UiField class="fp-wide"
              >Görev Notu<textarea v-model="taskForm.note" rows="2" maxlength="2000" />
            </UiField>
            <div class="fp-actions fp-wide">
              <UiButton type="submit" class="sw-button primary" :disabled="busy">{{
                editingTask ? 'Görevi Kaydet' : 'Görev Ekle'
              }}</UiButton
              ><UiButton v-if="editingTask" type="button" class="sw-button" @click="resetTask"
                >Vazgeç</UiButton
              >
            </div>
          </form>
        </section>
      </template>

      <template v-else-if="mode === 'branches'">
        <section class="sw-card">
          <div class="sw-card-heading fp-heading">
            <div>
              <h2>Şubeler ve Lokasyonlar</h2>
              <p class="sw-muted">
                Şubeleri tanımlayın, araçların bağlı ve bulunduğu şubeyi takip edin.
              </p>
            </div>
          </div>
          <UiTable class="sw-table-scroll"
            ><table class="sw-table">
              <thead>
                <tr>
                  <th>Şube / Şehir</th>
                  <th>Adres</th>
                  <th>Bulunan Araç</th>
                  <th>Durum</th>
                  <th>İşlem</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in state.branches" :key="b.id">
                  <td>
                    <strong>{{ b.name }}</strong
                    ><small>{{ b.city }}</small>
                  </td>
                  <td>{{ b.address || '—' }}</td>
                  <td>
                    {{
                      state.vehicles.filter((v) => v.location?.current_branch_id === b.id).length
                    }}
                  </td>
                  <td>{{ b.is_active ? 'Aktif' : 'Pasif' }}</td>
                  <td>
                    <UiButton
                      v-if="canBranch"
                      type="button"
                      class="sw-button"
                      :disabled="busy"
                      @click="editBranch(b)"
                      >Şubeyi Düzenle</UiButton
                    >
                  </td>
                </tr>
                <tr v-if="!state.branches.length">
                  <td colspan="5">Henüz şube tanımlanmadı.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
          <p class="sw-muted">
            {{ state.vehicles.filter((v) => !v.location).length }} aracın şube ataması bekliyor.
            Lokasyon güncellemesi GPS konumu veya teslimat işlemi oluşturmaz.
          </p>
        </section>
        <section v-if="canBranch" class="sw-card">
          <h2>{{ editingBranch ? 'Şubeyi Düzenle' : 'Yeni Şube' }}</h2>
          <form class="fp-form" @submit.prevent="saveBranch">
            <UiField>Şube Adı<input v-model="branchForm.name" required maxlength="100" /></UiField
            ><UiField>Şehir<input v-model="branchForm.city" required maxlength="100" /></UiField
            ><UiField class="fp-wide"
              >Adres<input v-model="branchForm.address" maxlength="500" /></UiField
            ><UiField
              >Şube Durumu<select aria-label="Şube Durumu" v-model="branchForm.is_active">
                <option :value="true">Aktif</option>
                <option :value="false">Pasif</option>
              </select></UiField
            >
            <div class="fp-actions fp-wide">
              <UiButton class="sw-button primary" type="submit" :disabled="busy">{{
                editingBranch ? 'Şubeyi Kaydet' : 'Şube Ekle'
              }}</UiButton
              ><UiButton v-if="editingBranch" class="sw-button" type="button" @click="resetBranch"
                >Vazgeç</UiButton
              >
            </div>
          </form>
        </section>
        <section class="sw-card">
          <h2>Araç Lokasyonları</h2>
          <div class="fp-filters">
            <UiField
              >Araç Ara<input v-model="vehicleSearch" placeholder="Plaka, marka veya model"
            /></UiField>
          </div>
          <UiTable class="sw-table-scroll"
            ><table class="sw-table">
              <thead>
                <tr>
                  <th>Araç</th>
                  <th>Bağlı Şube</th>
                  <th>Bulunduğu Şube</th>
                  <th>Konum Notu</th>
                  <th>Son Güncelleme</th>
                  <th>İşlem</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in filteredVehicles" :key="v.id">
                  <td>
                    {{ v.plate }}<small>{{ v.brand }} {{ v.model }}</small>
                  </td>
                  <td>{{ branchName(v.location?.home_branch_id) }}</td>
                  <td>{{ branchName(v.location?.current_branch_id) }}</td>
                  <td>{{ v.location?.location_note || '—' }}</td>
                  <td>
                    {{
                      v.location?.updated_at
                        ? new Date(v.location.updated_at).toLocaleString('tr-TR')
                        : '—'
                    }}<small>{{ v.location?.updated_by }}</small>
                  </td>
                  <td>
                    <UiButton
                      v-if="canVehicle"
                      type="button"
                      class="sw-button"
                      @click="editLocation(v)"
                      >Lokasyonu Düzenle</UiButton
                    >
                  </td>
                </tr>
                <tr v-if="!filteredVehicles.length">
                  <td colspan="6">Araç bulunamadı.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
        <section v-if="editingVehicle && canVehicle" class="sw-card">
          <h2>{{ editingVehicle.plate }} — Araç Lokasyonu</h2>
          <form class="fp-form" @submit.prevent="saveLocation">
            <UiField
              >Bağlı Şube<select
                aria-label="Bağlı Şube"
                v-model="locationForm.home_branch_id"
                required
              >
                <option value="">Şube seçin</option>
                <option v-for="b in activeBranches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select></UiField
            ><UiField
              >Bulunduğu Şube<select
                aria-label="Bulunduğu Şube"
                v-model="locationForm.current_branch_id"
                required
              >
                <option value="">Şube seçin</option>
                <option v-for="b in activeBranches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select></UiField
            ><UiField class="fp-wide"
              >Konum Notu<input
                v-model="locationForm.location_note"
                maxlength="300"
                placeholder="Otopark, teslim noktası veya açıklama"
            /></UiField>
            <div class="fp-actions fp-wide">
              <UiButton type="submit" class="sw-button primary" :disabled="busy"
                >Lokasyonu Kaydet</UiButton
              ><UiButton type="button" class="sw-button" @click="editingVehicle = null"
                >Vazgeç</UiButton
              >
            </div>
          </form>
        </section>
      </template>

      <template v-else-if="mode === 'reservations'">
        <section class="sw-card">
          <h2>Rezervasyon ve Müsaitlik Takvimi</h2>
          <p class="sw-muted">
            Mavi: rezervasyon · Mor: sözleşme · Açık yeşil: tarih engeli yok. Başlangıç ve dönüş
            günleri dahil tutulur. Servis, hasar, satış veya gecikmiş iade durumları rezervasyonu
            engeller.
          </p>
          <form class="fp-filters" @submit.prevent="loadCalendar">
            <UiField
              >Takvim Başlangıcı<input v-model="calendarStart" type="date" required /></UiField
            ><UiField
              >Gün Sayısı<select aria-label="Gün Sayısı" v-model.number="calendarDays">
                <option :value="7">7 gün</option>
                <option :value="14">14 gün</option>
                <option :value="31">31 gün</option>
              </select></UiField
            ><UiField
              >Araç / Grup Ara<input
                v-model="vehicleSearch"
                placeholder="Plaka, marka veya araç grubu" /></UiField
            ><UiButton type="submit" class="sw-button" :disabled="loading">Takvimi Göster</UiButton>
          </form>
          <UiTable class="sw-table-scroll fp-calendar"
            ><table class="sw-table">
              <thead>
                <tr>
                  <th>Araç / Durum</th>
                  <th v-for="day in calendarDates" :key="day">{{ dayText(day) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="v in calendarVehicles" :key="v.id">
                  <th>
                    {{ v.plate }}<small>{{ v.group }} · {{ v.status }}</small
                    ><small>{{
                      calendarRows.find((r) => r.vehicle_id === v.id)?.reason ||
                      'Seçilen aralık müsait'
                    }}</small>
                  </th>
                  <td
                    v-for="day in calendarDates"
                    :key="day"
                    :class="dayState(v.id, day).className"
                    :title="dayState(v.id, day).label"
                  >
                    {{ dayState(v.id, day).label }}
                  </td>
                </tr>
                <tr v-if="!calendarVehicles.length">
                  <td :colspan="calendarDates.length + 1">Bu şube veya aramada araç bulunamadı.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
        <section v-if="canReserve" class="sw-card">
          <h2>Yeni Rezervasyon</h2>
          <p class="sw-muted">
            Araç güncel teslim şubesinden seçilir. Tarih çakışması kayıt sırasında sunucuda tekrar
            kontrol edilir. Şube ve araç lokasyonu tanımlamak için
            <router-link to="/supplier-portal/branches">Şube ve Lokasyonlar</router-link> sayfasını
            kullanın.
          </p>
          <form class="fp-form" @submit.prevent="saveReservation">
            <UiField
              >Müşteri<select aria-label="Müşteri" v-model="reservationForm.customer_id" required>
                <option value="">Müşteri seçin</option>
                <option v-for="c in customers" :key="c.id" :value="c.id">
                  {{ c.title || c.company_name }}
                </option>
              </select></UiField
            >
            <UiField
              >Rezervasyon Aracı<select
                aria-label="Rezervasyon Aracı"
                v-model="reservationForm.vehicle_id"
                required
              >
                <option value="">Araç seçin</option>
                <option
                  v-for="v in state.vehicles.filter((v) => v.is_active)"
                  :key="v.id"
                  :value="v.id"
                >
                  {{ v.plate }} · {{ v.brand }} {{ v.model }}
                </option>
              </select></UiField
            >
            <UiField
              >Teslim Şubesi<select
                aria-label="Teslim Şubesi"
                v-model="reservationForm.pickup_branch_id"
                required
              >
                <option value="">Şube seçin</option>
                <option v-for="b in activeBranches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select></UiField
            >
            <UiField
              >Dönüş Şubesi<select
                aria-label="Dönüş Şubesi"
                v-model="reservationForm.return_branch_id"
                required
              >
                <option value="">Şube seçin</option>
                <option v-for="b in activeBranches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select></UiField
            >
            <UiField
              >Rezervasyon Başlangıcı<input
                v-model="reservationForm.start_date"
                type="date"
                :min="today"
                required /></UiField
            ><UiField
              >Rezervasyon Bitişi<input
                v-model="reservationForm.end_date"
                type="date"
                :min="reservationForm.start_date || today"
                required
            /></UiField>
            <UiField
              >Aylık Kira (TL)<input
                v-model.number="reservationForm.monthly_rent"
                type="number"
                min="0.01"
                max="100000000"
                step="0.01"
                required /></UiField
            ><UiField
              >Rezervasyon Notu<textarea v-model="reservationForm.note" maxlength="2000" rows="2" />
            </UiField>
            <UiButton type="submit" class="sw-button primary" :disabled="busy"
              >Rezervasyon Oluştur</UiButton
            >
          </form>
        </section>
        <section class="sw-card">
          <h2>Rezervasyon Kayıtları</h2>
          <UiTable class="sw-table-scroll"
            ><table class="sw-table">
              <thead>
                <tr>
                  <th>No / Müşteri</th>
                  <th>Araç</th>
                  <th>Tarih</th>
                  <th>Teslim / Dönüş Şubesi</th>
                  <th>Aylık Kira</th>
                  <th>Durum / İşlem</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in visibleReservations" :key="r.id">
                  <td>
                    #{{ r.id }}<small>{{ customerName(r.customer_id) }}</small>
                  </td>
                  <td>{{ plate(r.vehicle_id) }}</td>
                  <td>{{ dayText(r.start_date) }} — {{ dayText(r.end_date) }}</td>
                  <td>
                    {{ branchName(r.pickup_branch_id)
                    }}<small>{{ branchName(r.return_branch_id) }}</small>
                  </td>
                  <td>{{ money(r.monthly_rent) }}</td>
                  <td>
                    <span>{{ r.status }}</span>
                    <div class="fp-actions">
                      <template v-if="canReserve && r.status === 'Onaylandı'"
                        ><UiButton
                          class="sw-button"
                          type="button"
                          :disabled="busy"
                          @click="reservationAction(r, 'convert')"
                          >Sözleşme Taslağı Oluştur</UiButton
                        ><UiButton
                          class="sw-button"
                          type="button"
                          :disabled="busy"
                          @click="cancelTarget = r"
                          >İptal Et</UiButton
                        ></template
                      ><router-link
                        v-if="r.contract_id"
                        class="sw-button"
                        :to="`/supplier-portal/contracts?record=${r.contract_id}`"
                        >Sözleşmeyi Aç</router-link
                      >
                    </div>
                  </td>
                </tr>
                <tr v-if="!visibleReservations.length">
                  <td colspan="6">Henüz rezervasyon bulunamadı.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
          <div v-if="cancelTarget" class="fp-confirm" role="alert">
            <p>
              #{{ cancelTarget.id }} rezervasyonu iptal edilsin mi? Tarih engeli kaldırılacak,
              geçmiş kayıt korunacak.
            </p>
            <div class="fp-actions">
              <UiButton
                type="button"
                class="sw-button"
                :disabled="busy"
                @click="reservationAction(cancelTarget, 'cancel')"
                >İptali Onayla</UiButton
              ><UiButton type="button" class="sw-button" @click="cancelTarget = null"
                >Vazgeç</UiButton
              >
            </div>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { UiAlert, UiButton, UiField, UiTable } from './ui/index.js'
import { supplierApi } from '../utils/supplierApi'
const props = defineProps({
  mode: { type: String, default: 'operations' },
  compact: Boolean,
  role: { type: String, default: 'viewer' },
  customers: { type: Array, default: () => [] },
})
const state = ref(null),
  taskRows = ref([]),
  reservations = ref([]),
  calendarRows = ref([])
const loading = ref(false),
  busy = ref(false),
  error = ref(''),
  notice = ref('')
const branchFilter = ref(''),
  taskPeriod = ref('today'),
  category = ref(''),
  assigneeFilter = ref(''),
  vehicleSearch = ref('')
const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(new Date())
const addDays = (day, count) => {
  const d = new Date(day + 'T12:00:00Z')
  d.setUTCDate(d.getUTCDate() + count)
  return d.toISOString().slice(0, 10)
}
const dayText = (day) => (day ? new Date(day + 'T12:00:00Z').toLocaleDateString('tr-TR') : '—')
const money = (value) =>
  Number(value).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })
const calendarStart = ref(today),
  calendarDays = ref(14),
  loadedStart = ref(today),
  loadedDays = ref(14)
const calendarDates = computed(() =>
  Array.from({ length: loadedDays.value }, (_, i) => addDays(loadedStart.value, i)),
)
const activeBranches = computed(() => state.value?.branches.filter((b) => b.is_active) || [])
const canBranch = computed(() => ['owner', 'fleet_manager'].includes(props.role))
const canVehicle = computed(() => ['owner', 'fleet_manager', 'operations'].includes(props.role))
const canTask = computed(() =>
  ['owner', 'fleet_manager', 'operations', 'delivery'].includes(props.role),
)
const canReserve = computed(() =>
  ['owner', 'fleet_manager', 'operations', 'sales'].includes(props.role),
)
const plate = (id) => state.value?.vehicles.find((v) => v.id === id)?.plate || '—'
const branchName = (id) => state.value?.branches.find((b) => b.id === id)?.name || 'Atanmamış'
const memberName = (id) =>
  state.value?.members.find((u) => u.id === id)?.name || (id ? 'Pasif kullanıcı' : 'Atanmamış')
const customerName = (id) =>
  props.customers.find((c) => c.id === id)?.title ||
  props.customers.find((c) => c.id === id)?.company_name ||
  '—'
const belongs = (task) => !branchFilter.value || String(task.branch_id) === branchFilter.value
const openTasks = computed(() =>
  taskRows.value.filter((t) => t.status !== 'Tamamlandı' && belongs(t)),
)
const lateCount = computed(() => openTasks.value.filter((t) => t.due_date < today).length)
const todayCount = computed(() => openTasks.value.filter((t) => t.due_date === today).length)
const categories = ['Teslim', 'İade', 'Servis', 'Bakım', 'Rezervasyon', 'Görev']
const shownTasks = computed(() => {
  const period = props.compact ? 'today' : taskPeriod.value
  return taskRows.value
    .filter(
      (t) =>
        belongs(t) &&
        (!category.value || props.compact || t.category === category.value) &&
        (!assigneeFilter.value ||
          props.compact ||
          (assigneeFilter.value === 'none'
            ? !t.assignee_id
            : String(t.assignee_id) === assigneeFilter.value)) &&
        (period === 'done'
          ? t.status === 'Tamamlandı'
          : t.status !== 'Tamamlandı' &&
            (period === 'today'
              ? t.due_date <= today
              : period === 'tomorrow'
                ? t.due_date === addDays(today, 1)
                : period === 'week'
                  ? t.due_date >= today && t.due_date <= addDays(today, 6)
                  : true)),
    )
    .slice(0, props.compact ? 5 : undefined)
})
const filteredVehicles = computed(() =>
  (state.value?.vehicles || []).filter((v) =>
    `${v.plate} ${v.brand} ${v.model} ${v.group}`
      .toLocaleLowerCase('tr-TR')
      .includes(vehicleSearch.value.toLocaleLowerCase('tr-TR')),
  ),
)
const calendarVehicles = computed(() =>
  filteredVehicles.value.filter((v) => calendarRows.value.some((r) => r.vehicle_id === v.id)),
)
const visibleReservations = computed(() =>
  reservations.value.filter(
    (r) =>
      !branchFilter.value ||
      String(r.pickup_branch_id) === branchFilter.value ||
      String(r.return_branch_id) === branchFilter.value,
  ),
)
function dayState(id, day) {
  const row = calendarRows.value.find((r) => r.vehicle_id === id)
  const block = row?.blocks.find((b) => b.start.slice(0, 10) <= day && b.end.slice(0, 10) >= day)
  if (block)
    return {
      className: block.kind === 'reservation' ? 'fp-booked' : 'fp-contracted',
      label: block.label,
    }
  if (row?.operational_reason) return { className: 'fp-unavailable', label: 'Uygun değil' }
  return { className: 'fp-available', label: '—' }
}
let loadSequence = 0,
  calendarSequence = 0
async function calendarFetch() {
  const seq = ++calendarSequence
  const start = calendarStart.value,
    days = calendarDays.value
  const query = new URLSearchParams({ start_date: start, end_date: addDays(start, days - 1) })
  if (branchFilter.value) query.set('branch_id', branchFilter.value)
  const result = await supplierApi('/fleet/availability?' + query)
  if (seq === calendarSequence) {
    calendarRows.value = result
    loadedStart.value = start
    loadedDays.value = days
  }
}
async function loadCalendar() {
  error.value = ''
  loading.value = true
  try {
    await calendarFetch()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
async function load() {
  const seq = ++loadSequence
  loading.value = true
  error.value = ''
  try {
    const [overview, tasks, booked] = await Promise.all([
      supplierApi('/fleet/overview'),
      props.mode === 'operations' ? supplierApi('/fleet/tasks') : [],
      props.mode === 'reservations' ? supplierApi('/fleet/reservations') : [],
    ])
    if (seq !== loadSequence) return
    state.value = overview
    taskRows.value = tasks
    reservations.value = booked
    if (props.mode === 'reservations') await calendarFetch()
  } catch (e) {
    if (seq === loadSequence) error.value = e.message
  } finally {
    if (seq === loadSequence) loading.value = false
  }
}
async function act(action, message) {
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await action()
    notice.value = message
    await load()
    return true
  } catch (e) {
    error.value = e.message
    return false
  } finally {
    busy.value = false
  }
}
const editingBranch = ref(null),
  branchForm = reactive({ name: '', city: '', address: '', is_active: true, version: 0 })
function resetBranch() {
  editingBranch.value = null
  Object.assign(branchForm, { name: '', city: '', address: '', is_active: true, version: 0 })
}
function editBranch(b) {
  editingBranch.value = b
  Object.assign(branchForm, b)
}
async function saveBranch() {
  const body = {
    name: branchForm.name,
    city: branchForm.city,
    address: branchForm.address,
    is_active: branchForm.is_active,
    version: branchForm.version,
  }
  if (
    await act(
      () =>
        supplierApi('/fleet/branches' + (editingBranch.value ? '/' + editingBranch.value.id : ''), {
          method: editingBranch.value ? 'PUT' : 'POST',
          body,
        }),
      'Şube kaydedildi.',
    )
  )
    resetBranch()
}
const editingVehicle = ref(null),
  locationForm = reactive({
    home_branch_id: '',
    current_branch_id: '',
    location_note: '',
    version: 0,
  })
function editLocation(v) {
  editingVehicle.value = v
  Object.assign(
    locationForm,
    { home_branch_id: '', current_branch_id: '', location_note: '', version: 0 },
    v.location || {},
  )
}
async function saveLocation() {
  const body = {
    home_branch_id: locationForm.home_branch_id,
    current_branch_id: locationForm.current_branch_id,
    location_note: locationForm.location_note,
    version: locationForm.version,
  }
  if (
    await act(
      () =>
        supplierApi('/fleet/locations/' + encodeURIComponent(editingVehicle.value.id), {
          method: 'PUT',
          body,
        }),
      'Araç lokasyonu kaydedildi.',
    )
  )
    editingVehicle.value = null
}
const editingTask = ref(null),
  taskForm = reactive({
    title: '',
    due_date: today,
    vehicle_id: '',
    branch_id: '',
    assignee_id: '',
    note: '',
    status: 'Açık',
  })
function resetTask() {
  editingTask.value = null
  Object.assign(taskForm, {
    title: '',
    due_date: today,
    vehicle_id: '',
    branch_id: '',
    assignee_id: '',
    note: '',
    status: 'Açık',
  })
}
function editTask(task) {
  editingTask.value = task
  Object.assign(taskForm, { ...task, assignee_id: task.assignee_id || '' })
}
async function saveTask() {
  const task = editingTask.value
  const body = task
    ? {
        assignee_id: taskForm.assignee_id || null,
        note: taskForm.note,
        ...(task.derived ? {} : { title: taskForm.title, due_date: taskForm.due_date }),
        status: task.derived ? 'Açık' : taskForm.status,
        version: task.version,
      }
    : {
        title: taskForm.title,
        due_date: taskForm.due_date,
        vehicle_id: taskForm.vehicle_id || null,
        branch_id: taskForm.branch_id || null,
        assignee_id: taskForm.assignee_id || null,
        note: taskForm.note,
      }
  if (
    await act(
      () =>
        supplierApi('/fleet/tasks' + (task ? '/' + task.key : ''), {
          method: task ? 'PUT' : 'POST',
          body,
        }),
      'Görev kaydedildi.',
    )
  )
    resetTask()
}
const reservationForm = reactive({
  customer_id: '',
  vehicle_id: '',
  pickup_branch_id: '',
  return_branch_id: '',
  start_date: today,
  end_date: addDays(today, 7),
  monthly_rent: '',
  note: '',
})
const cancelTarget = ref(null)
async function saveReservation() {
  if (
    await act(
      () => supplierApi('/fleet/reservations', { method: 'POST', body: { ...reservationForm } }),
      'Rezervasyon oluşturuldu.',
    )
  )
    reservationForm.note = ''
}
async function reservationAction(row, action) {
  if (
    await act(
      () =>
        supplierApi(`/fleet/reservations/${row.id}/${action}`, {
          method: 'POST',
          body: { version: row.version },
        }),
      action === 'convert'
        ? 'Sözleşme taslağı oluşturuldu. Mevcut imza ve onay adımları sözleşme ekranından devam eder.'
        : 'Rezervasyon iptal edildi.',
    )
  )
    cancelTarget.value = null
}
watch(
  () => props.mode,
  () => {
    notice.value = ''
    resetTask()
    resetBranch()
    editingVehicle.value = null
    cancelTarget.value = null
    load()
  },
)
watch(branchFilter, () => {
  if (props.mode === 'reservations') loadCalendar()
})
onMounted(load)
</script>
<style scoped>
.fp-workspace {
  min-width: 0;
}
.fp-workspace .sw-card {
  margin-bottom: 20px;
}
.fp-heading {
  flex-wrap: wrap;
  gap: 12px;
}
.fp-heading h2 {
  margin-bottom: 5px;
}
.fp-toolbar,
.fp-filters {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: end;
}
.fp-filters {
  margin: 18px 0;
}
.fp-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 18px;
}
.fp-wide {
  grid-column: 1 / -1;
}
.fp-workspace label {
  display: grid;
  gap: 7px;
  font-size: 12px;
  color: #526f98;
  min-width: 0;
}
.fp-filters label,
.fp-toolbar label {
  flex: 1;
  min-width: 160px;
}
.fp-workspace input,
.fp-workspace select,
.fp-workspace textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 40px;
  padding: 9px 10px;
  font: inherit;
  font-size: 13px;
  color: #254774;
  border: 1px solid #dfe9f6;
  border-radius: 6px;
  background: white;
}
.fp-workspace :is(input, select, textarea):focus-visible {
  outline: 2px solid #0064ff;
  outline-offset: 2px;
}
.fp-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.fp-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  padding: 14px 0;
  font-size: 12px;
  color: #526f98;
}
.fp-metrics strong {
  font-size: 18px;
  color: #062464;
  margin-right: 5px;
}
.fp-late {
  color: #b42318;
  font-weight: 700;
}
.fp-calendar {
  max-height: 520px;
}
.fp-calendar .sw-table {
  min-width: max-content;
}
.fp-calendar th:first-child {
  position: sticky;
  left: 0;
  z-index: 1;
  background: #f8fbff;
  min-width: 170px;
  max-width: 220px;
  white-space: normal;
}
.fp-calendar th small {
  display: block;
  margin-top: 4px;
  font-weight: 400;
  line-height: 1.5;
}
.fp-calendar td {
  min-width: 100px;
  text-align: center;
  font-size: 10px;
}
.fp-calendar .fp-booked {
  background: #e8f1ff;
  color: #1652a4;
}
.fp-calendar .fp-contracted {
  background: #f0eaff;
  color: #7040a8;
}
.fp-calendar .fp-unavailable {
  background: #f2f4f7;
  color: #667085;
}
.fp-calendar .fp-available {
  background: #f0faf5;
}
.fp-confirm {
  padding: 16px;
  border: 1px solid #f5ca8d;
  border-radius: 8px;
  background: #fff8ed;
  margin-top: 16px;
  font-size: 13px;
}
@media (max-width: 600px) {
  .fp-form {
    grid-template-columns: 1fr;
  }
  .fp-filters label,
  .fp-toolbar label {
    flex-basis: 100%;
  }
  .fp-filters .sw-button {
    width: 100%;
  }
}
</style>
