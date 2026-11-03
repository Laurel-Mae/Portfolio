"""Atomic idempotency and rate limits, shared across processes via SQL."""
from __future__ import annotations
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from server.core.config import Settings


class RateLimited(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


class IdempotencyConflict(Exception):
    pass


class Store:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sqlite = settings.database_driver == "sqlite"
        if self.sqlite and not settings.production:
            settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            schema = Path(__file__).resolve().parents[2] / "database/schema.sql"
            with sqlite3.connect(settings.sqlite_path) as db:
                db.executescript(schema.read_text())

    @contextmanager
    def connect(self):
        if self.sqlite:
            if self.settings.production:
                raise RuntimeError("Production requires shared storage.")
            conn = sqlite3.connect(self.settings.sqlite_path, timeout=5, isolation_level=None)
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("BEGIN IMMEDIATE")
        else:
            import psycopg
            conn = psycopg.connect(self.settings.database_url, connect_timeout=5,
                                   prepare_threshold=None, sslmode="require")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, conn, statement: str, params: tuple = ()):
        return conn.execute(statement if self.sqlite else statement.replace("?", "%s"), params)

    def claim(self, request_id: str, fingerprint: str, client_hash: str) -> str:
        now = int(time.time())
        with self.connect() as db:
            self.execute(db, "DELETE FROM contact_requests WHERE updated_at < ?",
                         (now - self.settings.retention_days * 86400,))
            self.execute(db, "DELETE FROM contact_rate_limits WHERE expires_at < ?", (now,))
            row = self.execute(db, "SELECT fingerprint, status FROM contact_requests WHERE request_id = ?",
                               (request_id,)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise IdempotencyConflict()
                return row[1]
            # Both per-client and global counters are atomically incremented.
            for label, window, limit in [
                (client_hash, self.settings.rate_window, self.settings.rate_limit),
                ("global", 86400, self.settings.global_daily_limit),
            ]:
                bucket = now // window
                expiry = (bucket + 1) * window
                key = f"{label}:{bucket}:{window}"
                count = self.execute(db,
                    "INSERT INTO contact_rate_limits(bucket_key, attempts, expires_at) VALUES (?, 1, ?) "
                    "ON CONFLICT(bucket_key) DO UPDATE SET attempts = contact_rate_limits.attempts + 1 RETURNING attempts",
                    (key, expiry)).fetchone()[0]
                if count > limit:
                    raise RateLimited(max(1, expiry - now))
            inserted = self.execute(db,
                "INSERT INTO contact_requests(request_id, fingerprint, status, created_at, updated_at) "
                "VALUES (?, ?, 'pending', ?, ?) ON CONFLICT(request_id) DO NOTHING RETURNING request_id",
                (request_id, fingerprint, now, now)).fetchone()
            if inserted:
                return "new"
            row = self.execute(db, "SELECT fingerprint, status FROM contact_requests WHERE request_id = ?", (request_id,)).fetchone()
            if row[0] != fingerprint:
                raise IdempotencyConflict()
            return row[1]

    def finish(self, request_id: str, status: str) -> None:
        if status not in {"accepted", "failed", "uncertain"}:
            raise ValueError("Invalid delivery state")
        with self.connect() as db:
            self.execute(db, "UPDATE contact_requests SET status = ?, updated_at = ? WHERE request_id = ?",
                         (status, int(time.time()), request_id))
