<template>
  <header class="mobile-navigation-bar">
    <router-link :to="supplier ? '/supplier-portal' : '/dashboard'" class="mobile-brand"
      ><img
        class="customer-logo customer-logo--mobile"
        src="/fleetrent-logo-dark.png"
        alt="FleetRent"
        width="140"
        height="36" /></router-link
    ><span class="mobile-page-name">{{ currentLabel }}</span
    ><UiButton
      ref="menuButton"
      class="mobile-menu-toggle"
      aria-controls="customer-menu"
      :aria-expanded="mobileOpen"
      :aria-label="supplier ? 'Tedarikçi menüsünü aç' : 'Müşteri menüsünü aç'"
      @click="mobileOpen = true"
      >☰</UiButton
    >
  </header>
  <div
    v-if="mobileOpen"
    class="mobile-navigation-backdrop"
    @click="closeMenu"
    aria-hidden="true"
  ></div>
  <aside
    id="customer-menu"
    ref="menuPanel"
    class="portal-sidebar customer-navigation"
    :class="{ 'mobile-open': mobileOpen, 'supplier-navigation': supplier }"
    :inert="isMobile && !mobileOpen"
    :role="isMobile ? 'dialog' : undefined"
    :aria-modal="isMobile && mobileOpen ? 'true' : undefined"
    :aria-label="supplier ? 'Tedarikçi menüsü' : 'Müşteri menüsü'"
  >
    <UiButton
      ref="closeButton"
      class="mobile-menu-close"
      aria-label="Menüyü kapat"
      @click="closeMenu"
      >×</UiButton
    >
    <router-link :to="supplier ? '/supplier-portal' : '/dashboard'" class="fleet-brand"
      ><img
        class="customer-logo"
        src="/fleetrent-logo-dark.png"
        alt="FleetRent"
        width="188"
        height="46"
    /></router-link>
    <nav :aria-label="supplier ? 'Tedarikçi menüsü' : 'Müşteri menüsü'">
      <ul class="fleet-menu">
        <li
          v-for="item in navigationEntries"
          :key="item.id || item.to || item.label"
          :class="{ 'fleet-menu-group': item.children, 'fleet-menu-heading-row': item.heading }"
        >
          <span v-if="item.heading" class="fleet-menu-heading">{{ item.heading }}</span>
          <template v-else-if="item.children">
            <UiButton
              type="button"
              class="fleet-nav-link fleet-group-toggle"
              :class="{
                'group-current': item.children.some(isSelected),
                'group-expanded': expandedGroup === item.id,
              }"
              :aria-expanded="expandedGroup === item.id"
              :aria-controls="`supplier-group-${item.id}`"
              @click="expandedGroup = expandedGroup === item.id ? null : item.id"
            >
              <NavIcon class="nav-glyph" :label="item.label" />
              <span>{{ item.label }}</span>
              <span class="group-chevron" aria-hidden="true">⌄</span>
            </UiButton>
            <ul
              v-show="expandedGroup === item.id"
              :id="`supplier-group-${item.id}`"
              class="fleet-submenu"
              :aria-label="item.label + ' alt menüleri'"
            >
              <li v-for="child in item.children" :key="child.to">
                <router-link
                  :to="child.to"
                  class="fleet-nav-link fleet-submenu-link"
                  :class="{ selected: isSelected(child) }"
                  :aria-current="isSelected(child) ? 'page' : undefined"
                >
                  <NavIcon class="nav-glyph" :label="child.label" size="18" />
                  {{ child.label }}
                </router-link>
              </li>
            </ul>
          </template>
          <router-link
            v-else-if="item.to"
            :to="item.to"
            class="fleet-nav-link"
            :class="{ selected: isSelected(item) }"
            :aria-current="isSelected(item) ? 'page' : undefined"
            ><NavIcon class="nav-glyph" :label="item.label" />{{ item.label }}</router-link
          >
          <UiButton
            v-else
            class="fleet-nav-link unavailable"
            :aria-label="item.label + ': Yakında'"
            aria-disabled="true"
            ><span class="unavailable-content"
              ><NavIcon class="nav-glyph" :label="item.label" /><span class="soon-label">{{
                item.label
              }}</span></span
            ><span class="coming-soon">Yakında</span></UiButton
          >
        </li>
      </ul>
    </nav>
    <div class="account-actions">
      <router-link v-if="!supplier" to="/profile">Profilim</router-link
      ><span v-else>Tedarikçi Portalı</span><UiButton @click="logout">Çıkış Yap</UiButton>
    </div>
  </aside>
