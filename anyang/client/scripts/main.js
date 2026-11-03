import {hydrateIcons} from './components/icons.js';
import {initTheme} from './components/theme.js';
import {initModal} from './components/modal.js';
import {initCareer} from './components/career.js';
import {initTooltips} from './components/tooltip.js';
import {initNavigation} from './components/navigation.js';
import {initPrivacy} from './components/privacy.js';
import {initContent} from './sections/content.js';
import {initContact} from './sections/contact.js';

// Isolate feature failures so one unavailable browser API cannot blank the site.
for (const initialize of [hydrateIcons,initTheme,initModal,initCareer,initTooltips,initContent,initNavigation,initPrivacy,initContact]) {
  try {initialize();} catch(error) {console.error(`Could not initialize ${initialize.name}`,error);}
}
const portrait=document.querySelector('#hero-portrait'),wrap=document.querySelector('#portrait-wrap');
const overlay=document.querySelector('#page-loader');
let loadDone=false;
// The branded loader only appears if the critical portrait is genuinely slow.
// It never imposes a fixed wait or blocks access after a failed image load.
const showLoading=setTimeout(()=>{if(!loadDone)overlay.hidden=false;},180);
const ready=()=>{
  loadDone=true;
  clearTimeout(showLoading);
  portrait.classList.add('loaded');
  wrap.classList.remove('skeleton');
  overlay.hidden=true;
};
if(portrait.complete)ready();
else{portrait.addEventListener('load',ready,{once:true});portrait.addEventListener('error',ready,{once:true});}
// An unexpectedly stalled resource must not hold the page indefinitely.
setTimeout(()=>{if(!loadDone)ready();},4500);
if('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches){
  document.documentElement.classList.add('motion-ready');
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.remove('pending-reveal');observer.unobserve(entry.target);}}),{threshold:0.06,rootMargin:'0px 0px 15px 0px'});
  document.querySelectorAll('.reveal').forEach(el=>{if(el.getBoundingClientRect().top>innerHeight){el.classList.add('pending-reveal');observer.observe(el);}});
}
// No artificial loading delay, no polling, and no decorative full-page wait.
