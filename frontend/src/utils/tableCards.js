/*
 * Phone-width tables: list tables turn into one card per row (see .fr-cards in
 * mobile-tables.css). Each cell needs its column name as data-label, which this module fills
 * in from the table header, so no template has to repeat the header text per cell.
 */

// List tables that become cards. Matrix and calendar tables keep their grid.
export const CARD_TABLES = '.sw-table, .custom-table, .team-table, .data-table, .fuel-table'
const KEEP_GRID = '.fp-calendar table, .permission-matrix'

export function headerLabels(table) {
  const row = table.tHead?.rows[table.tHead.rows.length - 1]
  if (!row) return []
  const labels = []
  for (const th of row.cells) {
    const text = th.textContent.replace(/\s+/g, ' ').trim()
    for (let i = 0; i < (th.colSpan || 1); i++) labels.push(text)
  }
  return labels
}

export function labelTable(table) {
  if (table.matches(KEEP_GRID)) return
  table.classList.add('fr-cards')
  const labels = headerLabels(table)
  if (!labels.length) return
  for (const body of table.tBodies) {
    for (const row of body.rows) {
      let col = 0
      let titled = false
      for (const cell of row.cells) {
        // A template-provided label wins; full-width message rows get none.
        if (!cell.hasAttribute('data-label') && cell.colSpan === 1 && labels[col]) {
          cell.setAttribute('data-label', labels[col])
        }
        const label = cell.getAttribute('data-label') || ''
        // A running number or a select-all checkbox column says nothing on a card.
        const filler =
          label === '#' || (!label && cell.querySelector(':scope > input[type=checkbox]'))
        cell.classList.toggle('fr-card-skip', Boolean(filler))
        // The first real column (plate, record no, company) heads the card.
        const title = !titled && !filler && cell.colSpan === 1
        cell.classList.toggle('fr-card-title', title)
        if (title) titled = true
        col += cell.colSpan || 1
      }
    }
  }
}

export function labelAll(root = document) {
  root.querySelectorAll(CARD_TABLES).forEach((t) => t.tagName === 'TABLE' && labelTable(t))
}

export function installTableCards() {
  if (typeof MutationObserver === 'undefined') return
  let queued = false
  const run = () => {
    queued = false
    labelAll()
  }
  new MutationObserver(() => {
    if (!queued) {
      queued = true
      requestAnimationFrame(run)
    }
  }).observe(document.body, { childList: true, subtree: true })
  run()
}