</template>
<script setup>
defineOptions({ name: 'AppSidebar' })
import { UiButton } from './ui/index.js'
import NavIcon from './NavIcon.vue'

import { useRoute, useRouter } from 'vue-router'
import { supplierNavigation } from '../utils/supplierModules'
import { supplierNavigationGroups } from '../utils/supplierNavigation.js'
import { apiRequest } from '../api/http.js'
import { supplierApi } from '../utils/supplierApi'
import { clearSupplierSession } from '../api/partnerSession.js'
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
const props = defineProps({ supplier: Boolean })
const route = useRoute(),
  router = useRouter()
const expandedGroup = ref(null)
const mobileOpen = ref(false),
  isMobile = ref(false),
  menuButton = ref(null),
  menuPanel = ref(null),
  closeButton = ref(null)
let media,
  previousOverflow = ''
const customerItems = [
  { label: 'Ana Sayfa', icon: '⌂', to: '/dashboard' },
  {
    id: 'customer-fleet',
    label: 'Filo',
    children: [
      { label: 'Araçlar', to: '/dashboard/vehicles' },
      { label: 'Araç Takip', to: '/dashboard/reports?tab=location' },
      { label: 'Belgeler', to: '/dashboard/settings?tab=sirket_evraklari' },
    ],
  },
  {
    id: 'customer-service',
    label: 'Servis & Talepler',
    children: [
      { label: 'Talep & Teklifler', to: '/dashboard/quotes' },
      { label: 'Tedarikçi İşlemleri', to: '/dashboard/requests' },
      { label: 'Servis / Bakım', to: '/dashboard/service-management' },
      { label: 'Lastik Yönetimi', to: '/dashboard/tires' },
      { label: 'Hasar ve Kaza', to: '/dashboard/service-management?tab=damage' },
      { label: 'Yol Yardım', to: '/dashboard/roadside' },
      { label: 'İş Emirleri', to: '/dashboard/work-orders' },
    ],
  },
  { label: 'Yakıt ve Giderler', icon: '▥', to: '/dashboard/fuel' },
  {
    id: 'customer-reports',
    label: 'Raporlama',
    children: [
      { label: 'Raporlar', to: '/dashboard/reports' },
      { label: 'Filo Kontrol & Tasarruf', to: '/dashboard/savings' },
    ],
  },
  {
    id: 'customer-admin',
    label: 'Yönetim',
    children: [
      { label: 'Kullanıcılar ve Yetkiler', to: '/dashboard/users' },
      { label: 'Ayarlar', to: '/dashboard/settings' },
    ],
  },
  // Not built yet: listed under "Yakında".
  { label: 'Sözleşmeler' },
  { label: 'Faturalar' },
  { label: 'HGS & Cezalar' },
  { label: 'Şoförlü Araçlar' },
  { label: 'Bildirimler' },
]
const customerLinks = customerItems.flatMap((item) => item.children || [item])
const items = computed(() => (props.supplier ? supplierNavigation : customerLinks))
const accessPermissions = ref(null),
  canManageTeam = ref(true)
