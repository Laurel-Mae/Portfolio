// Small, locally defined SVG set. No icon service, external library or CDN.
const paths = {
  'arrow-up-right':'<path d="M6 18 18 6M6 6h12v12"/>',
  'arrow-down':'<path d="M12 4v16m-6-6 6 6 6-6"/>',
  'arrow-up':'<path d="M12 20V4m-6 6 6-6 6 6"/>',
  'chevron-down':'<path d="m6 9 6 6 6-6"/>',
  'moon':'<path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5 8.5 8.5 0 1 0 20.5 14.3Z"/>',
  'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  'file':'<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8Z"/><path d="M14 3v5h5M9 12h6m-6 4h6"/>',
  'files':'<path d="M9 3h8l4 4v11a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Zm7 0v5h5M4 7v14h12"/>',
  'spark':'<path d="M12 2v20M2 12h20M5 5l14 14M5 19 19 5"/>',
  'focus':'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5"/><circle cx="12" cy="12" r="4"/>',
  'people':'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 4v3"/>',
  'growth':'<path d="M4 20V10m7 10V6m7 14V3M3 4l5-2m8 0h6v6m0-6-8 8-4-3-6 6"/>',
  'briefcase':'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V4h8v3M3 12a22 22 0 0 0 18 0M10 12v3h4v-3"/>',
  'graduation':'<path d="m2 9 10-5 10 5-10 5Zm4 2v6c4 3 8 3 12 0v-6M22 9v8"/>',
  'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
  'shield':'<path d="M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  'mail':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  'home':'<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7"/>',
  'user':'<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  'grid':'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  'close':'<path d="m6 6 12 12M6 18 18 6"/>',
  'network':'<rect x="8" y="2" width="8" height="6" rx="1"/><rect x="2" y="16" width="7" height="6" rx="1"/><rect x="15" y="16" width="7" height="6" rx="1"/><path d="M12 8v4M5.5 16v-4h13v4"/>',
  'monitor':'<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 22h8m-4-5v5M5 13h14"/>',
  'message':'<path d="M21 11a9 9 0 0 1-9 9 11 11 0 0 1-4-1l-5 2 1-5a9 9 0 1 1 17-5Z"/><path d="M8 8h8m-8 5h5"/>',
  'book':'<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1Zm0 0v15"/>',
  'check':'<path d="m5 12 4 4L19 6"/>',
  'alert':'<path d="m12 3 10 18H2Zm0 5v6m0 3v1"/>',
  'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 15v6h16v-6"/>',
  'signal':'<path d="M2 8c5.5-5.5 14.5-5.5 20 0M5 12c4-4 10-4 14 0M8.5 16c2-2 5-2 7 0"/><circle cx="12" cy="20" r="1"/>',
  'wrench':'<path d="M14 6a5 5 0 0 0-6.6 6.6l-5.5 5.5a2 2 0 1 0 2.8 2.8l5.5-5.5A5 5 0 0 0 16.8 9l-3.4 3.4-3-3L14 6Z"/>',
  'terminal':'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 4 3-4 3m6 0h5"/>',
  'server':'<rect x="3" y="3" width="18" height="8" rx="2"/><rect x="3" y="13" width="18" height="8" rx="2"/><path d="M7 7h.01M7 17h.01M12 7h6M12 17h6"/>',
  'whatsapp':'<path d="M20 11.4a8.2 8.2 0 0 1-11.5 7.5L4 20l1.1-4.5A8.2 8.2 0 1 1 20 11.4Z"/><path d="M9 8c.2-.5.5-.6.8-.4l1.4 1.1c.3.3.2.6-.1.9l-.6.7a9 9 0 0 0 3.1 3.1l.7-.6c.3-.3.6-.4.9-.1l1.1 1.4c.2.3.1.6-.4.8-2.1.8-5-1.1-6.6-2.8C7.8 10.5 8.1 9.1 9 8Z"/>',
  'phone':'<path d="m5 3 4 4-2 3a15 15 0 0 0 7 7l3-2 4 4-3 3C10 21 3 14 2 6Z"/>',
};
export function icon(name) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  node.setAttribute('viewBox', '0 0 24 24'); node.setAttribute('class', 'icon');
  node.setAttribute('aria-hidden', 'true'); node.setAttribute('focusable', 'false');
  node.innerHTML = paths[name] || paths.info;
  return node;
}
export function hydrateIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach(node => {
    if (node.dataset.hydrated) return;
    node.replaceChildren(icon(node.dataset.icon)); node.dataset.hydrated = 'true';
  });
}
