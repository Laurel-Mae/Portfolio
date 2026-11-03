-- Run once in the Supabase SQL Editor, then set the SERVER connection URI.
-- Browser roles receive no privileges and no RLS policies. Server uses SQL.
CREATE TABLE IF NOT EXISTS public.contact_requests (
    request_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'failed', 'uncertain')),
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS contact_requests_updated ON public.contact_requests(updated_at);
CREATE TABLE IF NOT EXISTS public.contact_rate_limits (
    bucket_key TEXT PRIMARY KEY,
    attempts INTEGER NOT NULL DEFAULT 1,
    expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS contact_rate_expiry ON public.contact_rate_limits(expires_at);
ALTER TABLE public.contact_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contact_rate_limits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.contact_requests FROM anon, authenticated;
REVOKE ALL ON public.contact_rate_limits FROM anon, authenticated;
-- Use an appropriately privileged server-side SQL login only. Never ship this
-- URI, database password, or a Supabase service-role key in client configuration.
