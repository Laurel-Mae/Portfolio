-- SQLite development schema. No visitor names, addresses or messages stored.
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS contact_requests (
    request_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'failed', 'uncertain')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS contact_requests_updated ON contact_requests(updated_at);
CREATE TABLE IF NOT EXISTS contact_rate_limits (
    bucket_key TEXT PRIMARY KEY,
    attempts INTEGER NOT NULL DEFAULT 1,
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS contact_rate_expiry ON contact_rate_limits(expires_at);