const moduleForLink = (item) => {
  const path = item.to?.split('?')[0].split('/').at(-1)
  return {
    vehicles: 'vehicles',
    offers: 'offers',
    quotes: 'offers',
    contracts: 'contracts',
    operations: 'operations',
    branches: 'operations',
    reservations: 'operations',
    rentals: 'operations',
    deliveries: 'operations',
    returns: 'operations',
    maintenance: 'service',
    service: 'service',
    'service-management': 'service',
    'work-orders': 'service',
    roadside: 'service',
    tire: 'tires',
    tires: 'tires',
    damage: 'damage',
    policies: 'policies',
    hgs: 'tolls',
    fines: 'tolls',
    fuel: 'fuel',
    invoices: 'invoices',
    accounting: 'invoices',
    reports: 'reports',
    savings: 'reports',
    planning: 'planning',
    customers: 'customers',
    settings: 'settings',
    sales: 'vehicles',
  }[path]
}
const visibleLink = (item) => {
  if (item.to?.split('?')[0].endsWith('/users')) return canManageTeam.value
  const module = moduleForLink(item)
  return !accessPermissions.value || !module || accessPermissions.value[module]?.view
}
const navigationEntries = computed(() => {
  const source = props.supplier ? supplierNavigationGroups : customerItems
  const visible = source
    .map((item) =>
      item.children ? { ...item, children: item.children.filter(visibleLink) } : item,
    )
    .filter((item) => (item.children ? item.children.length : visibleLink(item)))
  // Not-yet-available items go last under a "Yakında" heading so the working menu stays together.
  const ready = visible.filter((item) => item.children || item.to)
  const soon = visible.filter((item) => !item.children && !item.to)
  return soon.length ? [...ready, { id: 'soon-heading', heading: 'Yakında' }, ...soon] : ready
})
const isSelected = (item) => {
  if (props.supplier) {
    const [path, query] = item.to.split('?')
    if (query)
      return route.path === path && route.query.tab === new URLSearchParams(query).get('tab')
    return path === '/supplier-portal' ? route.path === path : route.path.startsWith(path)
  }
  const [path, query] = item.to.split('?')
  if (query) return route.path === path && route.query.tab === new URLSearchParams(query).get('tab')
  return (
    (path === '/dashboard' ? route.path === path : route.path.startsWith(path)) &&
    !items.value.some(
      (other) =>
        other.to?.includes('?') &&
        other.to.split('?')[0] === route.path &&
        route.query.tab === new URLSearchParams(other.to.split('?')[1]).get('tab'),
    )
  )
}
const currentLabel = computed(
  () =>
    items.value.find((item) => item.to && isSelected(item))?.label ||
    (props.supplier ? 'Tedarikçi Portalı' : 'Müşteri Portalı'),
)
watch(
  () => [props.supplier, route.fullPath],
  () => {
    const source = props.supplier ? supplierNavigationGroups : customerItems
    expandedGroup.value = source.find((group) => group.children?.some(isSelected))?.id || null
  },
  { immediate: true },
)
function closeMenu() {
  mobileOpen.value = false
  nextTick(() => menuButton.value?.focus())
}
function handleMenuKey(event) {
  if (!isMobile.value || !mobileOpen.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeMenu()
  }
  if (event.key === 'Tab') {
    const focusable = [...menuPanel.value.querySelectorAll('a,button')].filter(
      (el) => el.getClientRects().length,
    )
    const first = focusable[0],
      last = focusable.at(-1)
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last?.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first?.focus()
    }
  }
}
function syncMobile() {
  isMobile.value = media.matches
  if (!media.matches) mobileOpen.value = false
}
watch(mobileOpen, async (open) => {
  if (open) {
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    await nextTick()
    closeButton.value?.focus()
  } else document.body.style.overflow = previousOverflow
})
watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)
async function loadAccess() {
  const supplierPortal = props.supplier
  try {
    const access = await apiRequest(
      `/api/team/${props.supplier ? 'supplier' : 'customer'}/session`,
      { account: props.supplier ? 'supplier' : 'customer' },
    )
    if (supplierPortal !== props.supplier) return
    accessPermissions.value = access.permissions
    canManageTeam.value = access.can_manage
  } catch {
    /* Existing authentication flows handle expired sessions. */
  }
}
watch(
  () => props.supplier,
  () => {
    accessPermissions.value = null
    canManageTeam.value = false
    loadAccess()
  },
)
onMounted(() => {
  loadAccess()
  media = window.matchMedia('(max-width:900px)')
  syncMobile()
  media.addEventListener('change', syncMobile)
  document.addEventListener('keydown', handleMenuKey)
})
onUnmounted(() => {
  document.removeEventListener('keydown', handleMenuKey)
  media?.removeEventListener('change', syncMobile)
  if (mobileOpen.value) document.body.style.overflow = previousOverflow
})
const logout = async () => {
  if (props.supplier) {
    try {
      await supplierApi('/logout', { method: 'POST' })
    } catch {
      // An expired or unavailable server session must not prevent local logout.
    }
    clearSupplierSession()
    router.push('/supplier-login')
    return
  }
  try {
    await fetch('/api/auth/logout', { method: 'POST' })
  } catch {
    // An expired or unavailable server session must not prevent local logout.
  }
  for (const key of [
    'fleetcar_token',
    'fleetcar_customer_id',
    'fleetcar_customer_name',
    'fleetcar_user_email',
    'fleetcar_user_verified',
    'fleet_customer',
    'customer_id',
  ])
    localStorage.removeItem(key)
  router.push('/login?role=customer')
}
</script>
<style scoped>
.supplier-navigation .fleet-nav-link {
  font-size: 12px;
  min-height: 32px;
  height: 32px !important;
}
.supplier-navigation .fleet-menu {
  gap: 2px;
}
.fleet-menu-group {
  border-radius: 7px;
}
.fleet-menu-group:has(.group-expanded) {
  background: #082333;
}
.fleet-group-toggle.group-current,
.fleet-group-toggle.group-expanded {
  background: #10334d;
  color: white;
}
.group-chevron {
  margin-left: auto;
  transition: transform 0.15s ease;
}
.group-expanded .group-chevron {
  transform: rotate(180deg);
}
.fleet-submenu {
  display: grid;
  gap: 2px;
  list-style: none;
  margin: 0;
  padding: 5px 6px 7px 14px;
}
.supplier-navigation .fleet-submenu-link {
  padding-left: 12px;
  gap: 9px;
}
.fleet-submenu-link .nav-glyph {
  width: 18px;
  height: 18px;
}
.fleet-nav-link:focus-visible {
  outline: 2px solid #8cbcff;
  outline-offset: -2px;
}
@media (prefers-reduced-motion: reduce) {
  .group-chevron {
    transition: none;
  }
}
.fleet-brand {
  display: flex;
  align-items: center;
  text-decoration: none;
  padding: 0 8px 16px;
}
.customer-logo {
  display: block;
  width: 188px;
  max-width: 100%;
  height: 46px;
  object-fit: cover;
  object-position: center;
  background: #0b2a4a;
  border-radius: 8px;
}
.fleet-menu {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 3px;
}
.fleet-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 0;
  border-radius: 5px;
  color: #d4e1ec;
  background: transparent;
  width: 100%;
  text-align: left;
  text-decoration: none;
  font: inherit;
  font-size: 13px;
  min-height: 38px;
  position: relative;
  cursor: pointer;
}
.fleet-nav-link:hover {
  background: #112f43;
  color: white;
}
.fleet-nav-link.selected {
  background: #0064ff;
  color: white;
  box-shadow: 0 4px 14px #0064ff30;
}
.nav-glyph {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}
.unavailable {
  cursor: default;
}
.unavailable {
  justify-content: space-between;
}
.unavailable-content {
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;
  opacity: 0.6;
}
.soon-label {
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.coming-soon {
  flex-shrink: 0;
  margin-left: 8px;
  padding: 1px 6px;
  border-radius: 10px;
  background: #163047;
  color: #a9c1d6;
  font-size: 11px;
  font-weight: 600;
}
.fleet-menu-heading {
  display: block;
  margin: 8px 0 2px;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #7f9bb3;
}
.fleet-support {
  margin-top: auto;
  border: 1px solid #163047;
  padding: 12px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: white;
}
.fleet-support p {
  margin: 6px 0 12px;
  color: #afc2d3;
}
.support-action {
  display: block;
  text-align: center;
  padding: 10px 5px;
  background: #0064ff;
  color: white;
  border-radius: 4px;
  text-decoration: none;
}
.account-actions {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  padding: 10px 8px;
}
.account-actions a,
.account-actions button {
  color: #afc2d3;
  background: none;
  border: 0;
  text-decoration: none;
  cursor: pointer;
}
nav {
  overflow-y: auto;
  min-height: 0;
  scrollbar-width: thin;
  flex: 1;
}
.mobile-navigation-bar,
.mobile-menu-close,
.mobile-navigation-backdrop {
  display: none;
}
@media (max-width: 900px) {
  .supplier-navigation .fleet-nav-link {
    min-height: 44px;
    height: auto !important;
  }
  .mobile-navigation-bar {
    display: flex;
    position: sticky;
    top: 0;
    z-index: 100;
    height: 60px;
    min-height: 60px;
    width: 100%;
    box-sizing: border-box;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: #031826;
    color: white;
  }
  .mobile-brand {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    text-decoration: none;
  }
  .customer-logo--mobile {
    width: 140px;
    height: 36px;
  }
  .mobile-page-name {
    flex: 1;
    font-size: 12px;
    text-align: right;
    color: #c7d8e6;
  }
  .mobile-menu-toggle,
  .mobile-menu-close {
    width: 44px;
    height: 44px;
    min-width: 44px;
    border: 1px solid #244055;
    border-radius: 8px;
    background: #112f43;
    color: white;
    font-size: 24px;
    cursor: pointer;
  }
  .mobile-menu-close {
    display: block;
    position: absolute;
    right: 12px;
    top: 12px;
  }
  .fleet-brand {
    padding-top: 5px;
    padding-right: 45px;
  }
  .mobile-navigation-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: #03182699;
    z-index: 201;
  }
  .customer-navigation .fleet-menu {
    grid-template-columns: 1fr !important;
  }
  .fleet-nav-link {
    font-size: 14px;
    min-height: 46px;
  }
  .account-actions {
    font-size: 14px;
  }
  .account-actions a,
  .account-actions button {
    min-height: 44px;
    display: flex;
    align-items: center;
  }
}
</style>
