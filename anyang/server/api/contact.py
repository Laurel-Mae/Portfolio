from __future__ import annotations
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import time
from uuid import UUID
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from server.database.store import RateLimited, IdempotencyConflict

router = APIRouter(prefix="/api")
log = logging.getLogger("portfolio.contact")


class ContactPayload(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=254)
    subject: str = Field(min_length=3, max_length=140)
    message: str = Field(min_length=10, max_length=5000)
    consent: bool
    website: str = Field(default="", max_length=200)  # Honeypot
    started_at: float
    turnstile_token: str = Field(default="", max_length=2048)

    @field_validator("name", "subject", mode="before")
    @classmethod
    def clean_header(cls, value):
        if isinstance(value, str):
            if any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError("Line breaks and control characters are not allowed here.")
            return value.strip()
        return value

    @field_validator("message", mode="before")
    @classmethod
    def clean_body(cls, value):
        if isinstance(value, str):
            if "\x00" in value:
                raise ValueError("Invalid message character.")
            return value.strip()
        return value


def ip_for(request: Request) -> str:
    settings = request.app.state.settings
    ip = request.client.host if request.client else "unknown"
    if settings.trust_proxy:
        # Only opt in when the ingress removes spoofable client-supplied headers.
        header = "x-vercel-forwarded-for" if os.environ.get("VERCEL") == "1" else "x-forwarded-for"
        candidate = request.headers.get(header, "")
        if candidate:
            ip = candidate.split(",")[0].strip()
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return "unknown"


def digest(settings, value: str) -> str:
    return hmac.new(settings.hmac_key.encode(), value.encode(), hashlib.sha256).hexdigest()


def outcome(state: str, request_id: str):
    responses = {
        "accepted": (200, "Your message was accepted for delivery. Thank you for reaching out."),
        "pending": (409, "This message is already being processed. Do not resend it yet."),
        "uncertain": (409, "Delivery could not be confirmed. Please do not resend yet; keep this reference."),
        "failed": (503, "Email delivery is temporarily unavailable. Your message has not been confirmed as sent."),
    }
    status, message = responses[state]
    return JSONResponse({"status": state, "message": message, "reference": request_id}, status_code=status)


@router.get("/contact/status")
def contact_status(request: Request):
    settings = request.app.state.settings
    return {"ready": settings.contact_ready,
            "captcha_required": bool(settings.turnstile_secret) or settings.turnstile_required,
            "message": "Ready to receive your message." if settings.contact_ready else "Email delivery is not connected yet."}


@router.post("/contact")
def submit(payload: ContactPayload, request: Request):
    settings = request.app.state.settings
    if not settings.contact_ready:
        raise HTTPException(503, "Email delivery is not connected yet. Please use another listed contact method.")
    origin = request.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        raise HTTPException(403, "This website is not allowed to submit messages.")
    if not payload.consent:
        raise HTTPException(422, "Please agree to use your details to respond to this enquiry.")
    if payload.website or not (2 <= time.time() - payload.started_at <= 86400):
        raise HTTPException(400, "Please wait a moment and try again, or refresh a form left open for a long time.")
    raw_id = request.headers.get("idempotency-key", "")
    try:
        request_id = str(UUID(raw_id))
    except (ValueError, AttributeError):
        raise HTTPException(400, "A valid request reference is required.")
    ip = ip_for(request)
    if settings.turnstile_secret or settings.turnstile_required:
        if not payload.turnstile_token:
            raise HTTPException(400, "Please complete the security check.")
        try:
            verification = httpx.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data={
                "secret": settings.turnstile_secret, "response": payload.turnstile_token,
                "remoteip": ip if ip != "unknown" else "", "idempotency_key": request_id,
            }, timeout=6).json()
        except Exception:
            raise HTTPException(503, "The security check is unavailable. Please try again later.")
        if not verification.get("success") or verification.get("action") != "contact":
            raise HTTPException(400, "The security check expired. Please complete it again.")
        if settings.turnstile_hostnames and verification.get("hostname") not in settings.turnstile_hostnames:
            raise HTTPException(400, "The security check did not match this website.")
    content = payload.model_dump(include={"name", "email", "subject", "message"})
    fingerprint = digest(settings, json.dumps(content, ensure_ascii=False, sort_keys=True))
    try:
        state = request.app.state.store.claim(request_id, fingerprint, digest(settings, ip))
    except RateLimited as exc:
        return JSONResponse({"message": "Too many enquiries. Please try again later.", "status": "rate_limited"},
                            status_code=429, headers={"Retry-After": str(exc.retry_after)})
    except IdempotencyConflict:
        raise HTTPException(409, "This reference belongs to a different message. Refresh the form before submitting.")
    except Exception:
        log.error("Contact storage unavailable")
        raise HTTPException(503, "The contact service is temporarily unavailable. No new email was sent.")
    if state != "new":
        return outcome(state, request_id)
    try:
        result = request.app.state.mailer.send(content, request_id)
        state = result.status
    except Exception:
        # An unexpected transport failure is not proof that delivery failed.
        state = "uncertain"
        log.error("Unexpected email failure reference=%s", request_id)
    try:
        request.app.state.store.finish(request_id, state)
    except Exception:
        # A pending row will prevent duplicate sends if a write fails after SMTP.
        log.error("Could not record delivery state reference=%s", request_id)
    return outcome(state, request_id)
