<template>
  <div class="portal-layout">
    <Sidebar :supplier="supplier" />
    <main class="portal-main team-page" :aria-busy="loading">
      <header class="team-heading">
        <div>
          <span class="eyebrow">{{ supplier ? 'TEDARİKÇİ PORTALI' : 'MÜŞTERİ PORTALI' }}</span>
          <h1>Kullanıcılar ve Yetkiler</h1>
          <p>Ekip üyelerinizi, davetleri ve modül erişim izinlerini yönetin.</p>
        </div>
        <div class="team-actions">
          <UiButton class="btn" :disabled="!data || busy" @click="newRole">＋ Yeni Rol</UiButton
          ><UiButton class="btn btn-blue" :disabled="!data || busy" @click="newUser"
            >＋ Yeni Kullanıcı</UiButton
          >
        </div>
      </header>
      <UiAlert v-if="error" tone="error"
        >{{ error }}
        <UiButton v-if="!data" class="btn" @click="load">Tekrar Dene</UiButton></UiAlert
      >
      <UiAlert v-if="notice" tone="success">{{ notice }}</UiAlert>
      <UiAlert v-if="loading" tone="info">Kullanıcılar yükleniyor…</UiAlert>
      <template v-if="data">
        <section class="team-stats" aria-label="Ekip özeti">
          <article v-for="stat in stats" :key="stat.label">
            <span>{{ stat.label }}</span
            ><strong>{{ stat.count }}</strong>
          </article>
        </section>
        <nav class="team-tabs" aria-label="Kullanıcı yönetimi sekmeleri">
          <UiButton
            v-for="item in tabs"
            :key="item.id"
            :class="{ current: tab === item.id }"
            :aria-pressed="tab === item.id"
            @click="tab = item.id"
            >{{ item.label }}</UiButton
          >
        </nav>
        <template v-if="tab === 'users'">
          <p class="team-hint">
            Şirket hesabı sahibi tüm erişimleri korur. Rol ve izin değişiklikleri kullanıcının açık
            oturumlarını kapatır. Yeni kullanıcı daveti 48 saat geçerlidir.
          </p>
          <div class="team-columns">
            <section class="team-card user-list">
              <div class="team-filters">
                <UiField
                  >Kullanıcı ara<input
                    v-model="search"
                    placeholder="Ad, e-posta veya departman"
                    type="search" /></UiField
                ><UiField
                  >Rol<select v-model="roleFilter" aria-label="Rol filtresi">
                    <option value="">Tüm Roller</option>
                    <option v-for="role in data.roles" :key="role.key" :value="role.key">
                      {{ roleName(role) }}
                    </option>
                  </select></UiField
                ><UiField
                  >Durum<select v-model="statusFilter" aria-label="Durum filtresi">
                    <option value="">Tüm Durumlar</option>
                    <option>Aktif</option>
                    <option>Pasif</option>
                    <option>Davet Bekliyor</option>
                    <option>Davet Edilmedi</option>
                    <option>Davet Süresi Doldu</option>
                  </select></UiField
                >
              </div>
              <UiTable label="Ekip kullanıcıları"
                ><table class="team-table">
                  <thead>
                    <tr>
                      <th>Ad Soyad / E-posta</th>
                      <th>Rol</th>
                      <th>Durum</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="user in pageUsers"
                      :key="user.id"
                      :class="{ selected: selectedId === user.id }"
                    >
                      <td>
                        <div class="user-identity">
                          <span class="team-avatar">{{ initials(user.name) }}</span>
                          <div>
                            <strong>{{ user.name }}</strong
                            ><small>{{ user.email }}</small
                            ><small v-if="user.department">{{ user.department }}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span class="role-badge">{{
                          roleName(data.roles.find((role) => role.key === user.role)) ||
                          user.role_name
                        }}</span>
                      </td>
                      <td>
                        <span class="status-badge" :class="{ active: user.status === 'Aktif' }">{{
                          user.status
                        }}</span>
                      </td>
                      <td>
                        <UiButton
                          class="btn small"
                          :disabled="busy"
                          :aria-label="`${user.name} düzenle`"
                          @click="selectUser(user)"
                          >Düzenle</UiButton
                        >
                      </td>
                    </tr>
                    <tr v-if="!filteredUsers.length">
                      <td colspan="4">
                        {{
                          data.users.length
                            ? 'Aramanıza uygun kullanıcı bulunamadı.'
                            : 'Henüz ekip üyesi eklenmedi. Yeni kullanıcı ekleyerek başlayın.'
                        }}
                      </td>
                    </tr>
                  </tbody>
                </table></UiTable
              >
              <footer class="team-pagination">
                <span>{{ filteredUsers.length }} kullanıcı</span>
                <div>
                  <UiButton
                    class="btn small"
                    :disabled="page <= 1"
                    aria-label="Önceki sayfa"
                    @click="page--"
                    >‹</UiButton
                  ><span>{{ page }} / {{ pageCount }}</span
                  ><UiButton
                    class="btn small"
                    :disabled="page >= pageCount"
                    aria-label="Sonraki sayfa"
                    @click="page++"
                    >›</UiButton
                  >
                </div>
              </footer>
            </section>
            <section class="team-card user-details">
              <template v-if="selectedId && edit"
                ><div class="team-detail-header">
                  <div class="user-identity">
                    <span class="team-avatar">{{ initials(edit.name) }}</span>
                    <div>
                      <h2>{{ edit.name }}</h2>
                      <small>{{ edit.email }}</small>
                    </div>
                  </div>
                  <span class="status-badge">{{ selectedUser?.status }}</span>
                </div>
                <form @submit.prevent="saveUser">
                  <div class="team-form-grid">
                    <UiField>Ad Soyad<input v-model="edit.name" required maxlength="100" /></UiField
                    ><UiField>Departman<input v-model="edit.department" maxlength="100" /></UiField
                    ><UiField
                      >Rol<select
                        aria-label="Rol"
                        :value="edit.role"
                        @change="changeUserRole($event.target.value)"
                      >
                        <option v-for="role in data.roles" :key="role.key" :value="role.key">
                          {{ roleName(role) }}
                        </option>
                      </select></UiField
                    ><UiField
                      >Hesap Durumu<select v-model="edit.is_active" aria-label="Hesap Durumu">
                        <option :value="true">Etkin</option>
                        <option :value="false">Pasif</option>
                      </select></UiField
                    ><template v-if="!supplier"
                      ><UiField>Telefon<input v-model="edit.phone" maxlength="40" /></UiField
                      ><UiField
                        >Tahsis Edilen Araç<select
                          v-model="edit.assigned_plate"
                          aria-label="Tahsis Edilen Araç"
                        >
                          <option value="">Araç seçilmedi</option>
                          <option
                            v-for="vehicle in vehicles"
                            :key="vehicle.id"
                            :value="vehicle.plate"
                          >
                            {{ vehicle.plate }}
                          </option>
                        </select></UiField
                      ></template
                    >
                  </div>
                  <h3>Modül Bazında Erişim</h3>
                  <label v-if="edit.role.startsWith('custom:')" class="team-check"
                    ><input v-model="edit.custom_permissions" type="checkbox" /> Bu kullanıcı için
                    özel izinler tanımla</label
                  >
                  <p class="team-hint">
                    İşaretler kullanıcıya özel izinlerdir. Desteklenmeyen işlemler temel rol
                    tarafından kapatılır. Görüntüleme kapatıldığında o modülün işlem izinleri de
                    kaldırılır.
                  </p>
                  <PermissionMatrix
                    v-model="edit.permissions"
                    :modules="data.modules"
                    :actions="data.actions"
                    :ceiling="userCeiling"
                    :readonly="edit.role.startsWith('custom:') && !edit.custom_permissions"
                  />
                  <footer class="team-actions detail-actions">
                    <UiButton
                      type="button"
                      class="btn"
                      :disabled="busy || !edit.is_active"
                      @click="invite(selectedId)"
                      >Davet Gönder / Yenile</UiButton
                    ><UiButton
                      type="button"
                      class="btn"
                      :disabled="busy"
                      @click="revokeInvite(selectedId)"
                      >Daveti İptal Et</UiButton
                    ><UiButton class="btn btn-blue" :disabled="busy"
                      >Değişiklikleri Kaydet</UiButton
                    >
                  </footer>
                </form></template
              >
              <div v-else class="team-empty">
                <span>♧</span>
                <h2>Kullanıcı seçin</h2>
                <p>
                  Bilgilerini ve erişim izinlerini düzenlemek için listeden bir ekip üyesi seçin.
                </p>
              </div>
            </section>
          </div>
        </template>
        <section v-else-if="tab === 'roles'" class="team-card">
          <header class="team-detail-header">
            <div>
              <h2>Roller ve İzin Şablonları</h2>
              <p class="team-hint">
                Sistem rollerini kopyalayarak şirketinize özel roller oluşturun. Şablonlar temel
                rolün mevcut işlem yetkilerini aşamaz.
              </p>
            </div>
          </header>
          <UiTable label="Rol şablonları"
            ><table class="team-table">
              <thead>
                <tr>
                  <th>Rol Adı</th>
                  <th>Açıklama</th>
                  <th>Kullanıcı</th>
                  <th>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="role in data.roles" :key="role.key">
                  <td>
                    <strong>{{ roleName(role) }}</strong
                    ><small>{{ role.system ? 'Sistem rolü' : 'Özel rol' }}</small>
                  </td>
                  <td>{{ role.description }}</td>
                  <td>{{ data.users.filter((user) => user.role === role.key).length }}</td>
                  <td>
                    <div class="team-actions">
                      <UiButton class="btn small" @click="openRole(role, role.system)">{{
                        role.system ? 'Şablondan Oluştur' : 'İzinleri Düzenle'
                      }}</UiButton
                      ><UiButton
                        v-if="!role.system"
                        class="btn small danger"
                        @click="deleteRole = role"
                        >Sil</UiButton
                      >
                    </div>
                  </td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
        <section v-else class="team-card">
          <h2>Ekip Yönetimi Aktivitesi</h2>
          <p class="team-hint">Kullanıcı, davet ve rol değişikliklerinin son 100 kaydı.</p>
          <UiTable label="Ekip aktivitesi"
            ><table class="team-table">
              <thead>
                <tr>
                  <th>Tarih</th>
                  <th>İşlem Yapan</th>
                  <th>İşlem</th>
                  <th>Hedef</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="activity in data.activities" :key="activity.id">
                  <td>{{ dateTime(activity.created_at) }}</td>
                  <td>{{ activity.actor }}</td>
                  <td>{{ activity.action }}</td>
                  <td>{{ activity.target }}</td>
                </tr>
                <tr v-if="!data.activities.length">
                  <td colspan="4">Henüz ekip yönetimi işlemi kaydedilmedi.</td>
                </tr>
              </tbody>
            </table></UiTable
          >
        </section>
      </template>
      <UiModal v-if="createOpen" class="team-modal" :busy="busy" @close="createOpen = false"
        ><section class="team-dialog">
          <header class="team-detail-header">
            <h2>Yeni Kullanıcı</h2>
            <UiButton
              class="btn small"
              :disabled="busy"
              aria-label="Kapat"
              @click="createOpen = false"
              >×</UiButton
            >
          </header>
          <form @submit.prevent="createUser">
            <div class="team-form-grid">
              <UiField>Ad Soyad<input v-model="create.name" required maxlength="100" /></UiField
              ><UiField
                >E-posta<input
                  v-model="create.email"
                  required
                  type="email"
                  maxlength="200" /></UiField
              ><UiField>Departman<input v-model="create.department" maxlength="100" /></UiField
              ><UiField
                >Rol<select aria-label="Rol" v-model="create.role" required>
                  <option v-for="role in data.roles" :key="role.key" :value="role.key">
                    {{ roleName(role) }}
                  </option>
                </select></UiField
              ><UiField v-if="!supplier"
                >Tahsis Edilen Araç<select
                  v-model="create.assigned_plate"
                  aria-label="Tahsis Edilen Araç"
                >
                  <option value="">Araç seçilmedi</option>
                  <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.plate">
                    {{ vehicle.plate }}
                  </option>
                </select></UiField
              >
            </div>
            <label class="team-check"
              ><input v-model="create.invite" type="checkbox" /> E-posta ile davet gönder</label
            >
            <p class="team-hint">
              Kullanıcı şifresini davet bağlantısından kendisi oluşturur. Daveti şimdi göndermeden
              kullanıcı kaydı da açabilirsiniz.
            </p>
            <UiAlert v-if="mutationError" tone="error">{{ mutationError }}</UiAlert>
            <footer class="team-actions detail-actions">
              <UiButton type="button" class="btn" :disabled="busy" @click="createOpen = false"
                >Vazgeç</UiButton
              ><UiButton class="btn btn-blue" :disabled="busy">{{
                busy ? 'Kaydediliyor…' : 'Kullanıcıyı Ekle'
              }}</UiButton>
            </footer>
          </form>
        </section></UiModal
      >
      <UiModal v-if="roleEdit" class="team-modal" :busy="busy" @close="roleEdit = null"
        ><section class="team-dialog wide">
          <header class="team-detail-header">
            <h2>{{ roleEdit.key ? 'Rol İzinlerini Düzenle' : 'Yeni Rol Şablonu' }}</h2>
            <UiButton class="btn small" :disabled="busy" aria-label="Kapat" @click="roleEdit = null"
              >×</UiButton
            >
          </header>
          <form @submit.prevent="saveRole">
            <div class="team-form-grid">
              <UiField>Rol Adı<input v-model="roleEdit.name" required maxlength="80" /></UiField
              ><UiField
                >Temel Rol<select
                  aria-label="Temel Rol"
                  :value="roleEdit.base_role"
                  :disabled="!!roleEdit.key"
                  @change="changeBaseRole($event.target.value)"
                >
                  <option v-for="role in systemRoles" :key="role.key" :value="role.key">
                    {{ roleName(role) }}
                  </option>
                </select></UiField
              ><UiField class="span-two"
                >Açıklama<input v-model="roleEdit.description" maxlength="300"
              /></UiField>
            </div>
            <PermissionMatrix
              v-model="roleEdit.permissions"
              :modules="data.modules"
              :actions="data.actions"
              :ceiling="roleCeiling"
            /><UiAlert v-if="mutationError" tone="error">{{ mutationError }}</UiAlert>
            <footer class="team-actions detail-actions">
              <UiButton class="btn btn-blue" :disabled="busy">Rolü Kaydet</UiButton>
            </footer>
          </form>
        </section></UiModal
      >
      <UiModal v-if="invitation" class="team-modal" @close="invitation = null"
        ><section class="team-dialog">
          <h2>Kullanıcı Daveti</h2>
          <UiAlert :tone="invitation.email_sent ? 'success' : 'info'">{{
            invitation.message
          }}</UiAlert
          ><UiField
            >Davet Bağlantısı<input
              :value="invitation.invitation_url"
              readonly
              @focus="$event.target.select()"
          /></UiField>
          <p class="team-hint">
            Bağlantı 48 saat geçerlidir ve bir kez kullanılabilir. Yeni davet gönderildiğinde önceki
            bağlantı iptal edilir.
          </p>
          <footer class="team-actions detail-actions">
            <UiButton class="btn" @click="copyInvitation">Bağlantıyı Kopyala</UiButton
            ><UiButton class="btn btn-blue" @click="invitation = null">Kapat</UiButton>
          </footer>
        </section></UiModal
      >
      <UiModal v-if="deleteRole" class="team-modal" :busy="busy" @close="deleteRole = null"
        ><section class="team-dialog">
          <h2>Rol şablonunu sil</h2>
          <p>{{ deleteRole.name }} şablonu silinecek. Kullanıcıya atanmış roller silinemez.</p>
          <UiAlert v-if="mutationError" tone="error">{{ mutationError }}</UiAlert>
          <footer class="team-actions detail-actions">
            <UiButton class="btn" :disabled="busy" @click="deleteRole = null">Vazgeç</UiButton
            ><UiButton class="btn danger" :disabled="busy" @click="removeRole">Rolü Sil</UiButton>
          </footer>
        </section></UiModal
      >
    </main>
  </div>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import PermissionMatrix from '../components/PermissionMatrix.vue'
