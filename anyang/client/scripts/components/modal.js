const dialog = document.querySelector('#site-modal');
let previousFocus = null;
let previousOverflow = '';
export function openModal({title, eyebrow = 'PORTFOLIO', content, wide = false, restoreFocus}) {
  if (dialog.open) dialog.close();
  previousFocus = restoreFocus || document.activeElement;
  document.querySelector('#modal-title').textContent = title;
  document.querySelector('#modal-eyebrow').textContent = eyebrow;
  document.querySelector('#modal-body').replaceChildren(content);
  dialog.classList.toggle('document-modal', wide);
  previousOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  dialog.showModal();
  document.querySelector('#modal-close').focus();
}
export function closeModal() { if (dialog.open) dialog.close(); }
export function initModal() {
  document.querySelector('#modal-close').addEventListener('click', closeModal);
  dialog.addEventListener('click', event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) closeModal();
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = previousOverflow;
    document.querySelector('#modal-body').replaceChildren();
    if (previousFocus?.isConnected) previousFocus.focus({preventScroll:true});
  });
}
export function paragraph(text) { const p = document.createElement('p'); p.textContent = text; return p; }
