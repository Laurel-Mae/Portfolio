"""Explicit, validated configuration. No private value is sent to the client."""
from __future__ import annotations
import csv
import json
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from dotenv import dotenv_values
from email_validator import validate_email, EmailNotValidError

ROOT = Path(__file__).resolve().parents[1]


def split_csv(value: str) -> list[str]:
    if not value.strip():
        return []
    return [part.strip() for part in next(csv.reader([value], skipinitialspace=True))]


def boolean(value: str) -> bool:
    return value.lower().strip() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SMTPAccount:
    host: str
    port: int
    security: str
    user: str
    password: str = field(repr=False)


@dataclass
class Settings:
    environment: str = "development"
    allowed_origins: list[str] = field(default_factory=lambda: ["http://127.0.0.1:3000", "http://localhost:3000"])
    database_driver: str = "sqlite"
    sqlite_path: Path = ROOT.parent / "database/database.db"
    database_url: str = field(default="", repr=False)
    hmac_key: str = field(default="", repr=False)
    contact_to: str = ""
    sender_name: str = "Mae Ann Laurel - Portfolio"
    accounts: list[SMTPAccount] = field(default_factory=list, repr=False)
    smtp_timeout: float = 5.0
    smtp_budget: float = 24.0
    rate_limit: int = 5
    rate_window: int = 900
    global_daily_limit: int = 60
    retention_days: int = 7
    trust_proxy: bool = False
    turnstile_secret: str = field(default="", repr=False)
    turnstile_hostnames: list[str] = field(default_factory=list)
    turnstile_required: bool = False
    configuration_error: str = ""

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def contact_ready(self) -> bool:
        return not self.readiness_error

    @property
    def readiness_error(self) -> str:
        if self.configuration_error:
            return self.configuration_error
        if not self.accounts or not self.contact_to:
            return "SMTP sender accounts and CONTACT_TO have not been configured."
        if self.database_driver == "postgres" and not self.database_url:
            return "PostgreSQL requires a private DATABASE_URL."
        if self.production and (self.database_driver != "postgres" or not self.database_url):
            return "Production contact delivery requires shared PostgreSQL storage."
        if self.production and len(self.hmac_key) < 32:
            return "Production requires a private CONTACT_HMAC_KEY of at least 32 characters."
        if self.turnstile_required and not self.turnstile_secret:
            return "Turnstile is required but its secret is missing."
        return ""


def _accounts(values: dict[str, str]) -> list[SMTPAccount]:
    raw = values.get("SMTP_ACCOUNTS_JSON", "").strip()
    if raw:
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("SMTP_ACCOUNTS_JSON must be a JSON array.")
        result = [SMTPAccount(host=str(x["host"]), port=int(x.get("port", 587)),
                              security=str(x.get("security", "starttls")).lower(),
                              user=str(x["user"]), password=str(x["password"])) for x in rows]
    else:
        users = split_csv(values.get("SMTP_USER", ""))
        passwords = split_csv(values.get("SMTP_PASS", ""))
        if not users and not passwords:
            return []
        if len(users) != len(passwords):
            raise ValueError("SMTP_USER and SMTP_PASS must have matching counts.")
        count = len(users)
        def column(key: str, default: str) -> list[str]:
            items = split_csv(values.get(key, default))
            if len(items) == 1:
                return items * count
            if len(items) != count:
                raise ValueError(f"{key} needs one shared value or one value per account.")
            return items
        hosts = column("SMTP_HOST", "smtp.gmail.com")
        ports = column("SMTP_PORT", "587")
        security = column("SMTP_SECURITY", "starttls")
        result = [SMTPAccount(h, int(p), s.lower(), u, password)
                  for h, p, s, u, password in zip(hosts, ports, security, users, passwords)]
    if not 1 <= len(result) <= 5:
        raise ValueError("Configure between one and five SMTP accounts.")
    for item in result:
        validate_email(item.user, check_deliverability=False)
        if not item.password or not item.host or any(c.isspace() for c in item.host):
            raise ValueError("Each SMTP account needs a valid host and nonempty credentials.")
        if item.port not in {465, 587, 2525} or item.security not in {"tls", "starttls"}:
            raise ValueError("Use authenticated TLS/STARTTLS on port 465, 587, or 2525.")
    return result


