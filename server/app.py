"""App factory for testing, Uvicorn, Render, and Vercel."""
from __future__ import annotations
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from server.core.config import Settings, load_settings
from server.database.store import Store
from server.services.email_service import EmailService
from server.api.contact import router


def create_app(settings: Settings | None = None, mailer=None, store=None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Mae Ann Laurel Portfolio API", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    # In production, no ephemeral SQLite store is ever initialized.
    app.state.store = store or Store(settings)
    app.state.mailer = mailer or EmailService(settings)


    @app.middleware("http")
    async def request_safety(request: Request, call_next):
        if request.method == "POST":
            if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                return JSONResponse({"message": "Use a JSON request."}, status_code=415)
            # Stream with an actual bound, including chunked requests without a length.
            parts = []; size = 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 32768:
                    return JSONResponse({"message": "Your message is too large."}, status_code=413)
                parts.append(chunk)
            request._body = b"".join(parts)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Do not echo raw validation inputs (which may contain personal content).
        return JSONResponse({"message": "Please check your name, email, subject and message.",
                             "fields": sorted({str(x["loc"][-1]) for x in exc.errors()})}, status_code=422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse({"message": str(exc.detail)}, status_code=exc.status_code, headers=exc.headers)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "portfolio-contact"}

    app.include_router(router)
    if settings.readiness_error:
        logging.getLogger("portfolio").warning("Contact setup: %s", settings.readiness_error)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                       allow_methods=["GET", "POST", "OPTIONS"],
                       allow_headers=["Content-Type", "Idempotency-Key"],
                       expose_headers=["Retry-After"], allow_credentials=False, max_age=600)
    return app
