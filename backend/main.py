"""
PurrFect Spots API - Main Application


Features:
- API versioning (/api/v1/*)
- Sentry error monitoring
- Rate limiting
- CORS configuration
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncIterator

from dotenv import load_dotenv

# Explicitly load .env - Trigger reload (fix magic)
load_dotenv()


# ========== Sentry Integration ==========
from typing import Any, cast

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

# MCPIntegration removed to prevent Internal Server Errors on Vercel
from sentry_sdk.integrations.starlette import StarletteIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from config import config

# Import custom exceptions
from limiter import limiter
from logger import logger
from middleware.csrf_middleware import CSRFMiddleware
from middleware.etag_middleware import ETagMiddleware
from middleware.idempotency_middleware import IdempotencyMiddleware
from middleware.request_id_middleware import RequestIdMiddleware
from middleware.security_middleware import (
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
)
from routes.admin import router as admin_router

# Import versioned API router
from routes.api_v1 import router as api_v1_router
from routes.health import router as health_router

SENTRY_DSN = config.SENTRY_DSN
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CONTENT_TYPE_JSON = "application/json"
IS_TEST_ENV = (
    ENVIRONMENT.lower() in {"test", "testing"} or bool(os.getenv("PYTEST_CURRENT_TEST")) or "pytest" in sys.modules
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if SENTRY_DSN and not IS_TEST_ENV:

    def before_send(event: Any, hint: Any) -> Any:
        # Filter exceptions by type (when exc_info is available)
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if isinstance(exc_value, (asyncio.CancelledError, KeyboardInterrupt)):
                return None
            status_code = getattr(exc_value, "status_code", None)
            if isinstance(status_code, int) and status_code < 500:
                return None

        # Filter by log message for errors that come through without exc_info
        # (e.g., starlette lifespan shutdown, port binding conflicts)
        event_dict = cast("dict[str, Any]", event)
        message_obj = event_dict.get("logentry", {}).get("message", "") or event_dict.get("message", "")
        message = str(message_obj)
        noise_patterns = [
            "CancelledError",
            "KeyboardInterrupt",
            "error while attempting to bind on address",
            "WinError 10048",
            "Errno 10048",
            "MagicMock",
            "testclient",
            "Event loop is closed",
        ]
        if any(pattern in message for pattern in noise_patterns):
            return None

        request = cast("dict[str, Any]", event_dict.get("request", {}) or {})
        headers = cast("dict[str, Any]", request.get("headers", {}) or {})
        user_agent = str(headers.get("User-Agent", headers.get("user-agent", "")))
        url = str(request.get("url", ""))
        if "testclient" in user_agent.lower() or url.startswith("http://test"):
            return None

        # Filter known synthetic test IDs and mock failures that should never
        # pollute real project monitoring.
        serialized_event = str(event)
        if "00000000-0000-4000-" in serialized_event or "MagicMock" in serialized_event:
            return None

        # SEC-04: Strip PII and sensitive tokens from Sentry reports
        # 1. Strip sensitive headers
        if "headers" in request:
            sensitive_headers = {"authorization", "cookie", "set-cookie", "x-csrf-token", "x-api-key"}
            request["headers"] = {
                k: ("[REDACTED]" if k.lower() in sensitive_headers else v) for k, v in request["headers"].items()
            }

        # 2. Strip sensitive user data
        if "user" in event_dict:
            user = cast("dict[str, Any]", event_dict["user"])
            for field in ["email", "ip_address", "username"]:
                if field in user:
                    user[field] = "[REDACTED]"

        # 3. Scrub breadcrumbs (e.g. SQL queries or API calls that might have PII)
        if "breadcrumbs" in event_dict:
            breadcrumbs = cast("dict[str, Any]", event_dict["breadcrumbs"])
            for breadcrumb in cast("list[dict[str, Any]]", breadcrumbs.get("values", [])):
                if breadcrumb.get("category") in ("query", "http"):
                    data = cast("dict[str, Any]", breadcrumb.get("data", {}))
                    if "query" in data:
                        # Basic SQL redaction - can be improved but good start
                        data["query"] = "[REDACTED_QUERY]"
                    if "url" in data:
                        # Remove query params from URLs in breadcrumbs
                        url_parts = str(data["url"]).split("?")
                        if len(url_parts) > 1:
                            data["url"] = url_parts[0] + "?[REDACTED_PARAMS]"

        return event

    sentry_integrations = [
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ]

    # MCPIntegration removed to prevent Internal Server Errors on Vercel

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=sentry_integrations,
        # Performance monitoring
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        # Profiling (requires additional setup)
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        # Default PII capture should remain opt-in.
        send_default_pii=_env_flag("SENTRY_SEND_DEFAULT_PII", default=False),
        # Enable Sentry Logs (required for MCP Insights logs tab)
        enable_logs=True,
        # Enable breadcrumbs
        max_breadcrumbs=50,
        # Attach stack traces for non-exception events
        attach_stacktrace=True,
        # Filter out CancelledError and KeyboardInterrupt
        before_send=before_send,
    )
    logger.info(f"Sentry initialized for environment: {ENVIRONMENT}")
else:
    logger.warning("SENTRY_DSN not configured or test environment detected - error monitoring disabled")

# ========== API Metadata ==========
tags_metadata = [
    {
        "name": "Manual Authentication",
        "description": "Operations for traditional email/password login and registration.",
    },
    {
        "name": "Google Authentication",
        "description": "OAuth2 authentication with Google.",
    },
    {
        "name": "Profile",
        "description": "User profile management operations.",
    },
    {
        "name": "Upload",
        "description": "Image upload and processing.",
    },
    {
        "name": "Cat Detection",
        "description": "AI-powered cat detection and analysis.",
    },
    {
        "name": "Gallery",
        "description": "Public gallery and location data access.",
    },
]


# Import telemetry setup
# ========== Background Tasks ==========
from contextlib import asynccontextmanager

from tasks.cleanup_tasks import start_cleanup_jobs, stop_cleanup_jobs
from utils.http_client import close_shared_httpx_client
from utils.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await start_cleanup_jobs()
    yield
    await stop_cleanup_jobs()
    await close_shared_httpx_client()


# ========== FastAPI Application ==========
# SECURITY: In production, disable OpenAPI docs to prevent information disclosure
if ENVIRONMENT == "production":
    app = FastAPI(
        lifespan=lifespan,
        title="PurrFect Spots API",
        description="""
        PurrFect Spots API helps you share and discover cat locations in a socially-connected way.

        ### 🌐 API Specification
        All endpoints follow the `/api/v1/` prefix convention for stable identification.

        ### ✨ Key Features
        * 📍 **Geo-Location Awareness**: High-precision cat spot sharing with privacy protection.
        * 🤳 **AI Photo Intelligence**: Automated cat detection and visual attribute extraction.
        * 🔒 **Enterprise-Grade Security**: PKCE-enabled OAuth 2.0 and Supabase-backed authentication.
        * ⚡ **Performance Optimized**: Built-in rate limiting, GZip compression, and ETag support.
        * 🔄 **Real-time Ready**: Designed for low-latency interactions and live updates.
        """,
        version="3.1.0",
        docs_url=None,  # SECURITY: Disabled in production
        redoc_url=None,  # SECURITY: Disabled in production
        openapi_url=None,  # SECURITY: Disabled in production
        default_response_class=JSONResponse,
        contact={
            "name": "Purrfect Spots Team",
            "email": "support@purrfectspots.com",
        },
        license_info={
            "name": "MIT",
        },
        openapi_tags=tags_metadata,
    )
    logger.warning("OpenAPI docs disabled in production environment")
else:
    app = FastAPI(
        lifespan=lifespan,
        title="PurrFect Spots API",
        description="""
        PurrFect Spots API helps you share and discover cat locations in a socially-connected way.

        ### 🌐 API Specification
        All endpoints follow the `/api/v1/` prefix convention for stable identification.

        ### ✨ Key Features
        * 📍 **Geo-Location Awareness**: High-precision cat spot sharing with privacy protection.
        * 🤳 **AI Photo Intelligence**: Automated cat detection and visual attribute extraction.
        * 🔒 **Enterprise-Grade Security**: PKCE-enabled OAuth 2.0 and Supabase-backed authentication.
        * ⚡ **Performance Optimized**: Built-in rate limiting, GZip compression, and ETag support.
        * 🔄 **Real-time Ready**: Designed for low-latency interactions and live updates.
        """,
        version="3.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=JSONResponse,
        contact={
            "name": "Purrfect Spots Team",
            "email": "support@purrfectspots.com",
        },
        license_info={
            "name": "MIT",
        },
        openapi_tags=tags_metadata,
    )

# Initialize Telemetry (OpenTelemetry)
setup_telemetry(app)

# (Background tasks are now managed by lifespan)


# ========== Rate Limiter ==========
from starlette.types import ExceptionHandler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(ExceptionHandler, _rate_limit_exceeded_handler))

# ========== Exception Handlers ==========

from starlette.types import ExceptionHandler

from utils.exception_handlers import (
    custom_http_exception_handler,
    generic_exception_handler,
    purrfect_spots_exception_handler,
    validation_exception_handler,
)
from utils.exceptions import PurrfectSpotsException


def cancelled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.info(f"Operation cancelled: {request.url.path}")
    return JSONResponse(status_code=499, content={"detail": "Request cancelled"})


def keyboard_interrupt_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.info("Server shutting down...")
    return JSONResponse(status_code=503, content={"detail": "Service shutting down"})


app.add_exception_handler(PurrfectSpotsException, cast(ExceptionHandler, purrfect_spots_exception_handler))
app.add_exception_handler(Exception, cast(ExceptionHandler, generic_exception_handler))
app.add_exception_handler(StarletteHTTPException, cast(ExceptionHandler, custom_http_exception_handler))
app.add_exception_handler(RequestValidationError, cast(ExceptionHandler, validation_exception_handler))
# import asyncio
# app.add_exception_handler(asyncio.CancelledError, cast(ExceptionHandler, cancelled_error_handler))


# ========== CORS Configuration (applied after all other middleware below) ==========
allowed_origins = config.get_allowed_origins()
logger.info(f"CORS allowed origins: {allowed_origins}")


# ========== Health Check Endpoints ==========
@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "version": "3.1.0",
            "api_versions": ["v1"],
        },
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )


@app.get("/health")
async def health_check() -> JSONResponse:
    """Simple health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "sentry_enabled": bool(SENTRY_DSN),
        },
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )


