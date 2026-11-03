import {icon} from './icons.js';
export function initTheme() {
  const button = document.querySelector('#theme-toggle');
  const sync = () => {
    const dark = document.documentElement.dataset.theme === 'dark';
    const label = `Switch to ${dark ? 'light' : 'dark'} theme`;
    button.replaceChildren(icon(dark ? 'sun' : 'moon'));
    button.setAttribute('aria-label', label); button.dataset.tooltip = label;
    document.querySelector('meta[name="theme-color"]').content = dark ? '#151515' : '#F7F5F0';
  };
  button.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try {localStorage.setItem('mae-theme', theme);} catch {}
    document.querySelector('#tooltip').hidden = true;
    sync(); document.dispatchEvent(new CustomEvent('themechange', {detail:theme}));
  });
  // No System option: device preference is only the initial fallback.
  sync();
}
