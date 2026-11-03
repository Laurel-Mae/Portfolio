"""Sequential SMTP failover. Never retry a possibly accepted DATA transfer."""
from __future__ import annotations
import logging
import re
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formataddr, formatdate
from server.core.config import Settings, SMTPAccount

log = logging.getLogger("portfolio.mail")


@dataclass(frozen=True)
class DeliveryResult:
    status: str  # accepted | failed | uncertain
    attempts: int


def build_message(account: SMTPAccount, settings: Settings, payload: dict, request_id: str) -> EmailMessage:
    message = EmailMessage(policy=SMTP)
    message["From"] = formataddr((settings.sender_name, account.user))
    message["To"] = settings.contact_to
    message["Reply-To"] = payload["email"]
    message["Subject"] = "[Portfolio] " + payload["subject"]
    message["Date"] = formatdate(localtime=False)
    # Keep the same ID for all attempts in this request. This is not a delivery guarantee.
    message["Message-ID"] = f"<{request_id}@portfolio.invalid>"
    message.set_content(
        "A new portfolio enquiry\n\n"
        f"Name: {payload['name']}\nEmail: {payload['email']}\nSubject: {payload['subject']}\n\n"
        f"{payload['message']}\n\nReference: {request_id}\n"
        "Reply to this message to contact the visitor.\n",
        charset="utf-8", cte="quoted-printable",
    )
    return message


class EmailService:
    def __init__(self, settings: Settings, smtp_factory=None, ssl_factory=None):
        self.settings = settings
        self.smtp_factory = smtp_factory or smtplib.SMTP
        self.ssl_factory = ssl_factory or smtplib.SMTP_SSL

    def send(self, payload: dict, request_id: str) -> DeliveryResult:
        deadline = time.monotonic() + self.settings.smtp_budget
        attempts = 0
        for index, account in enumerate(self.settings.accounts):
            if time.monotonic() >= deadline:
                break
            attempts += 1
            smtp = None
            data_started = False
            accepted = False
            def budget():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("SMTP time budget exceeded")
                timeout = min(self.settings.smtp_timeout, remaining)
                if smtp is not None and getattr(smtp, "sock", None) is not None:
                    smtp.sock.settimeout(timeout)
                return timeout
            try:
                context = ssl.create_default_context()
                if account.security == "tls":
                    smtp = self.ssl_factory(account.host, account.port, timeout=budget(), context=context)
                else:
                    smtp = self.smtp_factory(account.host, account.port, timeout=budget())
                budget(); smtp.ehlo()
                if account.security == "starttls":
                    budget(); smtp.starttls(context=context)
                    budget(); smtp.ehlo()
                budget(); smtp.login(account.user, account.password)
                budget(); code, reply = smtp.mail(account.user)
                if code != 250:
                    raise smtplib.SMTPSenderRefused(code, reply, account.user)
                budget(); code, reply = smtp.rcpt(self.settings.contact_to)
                if code not in {250, 251}:
                    # A permanently rejected recipient will not be fixed by trying
                    # more senders. Temporary rejections may safely fail over.
                    if 500 <= code < 600:
                        return DeliveryResult("failed", attempts)
                    raise smtplib.SMTPResponseException(code, reply)
                budget(); code, reply = smtp.docmd("DATA")
                if code != 354:
                    raise smtplib.SMTPDataError(code, reply)
                data = build_message(account, self.settings, payload, request_id).as_bytes()
                data = re.sub(br"(?m)^\.", b"..", data)
                if not data.endswith(b"\r\n"):
                    data += b"\r\n"
                # From here a broken connection is ambiguous: NEVER send again
                # via another account without reconciling with the provider.
                data_started = True
                budget(); smtp.send(data + b".\r\n")
                budget(); code, reply = smtp.getreply()
                if code != 250:
                    data_started = False  # An explicit rejection is safe to retry.
                    raise smtplib.SMTPDataError(code, reply)
                accepted = True
                return DeliveryResult("accepted", attempts)
            except (smtplib.SMTPException, OSError, TimeoutError, UnicodeError, ValueError) as exc:
                # Log type and position only; never credentials or visitor contents.
                log.warning("SMTP account_index=%s failure=%s", index + 1, type(exc).__name__)
                if data_started:
                    return DeliveryResult("uncertain", attempts)
            finally:
                if smtp is not None:
                    # QUIT is not part of message acceptance. Closing safely must
                    # not turn an already accepted message into another send.
                    try:
                        smtp.close()
                    except Exception:
                        pass
        return DeliveryResult("failed", attempts)
