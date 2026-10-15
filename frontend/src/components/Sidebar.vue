<template>
  <header class="mobile-navigation-bar">
    <router-link :to="supplier ? '/supplier-portal' : '/dashboard'" class="mobile-brand"
      ><img
        class="customer-logo customer-logo--mobile"
        src="/fleetrent-logo.jpeg"
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
        src="/fleetrent-logo.jpeg"
        alt="FleetRent"
        width="188"
        height="46"
    /></router-link>
    <nav :aria-label="supplier ? 'Tedarikçi menüsü' : 'Müşteri menüsü'">
      <ul class="fleet-menu">
        <li v-for="item in items" :key="item.label">
          <router-link
            v-if="item.to"
            :to="item.to"
            class="fleet-nav-link"
            :class="{ selected: isSelected(item) }"
            ><span class="nav-glyph" aria-hidden="true">{{ item.icon }}</span
            >{{ item.label }}</router-link
          >
          <UiButton
            v-else
            class="fleet-nav-link unavailable"
            :aria-label="item.label + ': Yakında'"
            aria-disabled="true"
            ><span class="unavailable-content"
              ><span class="nav-glyph" aria-hidden="true">{{ item.icon }}</span
              >{{ item.label }}</span
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

import { useRoute, useRouter } from 'vue-router'
import { supplierNavigation } from '../utils/supplierModules'
import { supplierApi } from '../utils/supplierApi'
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
const props = defineProps({ supplier: Boolean })
const route = useRoute(),
  router = useRouter()
const mobileOpen = ref(false),
  isMobile = ref(false),
  menuButton = ref(null),
  menuPanel = ref(null),
  closeButton = ref(null)
let media,
  previousOverflow = ''
const customerItems = [
  { label: 'Ana Sayfa', icon: '⌂', to: '/dashboard' },
  { label: 'Araçlar', icon: '▱', to: '/dashboard/vehicles' },
  { label: 'Talep & Teklifler', icon: '▤', to: '/dashboard/quotes' },
  { label: 'Sözleşmeler', icon: '▣' },
  { label: 'Servis / Bakım', icon: '⚒', to: '/dashboard/service-management' },
  { label: 'Lastik Yönetimi', icon: '◎', to: '/dashboard/tires' },
  { label: 'Hasar ve Kaza', icon: '⚠', to: '/dashboard/service-management?tab=damage' },
  { label: 'Yol Yardım', icon: '♧', to: '/dashboard/roadside' },
  { label: 'Şoförlü Araçlar', icon: '♧' },
  { label: 'Araç Takip', icon: '⌖', to: '/dashboard/reports?tab=location' },
  { label: 'HGS & Cezalar', icon: '♜' },
  { label: 'Yakıt ve Giderler', icon: '▥', to: '/dashboard/fuel' },
  { label: 'Faturalar', icon: '▤' },
  { label: 'Raporlar', icon: '▥', to: '/dashboard/reports' },
  { label: 'Belgeler', icon: '▤', to: '/dashboard/settings?tab=sirket_evraklari' },
  { label: 'Bildirimler', icon: '♧' },
  { label: 'Ayarlar', icon: '⚙', to: '/dashboard/settings' },
  { label: 'Tedarikçi İşlemleri', icon: '▤', to: '/dashboard/requests' },
  { label: 'İş Emirleri', icon: '▣', to: '/dashboard/work-orders' },
]
const items = computed(() => (props.supplier ? supplierNavigation : customerItems))
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
onMounted(() => {
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
    for (const key of [
      'fleetcar_supplier_token',
      'fleetcar_supplier_id',
      'fleetcar_supplier_name',
      'fleetcar_supplier_email',
      'fleetcar_supplier_type',
      'fleetcar_supplier_role',
      'fleetcar_supplier_user_name',
    ])
      localStorage.removeItem(key)
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
  background: #fff;
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
  font-size: 23px;
  width: 22px;
  display: inline-block;
  text-align: center;
  line-height: 1;
}
.unavailable {
  cursor: default;
}
.unavailable-content {
  display: flex;
  gap: 12px;
  align-items: center;
  filter: blur(0.7px);
  opacity: 0.55;
}
.coming-soon {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  background: #031826b3;
  border-radius: 5px;
  color: white;
  font-size: 12px;
}
.unavailable:hover .coming-soon,
.unavailable:focus-visible .coming-soon {
  opacity: 1;
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
