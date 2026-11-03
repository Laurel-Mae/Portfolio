import {api, config} from '../api.js';
import {toast} from '../components/toast.js';

function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
  const hex = [...bytes].map(x => x.toString(16).padStart(2,'0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
async function fingerprint(payload) {
  const value = JSON.stringify([payload.name,payload.email,payload.subject,payload.message]);
  if (!crypto.subtle) return null; // HTTP LAN preview: no persistent fingerprint.
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))].map(x => x.toString(16).padStart(2,'0')).join('');
}
export function initContact() {
  const form = document.querySelector('#contact-form'), button = document.querySelector('#send-button');
  const status = document.querySelector('#contact-status'); const message = form.elements.message;
  let startedAt = Date.now()/1000, busy = false, lastRequest = null, lastPayload = null, captchaToken = '', widgetId = null, captchaLoaded = false;
  try {lastRequest = JSON.parse(sessionStorage.getItem('mae-contact-reference') || 'null');} catch {}
  function setStatus(text, state = 'info') {status.textContent = text;status.dataset.state = state;}
  function clearError(name) {form.elements[name]?.removeAttribute('aria-invalid'); const el = document.querySelector(`#error-${name}`);if (el) el.textContent='';}
  function showError(name, text) {const input = form.elements[name]; input?.setAttribute('aria-invalid','true');document.querySelector(`#error-${name}`).textContent=text;}
  function validate() {
    ['name','email','subject','message','consent'].forEach(clearError);
    const errors = [];
    const rules = [['name',2,100,'Enter your name (2–100 characters).'],['subject',3,140,'Add a subject (3–140 characters).'],['message',10,5000,'Write a message between 10 and 5,000 characters.']];
    rules.forEach(([name,min,max,text]) => {const value=form.elements[name].value.trim();if (value.length<min || value.length>max || (name!=='message' && /[\x00-\x1f\x7f]/.test(value))) {showError(name,text);errors.push(name);}});
    if (!form.elements.email.validity.valid || !form.elements.email.value.trim()) {showError('email','Please enter a valid email address.');errors.push('email');}
    if (!form.elements.consent.checked) {showError('consent','Please agree before sending your message.');errors.push('consent');}
    if (errors.length) {form.elements[errors[0]].focus();return false;} return true;
  }
  function busyState(value) {
    busy=value;button.disabled=value;button.setAttribute('aria-busy',String(value));
    button.querySelector('.send-label').textContent=value?'Sending your message...':'Send message';
    button.querySelector('.button-spinner').hidden=!value;button.querySelector('.send-icon').hidden=value;
    [...form.querySelectorAll('input,textarea')].forEach(el => {el.disabled=value;});
  }
  message.addEventListener('input', () => {document.querySelector('#message-count').textContent=`${message.value.length.toLocaleString()} / 5,000`;});
  form.addEventListener('input', event => clearError(event.target.name));
  form.addEventListener('change', event => clearError(event.target.name));
  async function setupCaptcha() {
    if (!config.turnstileSiteKey || captchaLoaded) return;
    captchaLoaded=true;
    const script=document.createElement('script'); script.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';script.async=true;script.defer=true;
    script.onload=() => {widgetId=window.turnstile.render('#turnstile-container', {
      sitekey:config.turnstileSiteKey, theme:document.documentElement.dataset.theme, action:'contact', size:'flexible',
      callback:token=>captchaToken=token,'expired-callback':()=>captchaToken='',
      'error-callback':()=>{captchaToken='';setStatus('The security check could not load. Please try again later.','error');},
    });};
    script.onerror=()=>{setStatus('The security check is unavailable. Please check your connection.','error');};document.head.append(script);
  }
  async function checkStatus() {
    try {
      const data=await api('/api/contact/status');
      if (!data.ready) setStatus(data.message);
      if (data.captcha_required && !config.turnstileSiteKey) setStatus('The contact security check has not been configured yet.','error');
    } catch (error) {if (!busy) setStatus(error.message);}
    setupCaptcha();
  }
  if ('IntersectionObserver' in window) {
    const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)){observer.disconnect();checkStatus();}},{rootMargin:'150px'});observer.observe(form);
  } else checkStatus();
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy || !validate()) return;
    if (Date.now()/1000-startedAt<2) {setStatus('Please review your message before sending.');return;}
    if (config.turnstileSiteKey && !captchaToken) {setStatus('Please complete the security check before sending.','error');return;}
    const payload={name:form.elements.name.value.trim(),email:form.elements.email.value.trim(),subject:form.elements.subject.value.trim(),message:message.value.trim(),consent:form.elements.consent.checked,website:form.elements.website.value,started_at:startedAt,turnstile_token:captchaToken};
    const hash=await fingerprint(payload);
    const serialized=JSON.stringify([payload.name,payload.email,payload.subject,payload.message]);
    const sameContent=(hash && lastRequest?.hash===hash) || (!hash && lastPayload===serialized);
    const id=lastRequest && sameContent?lastRequest.id:uuid();
    lastPayload=serialized;
    lastRequest={id,hash};try{sessionStorage.setItem('mae-contact-reference',JSON.stringify(lastRequest));}catch{}
    busyState(true);setStatus('Sending your enquiry…');
    try {
      const result=await api('/api/contact',{body:payload,idempotencyKey:id,timeout:55000});
      setStatus(`${result.message}\nReference: ${result.reference}`,'success');toast(result.message,'success');
      form.reset();document.querySelector('#message-count').textContent='0 / 5,000';startedAt=Date.now()/1000;
      lastRequest=null;try{sessionStorage.removeItem('mae-contact-reference');}catch{}
    } catch(error) {
      setStatus(`${error.message}${error.reference?'\nReference: '+error.reference:''}`,error.status==='uncertain'?'uncertain':'error');
      toast(error.message,'error');
      // Reuse an ID after an ambiguous connection; use a new one only when the
      // server explicitly confirms the attempt failed, or the content changes.
      if(error.status==='failed'){lastRequest=null;try{sessionStorage.removeItem('mae-contact-reference');}catch{}}
      if(error.fields) error.fields.filter(name=>['name','email','subject','message','consent'].includes(name)).forEach(name=>showError(name,'Please check this field.'));
    } finally {
      busyState(false);if(widgetId!==null && window.turnstile){window.turnstile.reset(widgetId);captchaToken='';}
    }
  });
}
