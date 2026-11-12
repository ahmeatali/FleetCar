// Who is signed in to the customer portal, for headers. Login (and support impersonation)
// store the role; the company owner has no team role and is stored as "owner".
export function customerRoleLabel(storage = globalThis.localStorage) {
  const role = storage?.getItem('fleetcar_user_role')
  if (!role) return 'Müşteri Hesabı' // sessions from before the role was stored
  return role === 'owner' ? 'Hesap Sahibi' : role
}
