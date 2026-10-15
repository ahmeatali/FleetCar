import { authorizedOptions } from '../api/session.js'

const INSTALLED = Symbol.for('fleetrent.portalFetch')

// Compatibility bridge for legacy pages; new code imports an explicit API client.
export function installPortalFetch() {
  if (window.fetch[INSTALLED]) return
  const original = window.fetch.bind(window)
  const wrapped = (input, options = {}) => original(input, authorizedOptions(input, options))
  wrapped[INSTALLED] = true
  window.fetch = wrapped
}
