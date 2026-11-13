<template>
  <div :class="portal === 'service' ? 'nt-standalone' : 'portal-layout fleet-dashboard'">
    <Sidebar v-if="portal !== 'service'" :supplier="portal === 'supplier'" />
    <main :class="portal === 'service' ? 'nt-main nt-service' : 'portal-main nt-main'">
      <router-link v-if="portal === 'service'" to="/service-portal" class="nt-back"
        ><NavIcon name="arrow-left" size="16" />Servis portalı</router-link
      >
      <PageHeader
        title="Bildirimler"
        icon="bell"
        description="Hesabınızla ilgili gelişmeler. Hangi konularda uygulamada ve e-postayla haber alacağınızı Ayarlar sekmesinden seçin."
      >
        <template #actions>
          <UiButton
            v-if="tab === 'list' && unread"
            class="nt-btn ghost"
            :disabled="busy"
            @click="markAll"
            ><NavIcon name="check" size="16" />Tümünü okundu say</UiButton
          >
        </template>
      </PageHeader>

      <div class="nt-tabs" role="tablist" aria-label="Bildirim bölümleri">
        <button
          type="button"
          role="tab"
          class="nt-tab"
          :aria-selected="tab === 'list'"
          @click="setTab('list')"
        >
          Bildirimler <span v-if="unread">{{ unread }}</span>
        </button>
        <button
          type="button"
          role="tab"
          class="nt-tab"
          :aria-selected="tab === 'settings'"
          @click="setTab('settings')"
        >
          Ayarlar
        </button>
      </div>

      <UiAlert v-if="error" as="p" tone="error">{{ error }}</UiAlert>

      <!-- List -->
      <section v-if="tab === 'list'" class="nt-panel">
        <div class="nt-toolbar">
          <div class="nt-chips" role="group" aria-label="Konu">
            <button type="button" class="nt-chip" :aria-pressed="group === ''" @click="group = ''">
              Tümü
            </button>
            <button
              v-for="g in groups"
              :key="g.key"
              type="button"
              class="nt-chip"
              :aria-pressed="group === g.key"
              @click="group = g.key"
            >
              {{ g.label }}
            </button>
          </div>
          <label class="nt-check"
            ><input v-model="unreadOnly" type="checkbox" />Yalnızca okunmamışlar</label
          >
        </div>
        <p v-if="loading" class="nt-muted">Yükleniyor…</p>
        <EmptyState
          v-else-if="!shown.length"
          icon="bell"
          :title="items.length ? 'Bu filtrede bildirim yok' : 'Henüz bildirim yok'"
          :text="
            items.length
              ? 'Filtreyi değiştirmeyi deneyin.'
              : 'Teklif, teslimat, servis, hasar ve hatırlatma bildirimleri burada listelenecek.'
          "
        />
        <ul v-else class="nt-list">
          <li v-for="item in shown" :key="item.id" :class="{ unread: !item.read }">
            <span class="nt-dot" aria-hidden="true"></span>
            <div class="nt-text">
              <strong>{{ item.title }}</strong>
              <p v-if="item.body">{{ item.body }}</p>
              <small
                >{{ item.group_label }} · {{ timeAgo(item.created_at)
                }}<template v-if="item.email_status === 'sent'">
                  · e-posta gönderildi</template
                ></small
              >
            </div>
            <div class="nt-item-actions">
              <router-link
                v-if="item.link"
                :to="item.link"
                class="nt-btn sm"
                @click="markRead(item)"
                >Aç</router-link
              >
              <button
                v-if="!item.read"
                type="button"
                class="nt-btn sm ghost"
                :aria-label="`${item.title} okundu say`"
                @click="markRead(item)"
              >
                Okundu
              </button>
            </div>
          </li>
        </ul>
      </section>

      <!-- Settings -->
      <section v-else class="nt-panel">
        <p v-if="!prefs" class="nt-muted">Yükleniyor…</p>
        <template v-else>
          <div class="nt-mailbox">
            <NavIcon name="mail" size="18" />
            <p v-if="prefs.email">
              E-posta bildirimleri <strong>{{ prefs.email }}</strong> adresine gönderilir.
            </p>
            <p v-else>Hesabınızda e-posta adresi yok; bildirimler yalnızca uygulamada görünür.</p>
          </div>
          <UiAlert v-if="!prefs.email_configured" as="p" tone="info"
            >E-posta gönderimi sunucuda henüz yapılandırılmamış. Bildirimler uygulamada görünmeye
            devam eder.</UiAlert
          >
          <UiAlert v-if="!prefs.can_edit" as="p" tone="info"
            >Bildirim ayarlarını hesap sahibi veya filo yöneticisi değiştirebilir.</UiAlert
          >
          <table class="nt-prefs">
            <thead>
              <tr>
                <th>Konu</th>
                <th>Uygulamada</th>
                <th>E-posta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in draft" :key="g.key">
                <td>
                  <strong>{{ g.label }}</strong>
                  <p>{{ g.description }}</p>
                  <ul class="nt-topics">
                    <li v-for="t in g.topics" :key="t">{{ t }}</li>
                  </ul>
                </td>
                <td>
                  <label class="nt-switch">
                    <input
                      v-model="g.in_app"
                      type="checkbox"
                      role="switch"
                      :disabled="!prefs.can_edit"
                      :aria-label="`${g.label}: uygulamada göster`"
                    /><span aria-hidden="true"></span>
                  </label>
                </td>
                <td>
                  <label class="nt-switch">
                    <input
                      v-model="g.email"
                      type="checkbox"
                      role="switch"
                      :disabled="!prefs.can_edit"
                      :aria-label="`${g.label}: e-posta gönder`"
                    /><span aria-hidden="true"></span>
                  </label>
                </td>
              </tr>
            </tbody>
          </table>
          <footer v-if="prefs.can_edit" class="nt-save">
            <span>{{
              dirty ? 'Kaydedilmemiş değişiklik var.' : 'Tüm değişiklikler kayıtlı.'
            }}</span>
            <UiButton class="nt-btn" :disabled="!dirty || busy" @click="reset">Vazgeç</UiButton>
            <UiButton class="nt-btn primary" :disabled="!dirty || busy" @click="save">{{
              busy ? 'Kaydediliyor…' : 'Ayarları Kaydet'
            }}</UiButton>
          </footer>
        </template>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import NavIcon from '../components/NavIcon.vue'
