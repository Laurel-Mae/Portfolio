import {icon} from './icons.js';
export function toast(message, type = 'info') {
  const region = document.querySelector('#toast-region');
  while (region.children.length >= 3) region.firstElementChild.remove();
  const element = document.createElement('div'); element.className = 'toast'; element.dataset.type = type;
  const text = document.createElement('p'); text.textContent = message;
  const close = document.createElement('button'); close.type = 'button'; close.setAttribute('aria-label', 'Dismiss notification'); close.append(icon('close'));
  element.append(icon(type === 'success' ? 'check' : type === 'error' ? 'alert' : 'info'), text, close);
  region.append(element);
  let timer;
  const dismiss = () => {clearTimeout(timer); element.remove();};
  const schedule = () => {clearTimeout(timer); timer = setTimeout(dismiss, type === 'error' ? 10000 : 7000);};
  close.addEventListener('click', dismiss); element.addEventListener('pointerenter', () => clearTimeout(timer));
  element.addEventListener('pointerleave', schedule); element.addEventListener('focusin', () => clearTimeout(timer));
  element.addEventListener('focusout', schedule); schedule();
}
