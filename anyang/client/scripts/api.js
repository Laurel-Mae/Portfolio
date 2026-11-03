export const config = window.PORTFOLIO_CONFIG || {apiBaseUrl:'',siteUrl:'',turnstileSiteKey:''};
export async function api(path, {body, idempotencyKey, timeout = 12000} = {}) {
  if (!config.apiBaseUrl) throw new Error('The contact service is not connected yet.');
  const controller = new AbortController(), timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(`${config.apiBaseUrl.replace(/\/$/,'')}${path}`, {
      method:body ? 'POST' : 'GET', credentials:'omit', mode:'cors', cache:'no-store', signal:controller.signal,
      headers:body ? {'Content-Type':'application/json', 'Idempotency-Key':idempotencyKey} : {},
      ...(body ? {body:JSON.stringify(body)} : {}),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.message || 'The contact service could not complete this request.');
      error.status = data.status; error.reference = data.reference; error.code = response.status;
      error.fields = data.fields; error.retryAfter = response.headers.get('Retry-After'); throw error;
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      const uncertain = new Error(body ? 'The connection timed out. Delivery may still be in progress. Please do not send a new message yet.' : 'The contact service is taking longer than expected.');
      uncertain.status = body ? 'uncertain' : 'offline'; uncertain.reference = idempotencyKey; throw uncertain;
    }
    if (error instanceof TypeError) {
      const offline = new Error(body ? 'The connection was interrupted. Delivery could not be confirmed. Keep this reference before retrying.' : 'The contact service is unavailable at the moment.');
      offline.status = body ? 'uncertain' : 'offline'; offline.reference = idempotencyKey; throw offline;
    }
    throw error;
  } finally {clearTimeout(timer);}
}
