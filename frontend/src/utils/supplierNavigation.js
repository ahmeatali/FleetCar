import { supplierNavigation } from './supplierModules.js'

// Reuse the existing destinations and labels; grouping changes presentation only.
const entry = (key) =>
  supplierNavigation.find(
    (item) => item.to === (key === 'home' ? '/supplier-portal' : `/supplier-portal/${key}`),
  )
const group = (id, label, icon, keys) => ({ id, label, icon, children: keys.map(entry) })

export const supplierNavigationGroups = [
  entry('home'),
  entry('operations'),
  group('vehicles', 'Araçlar', '▱', [
    'vehicles',
    'maintenance',
    'service',
    'tire',
    'damage',
    'policies',
    'hgs',
    'fines',
    'fuel',
    'sales',
  ]),
  group('rentals', 'Kiralamalar', '▣', [
    'reservations',
    'rentals',
    'offers',
    'contracts',
    'deliveries',
    'returns',
    'marketplace',
  ]),
  entry('customers'),
  group('accounting', 'Muhasebe', '▤', ['invoices', 'accounting', 'approvals']),
  group('reports', 'Raporlar', '▥', ['reports', 'planning']),
  group('settings', 'Ayarlar', '⚙', ['settings', 'branches', 'users']),
]
