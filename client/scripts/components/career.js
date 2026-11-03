import {profile} from '../../data/profile.js';
import {icon} from './icons.js';
import {openModal, closeModal, paragraph} from './modal.js';

const BASE = '/assets/career/';
const availability = new Map();
function documentUrl(document) {
  const filename = document?.filename;
  // No user-provided remote links, query strings, path traversal, or folders.
  if (typeof filename !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.pdf$/i.test(filename) || filename.includes('..')) return '';
  return BASE + encodeURIComponent(filename);
}
async function available(url) {
  if (!url) return false;
  if (availability.has(url)) return availability.get(url);
  try {
    const response = await fetch(url, {method:'HEAD',cache:'no-store'});
    const ok = response.ok && /application\/pdf/i.test(response.headers.get('content-type') || '');
    availability.set(url,ok); return ok;
  } catch {return false;}
}
function documentContent(doc,url,exists) {
  const content = document.createElement('div');
  if (!exists) {
    const mark = document.createElement('div');mark.className='modal-empty-icon';mark.append(icon('file'));
    content.append(mark, paragraph(`${doc.title} has not been added yet.`), paragraph('Once the PDF is placed in the assets/career folder, it will be available to preview and download here. For now, please use the contact section for an enquiry.'));
    const actions=document.createElement('div');actions.className='modal-actions';
    const link=document.createElement('a');link.href='#contact';link.className='button button-primary';link.textContent='Get in touch';link.append(icon('arrow-up-right'));link.addEventListener('click',closeModal);
    actions.append(link);content.append(actions);return {content,wide:false};
  }
  const toolbar=document.createElement('div');toolbar.className='modal-document-bar';
  toolbar.append(paragraph('Preview the PDF or save a copy.'));
  const download=document.createElement('a');download.className='button button-secondary';download.href=url;download.download=doc.filename;download.textContent='Download PDF';download.append(icon('download'));toolbar.append(download);
  const wrap=document.createElement('div');wrap.className='document-viewer-wrap';
  const loader=document.createElement('div');loader.className='document-loader';loader.innerHTML='<span class="spinner" aria-label="Loading document"></span>';
  const iframe=document.createElement('iframe');iframe.title=`${profile.identity.name} — ${doc.title}`;iframe.className='document-viewer';iframe.src=`${url}#view=FitH`;iframe.addEventListener('load',()=>loader.remove(),{once:true});
  wrap.append(iframe,loader);
  const help=paragraph('PDF preview support depends on your browser.');help.className='document-help';
  const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open the PDF in a new tab.';link.className='text-link';help.append(' ',link);
  content.append(toolbar,wrap,help);return {content,wide:true};
}
export function initCareer() {
  const trigger=document.querySelector('#career-trigger'),menu=document.querySelector('#career-menu'),dropdown=document.querySelector('#career-dropdown');
  const options=[...menu.querySelectorAll('button[data-document]')];
  const close=(focus=false)=>{menu.hidden=true;trigger.setAttribute('aria-expanded','false');if(focus)trigger.focus();};
  async function refresh() {
    await Promise.all(options.map(async button=>{
      const doc=profile.documents[button.dataset.document];
      const state=button.querySelector('.document-state');
      const url=documentUrl(doc);
      const exists=await available(url);
      state.textContent=exists?'Preview or download PDF':'Not yet available';
    }));
  }
  trigger.addEventListener('click',()=>{
    const wasOpen=!menu.hidden;menu.hidden=wasOpen;trigger.setAttribute('aria-expanded',String(!wasOpen));
    if(!wasOpen) {options.forEach(button=>button.querySelector('.document-state').textContent='Checking document…');refresh();}
  });
  document.addEventListener('click',event=>{if(!event.target.closest('#career-dropdown'))close();});
  document.addEventListener('keydown',event=>{
    if(menu.hidden)return;
    if(event.key==='Escape'){event.preventDefault();close(true);return;}
    if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)&&(event.target===trigger||menu.contains(event.target))){
      event.preventDefault();let index=options.indexOf(document.activeElement);
      index=event.key==='Home'?0:event.key==='End'?options.length-1:(index+(event.key==='ArrowDown'?1:-1)+options.length)%options.length;
      options[index].focus();
    }
  });
  dropdown.addEventListener('focusout',()=>setTimeout(()=>{if(!dropdown.contains(document.activeElement))close();},0));
  options.forEach(button=>button.addEventListener('click',async()=>{
    const doc=profile.documents[button.dataset.document],url=documentUrl(doc);
    close();
    const loading=document.createElement('div');loading.className='document-loading-state';loading.append(icon('file'),paragraph('Checking the document…'));
    openModal({title:doc.title,eyebrow:'CAREER PROFILE',content:loading,restoreFocus:trigger});
    const exists=await available(url);
    if(!document.querySelector('#site-modal').open || document.querySelector('#modal-title').textContent!==doc.title)return;
    const result=documentContent(doc,url,exists);
    document.querySelector('#modal-body').replaceChildren(result.content);
    document.querySelector('#site-modal').classList.toggle('document-modal',result.wide);
  }));
}
