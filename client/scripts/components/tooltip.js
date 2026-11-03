export function initTooltips() {
  const tip = document.querySelector('#tooltip'); let active = null;
  const hide = () => {if (active) active.removeAttribute('aria-describedby'); tip.hidden = true; active = null;};
  const show = element => {
    if (!element?.dataset.tooltip) return;
    active = element; tip.textContent = element.dataset.tooltip; tip.hidden = false;
    const rect = element.getBoundingClientRect();
    const x = Math.min(window.innerWidth - tip.offsetWidth - 12, Math.max(12, rect.left + rect.width / 2 - tip.offsetWidth / 2));
    const y = rect.bottom + tip.offsetHeight + 16 > innerHeight ? rect.top - tip.offsetHeight - 9 : rect.bottom + 9;
    tip.style.left = `${x}px`; tip.style.top = `${y}px`; element.setAttribute('aria-describedby', 'tooltip');
  };
  document.addEventListener('pointerover', event => {if (event.pointerType === 'mouse') show(event.target.closest('[data-tooltip]'));});
  document.addEventListener('pointerout', hide);
  document.addEventListener('focusin', event => show(event.target.closest('[data-tooltip]')));
  document.addEventListener('focusout', hide);
  document.addEventListener('keydown', event => {if (event.key === 'Escape') hide();});
  window.addEventListener('scroll', hide, {passive:true});
}
