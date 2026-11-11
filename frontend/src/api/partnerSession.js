export function savePartnerSession(data, email, storage = localStorage) {
  const supplier = data?.supplier
  if (!data?.token || !Number.isInteger(supplier?.id) || supplier.id <= 0) {
    throw new Error('Sunucudan geçerli hesap bilgisi alınamadı.')
  }
  const values = {
    fleetcar_supplier_token: data.token,
    fleetcar_supplier_id: supplier.id,
    fleetcar_supplier_name: supplier.name || '',
    fleetcar_supplier_type: supplier.type || '',
    fleetcar_supplier_email: supplier.email || email,
    fleetcar_supplier_role: data.user?.role || 'owner',
    fleetcar_supplier_user_name: data.user?.name || supplier.name || '',
    fleetcar_user_email: data.user?.email || email,
    fleetcar_user_verified: supplier.is_email_verified ? 'true' : 'false',
    fleet_supplier: JSON.stringify(supplier),
  }
  for (const [key, value] of Object.entries(values)) storage.setItem(key, String(value))
}

const SUPPLIER_KEYS = [
  'fleetcar_supplier_token',
  'fleetcar_supplier_id',
  'fleetcar_supplier_name',
  'fleetcar_supplier_email',
  'fleetcar_supplier_type',
  'fleetcar_supplier_role',
  'fleetcar_supplier_user_name',
]

export function clearSupplierSession(storage = localStorage) {
  for (const key of SUPPLIER_KEYS) storage.removeItem(key)
}