import { EmptyState, PageHeader, UiAlert, UiButton } from '../components/ui/index.js'
import { notificationsApi, portalFromPath, timeAgo } from '../api/notifications.js'
import { notify } from '../utils/feedback.js'

const route = useRoute()
const router = useRouter()
const portal = computed(() => portalFromPath(route.path))
const api = computed(() => notificationsApi(portal.value))

const tab = computed(() => (route.query.tab === 'settings' ? 'settings' : 'list'))
const items = ref([]),
  unread = ref(0),
  prefs = ref(null),
  draft = ref([]),
  group = ref(''),
  unreadOnly = ref(false),
  loading = ref(true),
  busy = ref(false),
  error = ref('')

const groups = computed(() => prefs.value?.groups || [])
const shown = computed(() =>
  items.value.filter(
    (item) => (!group.value || item.group === group.value) && (!unreadOnly.value || !item.read),
  ),
)
const dirty = computed(() =>
  draft.value.some((g, i) => {
    const saved = prefs.value.groups[i]
    return g.in_app !== saved.in_app || g.email !== saved.email
  }),
)

function setTab(name) {
  router.replace({ query: name === 'settings' ? { tab: 'settings' } : {} })
}
function reset() {
  draft.value = (prefs.value?.groups || []).map((g) => ({ ...g }))
}
async function loadList() {
  loading.value = true
  try {
    const data = await api.value('?limit=100')
    items.value = data.items
    unread.value = data.unread
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
async function loadPrefs() {
  try {
    prefs.value = await api.value('/preferences')
    reset()
  } catch (e) {
    error.value = e.message
  }
}
async function markRead(item) {
  if (item.read) return
  item.read = true
  unread.value = Math.max(0, unread.value - 1)
  api.value(`/${item.id}/read`, { method: 'POST' }).catch(() => {})
}
async function markAll() {
  busy.value = true
  try {
    await api.value('/read-all', { method: 'POST' })
    items.value.forEach((item) => (item.read = true))
    unread.value = 0
  } catch (e) {
    notify(e.message, { tone: 'error' })
  } finally {
    busy.value = false
  }
}
async function save() {
  busy.value = true
  try {
    prefs.value = await api.value('/preferences', {
      method: 'PUT',
      body: { groups: draft.value.map(({ key, in_app, email }) => ({ key, in_app, email })) },
    })
    reset()
    notify('Bildirim ayarları kaydedildi.', { tone: 'success' })
    loadList()
  } catch (e) {
    notify(e.message, { tone: 'error' })
  } finally {
    busy.value = false
  }
}

watch(portal, () => {
  loadList()
  loadPrefs()
})
onMounted(() => {
  loadList()
  loadPrefs()
})
</script>

<style scoped>
.nt-standalone {
  min-height: 100vh;
  background: var(--fr-bg);
}
.nt-main {
  background: var(--fr-bg);
  color: var(--fr-text);
}
.nt-service {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px 20px 48px;
}
.nt-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  color: var(--fr-primary);
  font-size: var(--fr-text-sm);
  font-weight: 600;
  text-decoration: none;
}
.nt-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: var(--fr-space-4);
  border-bottom: 1px solid var(--fr-border);
}
.nt-tab {
  padding: 10px 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--fr-muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.nt-tab span {
  margin-left: 4px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--fr-primary);
  color: #fff;
  font-size: var(--fr-text-xs);
}
.nt-tab[aria-selected='true'] {
  border-bottom-color: var(--fr-primary);
  color: var(--fr-primary);
}
.nt-panel {
  padding: var(--fr-space-4);
  background: var(--fr-surface);
  border: 1px solid var(--fr-border);
  border-radius: var(--fr-radius-lg);
  box-shadow: var(--fr-shadow-sm);
}
.nt-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--fr-space-3);
  padding-bottom: var(--fr-space-3);
  border-bottom: 1px solid var(--fr-border);
}
.nt-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.nt-chip {
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
.nt-chip[aria-pressed='true'] {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
  font-weight: 600;
}
.nt-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fr-text-sm);
  color: var(--fr-text);
  cursor: pointer;
}
.nt-muted {
  margin: 0;
  padding: var(--fr-space-4) 0;
  color: var(--fr-muted);
}
.nt-list {
  margin: 0;
  padding: 0;
  list-style: none;
}
.nt-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 4px;
  border-bottom: 1px solid var(--fr-border);
}
.nt-list li:last-child {
  border-bottom: 0;
}
.nt-dot {
  width: 9px;
  height: 9px;
  margin-top: 6px;
  flex: none;
  border-radius: 50%;
}
.nt-list li.unread .nt-dot {
  background: var(--fr-primary);
}
.nt-text {
  flex: 1;
  min-width: 0;
}
.nt-text strong {
  color: var(--fr-ink);
  font-weight: 600;
}
.nt-list li:not(.unread) .nt-text strong {
  font-weight: 500;
}
.nt-text p {
  margin: 3px 0;
  font-size: var(--fr-text-sm);
  color: var(--fr-text);
  overflow-wrap: anywhere;
}
.nt-text small {
  font-size: var(--fr-text-xs);
  color: var(--fr-muted);
}
.nt-item-actions {
  display: flex;
  gap: 6px;
  flex: none;
}
.nt-btn {
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
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
}
.nt-btn:hover {
  border-color: var(--fr-primary);
  color: var(--fr-primary);
}
.nt-btn.primary {
  border-color: var(--fr-primary);
  background: var(--fr-primary);
  color: #fff;
}
.nt-btn.ghost {
  background: transparent;
}
.nt-btn.sm {
  min-height: 32px;
  padding: 0 10px;
  font-size: var(--fr-text-sm);
}
.nt-btn:disabled {
  opacity: 0.55;
  cursor: default;
}
.nt-mailbox {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: var(--fr-space-3);
  color: var(--fr-muted);
}
.nt-mailbox p {
  margin: 0;
  color: var(--fr-text);
}
.nt-prefs {
  width: 100%;
  margin-top: var(--fr-space-3);
  border-collapse: collapse;
}
.nt-prefs th {
  padding: 8px 12px;
  border-bottom: 1px solid var(--fr-border);
  font-size: var(--fr-text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: left;
  text-transform: uppercase;
  color: var(--fr-muted);
}
.nt-prefs th:not(:first-child),
.nt-prefs td:not(:first-child) {
  width: 110px;
  text-align: center;
}
.nt-prefs td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--fr-border);
  vertical-align: top;
}
.nt-prefs td strong {
  color: var(--fr-ink);
}
.nt-prefs td p {
  margin: 3px 0 8px;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
.nt-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.nt-topics li {
  padding: 2px 8px;
  border: 1px solid var(--fr-border);
  border-radius: 6px;
  font-size: var(--fr-text-xs);
  color: var(--fr-text);
}
.nt-switch {
  position: relative;
  display: inline-block;
  width: 42px;
  height: 24px;
  cursor: pointer;
}
.nt-switch input {
  position: absolute;
  inset: 0;
  width: 100% !important;
  height: 100% !important;
  margin: 0;
  opacity: 0;
  cursor: inherit;
}
.nt-switch span {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: var(--fr-border-strong);
  transition: background 0.15s ease;
  pointer-events: none;
}
.nt-switch span::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(16, 37, 76, 0.25);
  transition: transform 0.15s ease;
}
.nt-switch input:checked + span {
  background: var(--fr-primary);
}
.nt-switch input:checked + span::after {
  transform: translateX(18px);
}
.nt-switch input:focus-visible + span {
  outline: 2px solid var(--fr-focus);
  outline-offset: 2px;
}
.nt-switch input:disabled {
  cursor: default;
}
.nt-switch input:disabled + span {
  opacity: 0.5;
}
.nt-save {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin: 0 calc(-1 * var(--fr-space-4)) calc(-1 * var(--fr-space-4));
  padding: 12px var(--fr-space-4);
  border-top: 1px solid var(--fr-border);
  background: var(--fr-surface);
  border-radius: 0 0 var(--fr-radius-lg) var(--fr-radius-lg);
}
.nt-save span {
  margin-right: auto;
  font-size: var(--fr-text-sm);
  color: var(--fr-muted);
}
@media (max-width: 640px) {
  .nt-list li {
    flex-wrap: wrap;
  }
  .nt-item-actions {
    width: 100%;
    padding-left: 21px;
  }
  .nt-prefs th:not(:first-child),
  .nt-prefs td:not(:first-child) {
    width: 64px;
  }
  .nt-prefs th {
    font-size: 10px;
  }
}
</style>