import { UiAlert, UiButton, UiField, UiModal, UiTable } from '../components/ui/index.js'
import { apiRequest } from '../api/http.js'
const route = useRoute(),
  supplier = computed(() => route.path.startsWith('/supplier-portal'))
const portal = computed(() => (supplier.value ? 'supplier' : 'customer'))
const api = (path, options = {}) =>
  apiRequest(`/api/team/${portal.value}${path}`, { ...options, account: portal.value })
const data = ref(null),
  vehicles = ref([]),
  loading = ref(true),
  busy = ref(false),
  error = ref(''),
  mutationError = ref(''),
  notice = ref('')
const tab = ref('users'),
  search = ref(''),
  roleFilter = ref(''),
  statusFilter = ref(''),
  page = ref(1)
const selectedId = ref(null),
  edit = ref(null),
  createOpen = ref(false),
  create = ref({}),
  roleEdit = ref(null),
  invitation = ref(null),
  deleteRole = ref(null)
const tabs = [
  { id: 'users', label: 'Kullanıcılar' },
  { id: 'roles', label: 'Roller & İzinler' },
  { id: 'activity', label: 'Aktivite' },
]
const labels = {
  fleet_manager: 'Filo Yöneticisi',
  operations: 'Operasyon',
  finance: 'Finans',
  sales: 'Satış',
  delivery: 'Teslim & İade',
  viewer: 'Görüntüleyici',
}
const roleName = (role) => (role ? labels[role.name] || role.name : '')
const initials = (name) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toLocaleUpperCase('tr-TR')
const dateTime = (value) => new Date(value).toLocaleString('tr-TR')
const systemRoles = computed(() => data.value?.roles.filter((role) => role.system) || [])
const stats = computed(() => [
  { label: 'Toplam Ekip Üyesi', count: data.value.users.length },
  {
    label: 'Aktif Kullanıcı',
    count: data.value.users.filter((user) => user.status === 'Aktif').length,
  },
  {
    label: 'Bekleyen Davet / Kayıt',
    count: data.value.users.filter((user) => user.status.startsWith('Davet')).length,
  },
  { label: 'Pasif Kullanıcı', count: data.value.users.filter((user) => !user.is_active).length },
  { label: 'Rol Şablonu', count: data.value.roles.length },
])
const filteredUsers = computed(() =>
  (data.value?.users || []).filter(
    (user) =>
      (!search.value ||
        `${user.name} ${user.email} ${user.department}`
          .toLocaleLowerCase('tr-TR')
          .includes(search.value.toLocaleLowerCase('tr-TR'))) &&
      (!roleFilter.value || user.role === roleFilter.value) &&
      (!statusFilter.value || user.status === statusFilter.value),
  ),
)
const pageCount = computed(() => Math.max(1, Math.ceil(filteredUsers.value.length / 10)))
const pageUsers = computed(() => filteredUsers.value.slice((page.value - 1) * 10, page.value * 10))
const selectedUser = computed(() => data.value?.users.find((user) => user.id === selectedId.value))
const userCeiling = computed(
  () =>
    systemRoles.value.find(
      (role) =>
        role.key === data.value?.roles.find((item) => item.key === edit.value?.role)?.base_role,
    )?.permissions || {},
)
const roleCeiling = computed(
  () => systemRoles.value.find((role) => role.key === roleEdit.value?.base_role)?.permissions || {},
)
watch([search, roleFilter, statusFilter], () => {
  page.value = 1
})
watch(pageCount, (count) => {
  page.value = Math.min(page.value, count)
})
let loadGeneration = 0
watch(portal, () => {
  data.value = null
  selectedId.value = null
  edit.value = null
  roleEdit.value = null
  createOpen.value = false
  invitation.value = null
  deleteRole.value = null
  vehicles.value = []
  search.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  tab.value = 'users'
  load()
})
async function load() {
  const generation = ++loadGeneration
  const account = portal.value
  loading.value = true
  error.value = ''
  try {
    const overview = await api('/overview')
    if (generation !== loadGeneration || account !== portal.value) return
    data.value = overview
    if (account === 'customer') {
      const cars = await apiRequest('/api/vehicles', { account: 'customer' })
      if (generation !== loadGeneration || account !== portal.value) return
      vehicles.value = cars
    }
    if (selectedId.value) {
      const user = data.value.users.find((item) => item.id === selectedId.value)
      if (user) selectUser(user)
    }
  } catch (failure) {
    if (generation === loadGeneration) error.value = failure.message
  } finally {
    if (generation === loadGeneration) loading.value = false
  }
}
function selectUser(user) {
  selectedId.value = user.id
  edit.value = JSON.parse(JSON.stringify(user))
  error.value = ''
  notice.value = ''
}
function memberBody(user) {
  const body = Object.fromEntries(
    [
      'name',
      'email',
      'phone',
      'role',
      'department',
      'assigned_plate',
      'is_active',
      'permissions',
      'version',
      'invite',
    ]
      .filter((key) => user[key] !== undefined)
      .map((key) => [key, user[key]]),
  )
  if (user.role?.startsWith('custom:') && !user.custom_permissions) body.permissions = null
  return body
}
async function mutate(action) {
  busy.value = true
  mutationError.value = ''
  error.value = ''
  notice.value = ''
  try {
    await action()
  } catch (failure) {
    mutationError.value = failure.message
    error.value = failure.message
  } finally {
    busy.value = false
  }
}
function newUser() {
  mutationError.value = ''
  create.value = {
    name: '',
    email: '',
    department: '',
    role: supplier.value ? 'viewer' : 'Görüntüleyici',
    assigned_plate: '',
    invite: true,
  }
  createOpen.value = true
}
async function createUser() {
  await mutate(async () => {
    const result = await api('/users', { method: 'POST', body: memberBody(create.value) })
    selectedId.value = result.user.id
    createOpen.value = false
    await load()
    notice.value = 'Kullanıcı kaydı oluşturuldu.'
    if (result.invitation_url) invitation.value = result
  })
}
async function saveUser() {
  await mutate(async () => {
    await api(`/users/${selectedId.value}`, { method: 'PUT', body: memberBody(edit.value) })
    await load()
    notice.value = 'Kullanıcı ve izinleri kaydedildi. Kullanıcının açık oturumları kapatıldı.'
  })
}
function changeUserRole(key) {
  edit.value.role = key
  edit.value.custom_permissions = false
  edit.value.permissions = JSON.parse(
    JSON.stringify(data.value.roles.find((role) => role.key === key).permissions),
  )
}
async function invite(uid) {
  await mutate(async () => {
    invitation.value = await api(`/users/${uid}/invite`, { method: 'POST' })
    await load()
  })
}
async function revokeInvite(uid) {
  await mutate(async () => {
    await api(`/users/${uid}/revoke-invitation`, { method: 'POST' })
    await load()
    notice.value = 'Davet iptal edildi.'
  })
}
async function copyInvitation() {
  try {
    await navigator.clipboard.writeText(invitation.value.invitation_url)
    notice.value = 'Davet bağlantısı kopyalandı.'
  } catch {
    notice.value = 'Bağlantıyı seçip kopyalayabilirsiniz.'
  }
}
function openRole(role, copy = false) {
  mutationError.value = ''
  roleEdit.value = JSON.parse(JSON.stringify(role))
  if (copy) {
    roleEdit.value.key = null
    roleEdit.value.name = roleName(role) + ' Özel'
    roleEdit.value.version = 0
  }
}
function newRole() {
  openRole(
    systemRoles.value.find((role) => role.key === (supplier.value ? 'viewer' : 'Görüntüleyici')),
    true,
  )
}
function changeBaseRole(key) {
  roleEdit.value.base_role = key
  roleEdit.value.permissions = JSON.parse(
    JSON.stringify(systemRoles.value.find((role) => role.key === key).permissions),
  )
}
async function saveRole() {
  await mutate(async () => {
    const role = roleEdit.value
    await api(role.key ? `/roles/${role.key.replace('custom:', '')}` : '/roles', {
      method: role.key ? 'PUT' : 'POST',
      body: {
        name: role.name,
        description: role.description,
        base_role: role.base_role,
        permissions: role.permissions,
        version: role.version,
      },
    })
    roleEdit.value = null
    await load()
    notice.value = 'Rol şablonu kaydedildi.'
    tab.value = 'roles'
  })
}
async function removeRole() {
  await mutate(async () => {
    await api(`/roles/${deleteRole.value.key.replace('custom:', '')}`, { method: 'DELETE' })
    deleteRole.value = null
    await load()
    notice.value = 'Rol şablonu silindi.'
  })
}
onMounted(load)
</script>
<style scoped>
.team-page {
  min-width: 0;
  color: #112b4e;
}
.team-heading,
.team-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 22px;
}
.team-heading h1 {
  margin: 7px 0;
  font-size: 28px;
}
.team-heading p {
  color: #72839a;
  margin: 0;
}
.eyebrow {
  color: #0064ff;
  font-size: 11px;
  letter-spacing: 1.2px;
  font-weight: 700;
}
.team-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.team-stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin: 24px 0;
}
.team-stats article,
.team-card {
  background: white;
  border: 1px solid #e4edf8;
  border-radius: 12px;
  box-shadow: 0 4px 14px #16396105;
}
.team-stats article {
  display: grid;
  gap: 10px;
  padding: 20px;
}
.team-stats span {
  color: #6b7e98;
  font-size: 12px;
}
.team-stats strong {
  color: #005bdf;
  font-size: 28px;
}
.team-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid #e1e9f4;
  margin: 12px 0 20px;
}
.team-tabs button {
  border: 0;
  border-bottom: 3px solid transparent;
  background: transparent;
  padding: 12px 16px;
  color: #72839a;
  font: inherit;
  cursor: pointer;
}
.team-tabs .current {
  color: #0064ff;
  border-color: #0064ff;
  font-weight: 700;
}
.team-columns {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) minmax(550px, 1.15fr);
  gap: 20px;
  align-items: start;
}
.team-card {
  padding: 20px;
  min-width: 0;
}
.team-card h2 {
  font-size: 18px;
  margin: 0;
}
.team-card h3 {
  font-size: 15px;
  margin: 24px 0 8px;
}
.team-filters {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) 130px 145px;
  gap: 10px;
  margin-bottom: 18px;
}
.team-page :deep(label:not(.team-check)) {
  display: grid;
  gap: 6px;
  min-width: 0;
  font-size: 12px;
}
.team-page :deep(input:not([type='checkbox'])),
.team-page :deep(select) {
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d8e2f0;
  border-radius: 7px;
  padding: 11px;
  background: white;
  color: #173153;
  font: inherit;
}
.team-page :deep(input:focus),
.team-page :deep(select:focus) {
  outline: 2px solid #b3d2ff;
  outline-offset: 1px;
}
.team-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
}
.team-table th {
  background: #f7faff;
  color: #71849e;
  font-size: 11px;
}
.team-table td,
.team-table th {
  padding: 13px 9px;
  border-bottom: 1px solid #eaf0f7;
}
.team-table small,
.user-identity small {
  display: block;
  color: #7f90a8;
  font-size: 11px;
  margin-top: 5px;
  overflow-wrap: anywhere;
}
.team-table .selected {
  background: #f1f7ff;
}
.user-identity {
  display: flex;
  align-items: center;
  gap: 10px;
}
.team-avatar {
  background: linear-gradient(135deg, #00a7ae, #0064ff);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.role-badge,
.status-badge {
  display: inline-block;
  font-size: 10px;
  border-radius: 6px;
  padding: 6px 8px;
  line-height: 1.4;
  background: #f1f4f9;
  color: #687b94;
}
.role-badge {
  color: #1260bd;
  background: #eaf3ff;
}
.status-badge.active {
  color: #168358;
  background: #e4f8ee;
}
.team-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #71849e;
  padding-top: 16px;
}
.team-pagination > div {
  display: flex;
  align-items: center;
  gap: 12px;
}
.team-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px;
}
.span-two {
  grid-column: 1/-1;
}
.team-hint {
  font-size: 12px;
  color: #72839a;
  line-height: 1.7;
}
.team-empty {
  padding: 80px 25px;
  text-align: center;
}
.team-empty > span {
  font-size: 36px;
  color: #0064ff;
}
.team-empty p {
  color: #8b99ae;
  font-size: 13px;
  line-height: 1.7;
}
.detail-actions {
  justify-content: flex-end;
  margin-top: 22px;
}
.team-modal {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #07182c88;
}
.team-dialog {
  background: white;
  border-radius: 14px;
  width: min(600px, 100%);
  padding: 26px;
  max-height: 90vh;
  overflow: auto;
}
.team-dialog.wide {
  width: min(850px, 100%);
}
.team-dialog h2 {
  margin: 0 0 18px;
  font-size: 20px;
}
.team-dialog :deep(label:not(.team-check)) {
  margin-bottom: 12px;
}
.team-check {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
}
.small {
  padding: 7px 10px;
  font-size: 11px;
}
.danger {
  color: #c33838;
  border-color: #f0cece;
}
.team-dialog .team-actions {
  margin-top: 20px;
}
@media (max-width: 1250px) {
  .team-columns {
    grid-template-columns: 1fr;
  }
  .user-list .team-filters {
    grid-template-columns: 1fr 180px 180px;
  }
}
@media (max-width: 800px) {
  .team-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .team-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .team-columns {
    grid-template-columns: minmax(0, 1fr);
  }
  .user-list .team-filters,
  .team-form-grid {
    grid-template-columns: 1fr;
  }
  .team-card {
    padding: 14px;
  }
  .team-table {
    min-width: 550px;
  }
  .team-modal {
    padding: 12px;
  }
  .team-dialog {
    padding: 18px;
  }
  .team-stats article {
    padding: 14px;
  }
  .team-heading h1 {
    font-size: 24px;
  }
}
</style>
