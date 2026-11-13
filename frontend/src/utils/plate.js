/*
 * Turkish licence plates are written "34 ABC 123": province code, letters, number, with a
 * space between each. Same rule as backend app/common/plates.py, so what the form shows is
 * what gets stored.
 */
const PLATE = /^(\d{2})([A-Z]{1,3})(\d{2,5})$/

const upper = (value) =>
  String(value ?? '')
    .toLocaleUpperCase('tr-TR')
    .replace(/İ/g, 'I')

export function compactPlate(value) {
  return upper(value).replace(/\s+/g, '')
}

export function formatPlate(value) {
  const match = compactPlate(value).match(PLATE)
  if (match) return match.slice(1).join(' ')
  return upper(value).replace(/\s+/g, ' ').trim()
}

// Province codes run 01–81; a plate outside that pattern is allowed (foreign, temporary)
// but worth a second look before saving.
export function isTurkishPlate(value) {
  const match = compactPlate(value).match(PLATE)
  return Boolean(match && Number(match[1]) >= 1 && Number(match[1]) <= 81)
}
