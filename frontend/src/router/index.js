import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import VehiclesView from '../views/VehiclesView.vue'
import RequestsView from '../views/RequestsView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminPortalView from '../views/AdminPortalView.vue'
import ProfileView from '../views/ProfileView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/vehicles',
    name: 'Vehicles',
    component: VehiclesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/requests',
    name: 'Requests',
    component: RequestsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/quotes',
    name: 'Quotes',
    component: () => import('../views/QuotesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/reports',
    name: 'Reports',
    component: () => import('../views/ReportsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin-login',
    name: 'AdminLogin',
    component: AdminLoginView
  },
  {
    path: '/admin-portal',
    name: 'AdminPortal',
    component: AdminPortalView,
    meta: { requiresAdminAuth: true }
  },
  {
    path: '/supplier-login',
    name: 'SupplierLogin',
    component: () => import('../views/SupplierLoginView.vue')
  },
  {
    path: '/service-login',
    name: 'ServiceLogin',
    component: () => import('../views/ServiceLoginView.vue')
  },
  {
    path: '/supplier-portal',
    name: 'SupplierPortal',
    component: () => import('../views/SupplierPortalView.vue'),
    meta: { requiresSupplierAuth: true }
  },
  {
    path: '/service-portal',
    name: 'ServicePortal',
    component: () => import('../views/SupplierPortalView.vue'),
    meta: { requiresSupplierAuth: true }
  },
  {
    path: '/setup-password',
    name: 'SupplierSetupPassword',
    component: () => import('../views/SupplierSetupPasswordView.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Simple navigation guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = Boolean(localStorage.getItem('fleetcar_token'))
  const isAdminAuthenticated = Boolean(localStorage.getItem('fleetcar_admin_token'))
  const isSupplierAuthenticated = Boolean(localStorage.getItem('fleetcar_supplier_token'))
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      next({ name: 'Login' })
    } else {
      next()
    }
  } else if (to.matched.some(record => record.meta.requiresAdminAuth)) {
    if (!isAdminAuthenticated) {
      next({ name: 'AdminLogin' })
    } else {
      next()
    }
  } else if (to.matched.some(record => record.meta.requiresSupplierAuth)) {
    if (!isSupplierAuthenticated) {
      next({ name: 'SupplierLogin' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
