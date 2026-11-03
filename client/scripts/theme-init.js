/* Blocking, tiny first-paint theme selection; works before the styles load. */
(() => {
  let preference;
  try { preference = localStorage.getItem('mae-theme'); } catch {}
  const theme = preference === 'dark' || preference === 'light' ? preference :
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#151515' : '#F7F5F0');
})();