# ========== Favicon Routes (to prevent 404 noise) ==========
@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon() -> Response:
    """Handle favicon requests to prevent 404 security event logs."""
    return Response(status_code=204)


# Test endpoint removed for security


# ========== API Routes ==========
# Include versioned API router (recommended)
# We ensure the routers are included with correct prefixes
app.include_router(api_v1_router)  # This has /api/v1 prefix in api_v1.py
app.include_router(admin_router, prefix="/api/v1")  # Admin is separate

# Include health check routes (no prefix, accessible at /health/*)
app.include_router(health_router)

# ========== Security Middleware ==========
# Order matters: First added = Last executed
# Execution order: GZip -> RequestId -> Idempotency -> ETag -> CSRF -> SecurityHeaders -> HTTPSRedirect

# HTTPS redirect (must be added last to run first)
app.add_middleware(HTTPSRedirectMiddleware)

# Trust X-Forwarded-For headers from proxies (e.g. AWS LB, Vercel)
# Only explicitly trusted proxies may rewrite client IP information
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=config.get_trusted_proxy_hosts(),
)

# Security headers (CSP, HSTS, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CSRF protection for state-changing requests
app.add_middleware(CSRFMiddleware)

# ETag support for conditional GET requests (304 Not Modified)
# SECURITY: Enable in production for performance, disable in dev for easier debugging
if ENVIRONMENT != "development":
    app.add_middleware(ETagMiddleware)

# Idempotency key support for POST operations
app.add_middleware(IdempotencyMiddleware)

# Request ID for tracing and audit logs
app.add_middleware(RequestIdMiddleware)

# ========== Compression ==========

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ========== CORS Middleware (MUST BE LAST - outermost layer) ==========
# IMPORTANT: In Starlette/FastAPI, the LAST middleware added is the OUTERMOST.
# CORS must be outermost so it can add Access-Control-Allow-Origin headers
# to ALL responses, including error responses from inner middleware like CSRF.
# If CORS is not outermost, errors from inner middleware (like 403 Forbidden)
# will be returned WITHOUT CORS headers, causing browser to block them.
#
# SECURITY REVIEW: CORS Configuration
# allow_credentials=True is necessary for authentication cookies (refresh_token)
# allow_origins MUST be a restricted list when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Pragma",
        "X-CSRF-Token",
        "X-Api-Version",
        "Accept-Version",
        "Content-MD5",
    ],
    expose_headers=[
        "Content-Range",
        "X-Content-Range",
        "X-Request-ID",
        "X-CSRF-Token",
        "Content-Length",
        "Content-Type",
    ],
    max_age=86400,
)

# Vercel expects this to be available


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
# triggering reload