def load_settings() -> Settings:
    project = ROOT.parent
    values = {**dotenv_values(project / ".env"), **dotenv_values(ROOT / ".env"), **os.environ}
    values = {key: str(value or "") for key, value in values.items()}
    env = values.get("APP_ENV", "development").lower()
    # Hosted services are production unless explicitly configured otherwise.
    if values.get("VERCEL") == "1" or values.get("RENDER") == "true":
        env = "production"
    origin_values = split_csv(values.get("ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000"))
    errors = []
    for origin in origin_values:
        p = urlparse(origin)
        if p.scheme not in {"https", "http"} or not p.netloc or p.path not in {"", "/"} or p.query or p.fragment:
            errors.append("ALLOWED_ORIGINS must contain exact HTTP(S) origins, not wildcards.")
    origin_values = [origin.rstrip("/") for origin in origin_values]
    try:
        accounts = _accounts(values)
    except (ValueError, KeyError, TypeError, EmailNotValidError):
        accounts = []
        errors.append("Invalid SMTP configuration. Check account counts, addresses, ports and security.")
    contact_to = values.get("CONTACT_TO", "").strip()
    if contact_to:
        try:
            contact_to = validate_email(contact_to, check_deliverability=False).normalized
        except EmailNotValidError:
            errors.append("CONTACT_TO must be one valid recipient email address.")
    db_driver = values.get("DATABASE_DRIVER", "sqlite").lower()
    if db_driver not in {"sqlite", "postgres"}:
        errors.append("DATABASE_DRIVER must be sqlite or postgres.")
    sqlite_path = Path(values.get("SQLITE_PATH", "database/database.db"))
    if not sqlite_path.is_absolute():
        sqlite_path = project / sqlite_path
    key = values.get("CONTACT_HMAC_KEY", "")
    if not key and env != "production":
        secret_file = project / "database/.contact-key"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as handle:
                handle.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        key = secret_file.read_text().strip()
    def number(key_name: str, default: float, minimum: float, maximum: float) -> float:
        try:
            return max(minimum, min(maximum, float(values.get(key_name, str(default)))))
        except ValueError:
            errors.append(f"{key_name} must be numeric.")
            return default
    result = Settings(
        environment=env, allowed_origins=origin_values, database_driver=db_driver,
        sqlite_path=sqlite_path, database_url=values.get("DATABASE_URL", ""),
        hmac_key=key, contact_to=contact_to,
        sender_name=values.get("CONTACT_SENDER_NAME", "Mae Ann Laurel - Portfolio"),
        accounts=accounts, smtp_timeout=number("SMTP_TIMEOUT_SECONDS", 5, 1, 8),
        smtp_budget=number("SMTP_TOTAL_BUDGET_SECONDS", 24, 5, 35),
        rate_limit=int(number("CONTACT_RATE_LIMIT", 5, 1, 20)),
        rate_window=int(number("CONTACT_RATE_WINDOW_SECONDS", 900, 60, 86400)),
        global_daily_limit=int(number("CONTACT_GLOBAL_DAILY_LIMIT", 60, 1, 500)),
        retention_days=int(number("CONTACT_RETENTION_DAYS", 7, 1, 30)),
        trust_proxy=boolean(values.get("TRUST_PROXY_HEADERS", "false")),
        turnstile_secret=values.get("TURNSTILE_SECRET_KEY", ""),
        turnstile_hostnames=split_csv(values.get("TURNSTILE_ALLOWED_HOSTNAMES", "")),
        turnstile_required=boolean(values.get("TURNSTILE_REQUIRED", "false")),
    )
    if "\r" in result.sender_name or "\n" in result.sender_name:
        errors.append("Sender name cannot contain line breaks.")
    result.configuration_error = " ".join(errors)
    return result
