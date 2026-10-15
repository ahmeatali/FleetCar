// Shared by all dialog instances so nested dialogs do not unlock each other's scroll.
const stack = []
let previousOverflow = ''

export function registerModal(element, body = document.body) {
  if (!stack.length) {
    previousOverflow = body.style.overflow
    body.style.overflow = 'hidden'
  }
  stack.push(element)
  return () => {
    const index = stack.indexOf(element)
    if (index !== -1) stack.splice(index, 1)
    if (!stack.length) body.style.overflow = previousOverflow
  }
}

export function isTopModal(element) {
  return stack.at(-1) === element
}

export function trapModalFocus(event, element) {
  if (event.key !== 'Tab') return
  const nodes = [
    ...element.querySelectorAll('button,input,select,textarea,a[href],[tabindex]'),
  ].filter(
    (node) =>
      !node.disabled &&
      node.tabIndex >= 0 &&
      !node.closest('[inert]') &&
      node.getClientRects().length,
  )
  const first = nodes[0],
    last = nodes.at(-1)
  if (!first) {
    event.preventDefault()
    element.focus()
    return
  }
  if (
    event.shiftKey &&
    (document.activeElement === first || !element.contains(document.activeElement))
  ) {
    event.preventDefault()
    last.focus()
  } else if (
    !event.shiftKey &&
    (document.activeElement === last || !element.contains(document.activeElement))
  ) {
    event.preventDefault()
    first.focus()
  }
}
