import {profile} from '../../data/profile.js';
import {experience} from '../../data/experience.js';
import {education} from '../../data/education.js';
import {skills} from '../../data/skills.js';
import {icon} from '../components/icons.js';
import {openModal,paragraph} from '../components/modal.js';
function text(tag,value,className=''){const el=document.createElement(tag);el.textContent=value??'';if(className)el.className=className;return el;}
function nameAndIdentity(){
  const {identity,hero,about,portrait}=profile;
  document.title=`${identity.name} | ${identity.title}`;
  document.querySelectorAll('.brand-copy strong,.footer-brand strong').forEach(node=>node.textContent=identity.name);
  document.querySelectorAll('.brand-copy small,.footer-brand small').forEach(node=>node.textContent=identity.title);
  const headline=document.querySelector('#hero-heading');
  const parts=identity.name.trim().split(/\s+/);
  headline.replaceChildren(document.createTextNode(parts.slice(0,-1).join(' ')||parts[0]),document.createElement('br'));
  const last=document.createElement('span');last.append(document.createTextNode(parts.length>1?parts.at(-1):''));
  const dot=document.createElement('span');dot.className='title-dot';dot.textContent='.';last.append(dot);headline.append(last);
  document.querySelector('#hero-role').textContent=identity.title;
  document.querySelector('#hero-intro').textContent=hero.introduction;
  document.querySelector('#hero-note').querySelector('span:last-child').textContent=hero.note;
  document.querySelector('#hero-availability').lastChild.textContent=' '+hero.availability;
  const metas=document.querySelectorAll('#hero-bottom>div');
  metas[0]?.querySelector('span:last-child')?.replaceChildren(document.createTextNode(hero.focus));
  metas[1]?.querySelector('span:last-child')?.replaceChildren(document.createTextNode(hero.direction));
  const image=document.querySelector('#hero-portrait');
  image.alt=portrait.alt; if(portrait.image && image.getAttribute('src')!==portrait.image){image.src=portrait.image;image.removeAttribute('srcset');}
  document.querySelector('#portrait-caption strong').textContent=portrait.caption;
  document.querySelector('#portrait-caption small').textContent=portrait.subtitle || `${identity.name} · ${identity.status}`;
  const aboutTitle=document.querySelector('#about-title');
  aboutTitle.replaceChildren(document.createTextNode(about.headline),document.createElement('br'));
  const accent=document.createElement('span');accent.className='muted-heading';accent.textContent=about.headlineAccent;
  aboutTitle.append(accent);
  const paragraphNodes=document.querySelectorAll('#about-body>p');
  about.paragraphs.slice(0,paragraphNodes.length).forEach((copy,i)=>paragraphNodes[i].textContent=copy);
  document.querySelector('#copyright-year').textContent=String(new Date().getFullYear());
  const credit=document.querySelector('#developer-credit');if(credit){credit.textContent=profile.credit.name;const url=profile.credit.url;credit.href=/^https:\/\/[^\s]+$/i.test(url)?url:'#home';credit.append(icon('arrow-up-right'));}
}
function renderExperience(){
  if(!experience.length)return;
  document.querySelector('#experience-list').replaceChildren(...experience.map(item=>{
    const el=document.createElement('article');el.className='experience-item';
    el.append(text('span',item.period,'meta-label'),text('h3',item.role),text('span',item.organization,'experience-org'));
    if(item.type||item.location)el.append(text('p',[item.type,item.location].filter(Boolean).join(' · '),'experience-meta'));
    if(item.description)el.append(text('p',item.description));
    if(item.highlights?.length){const list=document.createElement('ul');item.highlights.forEach(line=>list.append(text('li',line)));el.append(list);}
    return el;
  }));
}
function renderEducation(){
  if(!education.length)return;
  document.querySelector('#education-list').replaceChildren(...education.map(item=>{
    const card=document.createElement('article');card.className='education-card education-entry';
    const graphic=document.createElement('div');graphic.className='education-icon';graphic.append(icon('graduation'));
    const body=document.createElement('div');body.append(text('span',item.period,'meta-label'),text('h3',item.program));
    if(item.status)body.append(text('span',item.status,'subtle-badge'));
    body.append(text('p',item.institution));if(item.location)body.append(text('p',item.location,'education-location'));
    if(item.description)body.append(text('p',item.description));
    if(item.highlights?.length){const list=document.createElement('ul');item.highlights.forEach(v=>list.append(text('li',v)));body.append(list);}
    card.append(graphic,body);return card;
  }));
}
function renderContact(){
  const grid=document.querySelector('#contact-links'),contact=profile.contact;
  const digits=String(contact.whatsapp||'').replace(/[^\d]/g,'');
  const entries=[
    {label:contact.email,href:`mailto:${contact.email}`,valid:/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact.email),name:'mail'},
    {label:'WhatsApp',href:`https://wa.me/${digits}`,valid:/^\d{8,15}$/.test(digits),name:'whatsapp',external:true},
    {label:contact.phone,href:`tel:${String(contact.phone).replace(/[^+\d]/g,'')}`,valid:/^\+?[\d\s()-]{7,}$/.test(contact.phone),name:'phone'},
  ];
  grid.replaceChildren(...entries.filter(e=>e.valid).map(e=>{
    const a=document.createElement('a');a.href=e.href;a.className='contact-link';
    if(e.external){a.target='_blank';a.rel='noopener noreferrer';}
    a.append(icon(e.name),text('span',e.label),icon('arrow-up-right'));return a;
  }));
}
function renderSkills(){
  const grid=document.querySelector('#skill-grid'),tabs=[...document.querySelectorAll('[data-skill-filter]')];
  function render(filter='all'){
    grid.replaceChildren(...skills.filter(item=>filter==='all'||item.category===filter).map(item=>{
      const card=document.createElement('article');card.className='skill-card';
      const action=document.createElement('button');action.type='button';action.className='skill-detail-button';action.setAttribute('aria-label',`More about ${item.title}`);
      action.append(document.createTextNode(item.label),icon('arrow-up-right'));
      action.addEventListener('click',()=>{
        const content=document.createElement('div');content.append(text('span',item.label,'subtle-badge'),paragraph(item.details));
        openModal({title:item.title,eyebrow:'AREAS OF INTEREST',content,restoreFocus:action});
      });
      card.append(icon(item.icon),text('h3',item.title),text('p',item.summary),action);return card;
    }));
  }
  tabs.forEach((tab,index)=>{
    function activate(){tabs.forEach(t=>{t.setAttribute('aria-selected',String(t===tab));t.tabIndex=t===tab?0:-1;});grid.setAttribute('aria-labelledby',tab.id);render(tab.dataset.skillFilter);}
    tab.addEventListener('click',activate);
    tab.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
      tabs[next].focus();tabs[next].click();
    });
  });
  document.querySelector('#tab-all span').textContent=String(skills.length).padStart(2,'0');render();
}
export function initContent(){nameAndIdentity();renderExperience();renderEducation();renderContact();renderSkills();}
