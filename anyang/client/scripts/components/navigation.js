// Desktop: sticky horizontal navigation. Compact screens: an accessible radial menu.
export function initNavigation() {
  const dock = document.querySelector('#orbit-dock');
  const button = document.querySelector('#orbit-toggle');
  const menu = document.querySelector('#orbit-menu');
  const backdrop = document.querySelector('#nav-backdrop');
  const orbitalLinks = [...menu.querySelectorAll('a[href^="#"]')];
  const desktopLinks = [...document.querySelectorAll('#desktop-nav a[href^="#"]')];
  const allLinks = [...desktopLinks, ...orbitalLinks];
  const sections = [...document.querySelectorAll('main section[data-section]')];
  const locationLabel = document.querySelector('#orbit-location');
  const compact = matchMedia('(max-width:1080px)');
  const inertTargets = [document.querySelector('header'), document.querySelector('main'), document.querySelector('footer')];
  let open = false;
  let closeTimer;
  let overflowBefore = '';
  let scrollQueued = false;

  function close(restoreFocus = true) {
    if (!open) return;
    open = false;
    dock.classList.remove('is-open');
    button.setAttribute('aria-expanded','false');
    button.setAttribute('aria-label','Open section navigation');
    backdrop.hidden = true;
    menu.inert = true;
    inertTargets.forEach(target => {if (target) target.inert = false;});
    document.body.style.overflow = overflowBefore;
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {if (!open) menu.hidden = true;}, 280);
    if (restoreFocus && compact.matches) button.focus({preventScroll:true});
  }
  function expand() {
    if (!compact.matches) return;
    clearTimeout(closeTimer);
    open = true;
    overflowBefore = document.body.style.overflow;
    menu.hidden = false;
    menu.inert = false;
    backdrop.hidden = false;
    document.body.style.overflow = 'hidden';
    inertTargets.forEach(target => {if (target) target.inert = true;});
    button.setAttribute('aria-expanded','true');
    button.setAttribute('aria-label','Close section navigation');
    requestAnimationFrame(() => {
      dock.classList.add('is-open');
      (orbitalLinks.find(link => link.hasAttribute('aria-current')) || orbitalLinks[0]).focus({preventScroll:true});
    });
  }
  button.addEventListener('click',() => open ? close() : expand());
  backdrop.addEventListener('click',() => close());
  orbitalLinks.forEach(link => link.addEventListener('click',() => close(false)));
  document.addEventListener('keydown',event => {
    if (!open) return;
    if (event.key === 'Escape') {event.preventDefault();close();return;}
    const focusables = [...orbitalLinks,button];
    const current = focusables.indexOf(document.activeElement);
    if (event.key === 'Tab') {
      event.preventDefault();
      focusables[(current + (event.shiftKey?-1:1) + focusables.length) % focusables.length].focus();
    } else if (['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].includes(event.key)) {
      event.preventDefault();
      const delta = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : -1;
      const idx = orbitalLinks.indexOf(document.activeElement);
      orbitalLinks[(idx + delta + orbitalLinks.length) % orbitalLinks.length].focus();
    }
  });
  function update() {
    scrollQueued = false;
    const headerHeight = Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height')) || 76;
    const marker = headerHeight + 38;
    let active = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= marker) active = section;
    }
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 5) active = sections.at(-1);
    allLinks.forEach(link => {
      if (link.hash === `#${active.id}`) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    });
    locationLabel.replaceChildren(document.createTextNode(String(sections.indexOf(active) + 1).padStart(2,'0') + ' '));
    const slash = document.createElement('span');slash.textContent='/';
    locationLabel.append(slash,document.createTextNode(' '+active.dataset.section));
    const max = document.documentElement.scrollHeight - innerHeight;
    document.querySelector('#page-progress').style.transform = `scaleX(${max>0?Math.min(1,scrollY/max):0})`;
  }
  function queueUpdate(){if(!scrollQueued){scrollQueued=true;requestAnimationFrame(update);}}
  window.addEventListener('scroll',queueUpdate,{passive:true});
  window.addEventListener('hashchange',queueUpdate);
  window.addEventListener('resize',queueUpdate,{passive:true});
  compact.addEventListener('change',() => {if(!compact.matches)close(false);dock.hidden=false;queueUpdate();});
  document.addEventListener('focusin',event => {
    if(compact.matches && event.target.matches('input,textarea,select')){
      if(open) close(false);
      dock.hidden = true;
    }
  });
  document.addEventListener('focusout',() => setTimeout(() => {
    if(!document.activeElement.matches('input,textarea,select'))dock.hidden=false;
  },0));
  menu.inert=true;
  update();
}
