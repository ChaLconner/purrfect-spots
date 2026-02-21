"""
PurrFect Spots API - Main Application


Features:
- API versioning (/api/v1/*)
- Sentry error monitoring
- Rate limiting
- CORS configuration
"""

import asyncio
import os

from dotenv import load_dotenv

# Explicitly load .env - Trigger reload (fix magic)
load_dotenv()


# ========== Sentry Integration ==========
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.mcp import MCPIntegration
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

if SENTRY_DSN:
    from sentry_sdk.types import Event, Hint

    def before_send(event: Event, hint: Hint) -> Event | None:
        # Filter exceptions by type (when exc_info is available)
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if isinstance(exc_value, (asyncio.CancelledError, KeyboardInterrupt)):
                return None

        # Filter by log message for errors that come through without exc_info
        # (e.g., starlette lifespan shutdown, port binding conflicts)
        message_obj = event.get("logentry", {}).get("message", "") or event.get("message", "")
        message = str(message_obj)
        noise_patterns = [
            "CancelledError",
            "KeyboardInterrupt",
            "error while attempting to bind on address",
            "WinError 10048",
            "Errno 10048",
        ]
        if any(pattern in message for pattern in noise_patterns):
            return None

        return event

    sentry_integrations = [
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
        MCPIntegration(
            # Set include_prompts=False to exclude tool inputs/outputs from Sentry
            # (useful if they contain PII). Default is True.
            include_prompts=True,
        ),
    ]

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=sentry_integrations,
        # Performance monitoring
        traces_sample_rate=1.0,
        # Profiling (requires additional setup)
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        # Send user info for debugging
        send_default_pii=True,
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
    logger.warning("SENTRY_DSN not configured - error monitoring disabled")

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
from utils.telemetry import setup_telemetry

# ========== FastAPI Application ==========
# SECURITY: In production, disable OpenAPI docs to prevent information disclosure
if ENVIRONMENT == "production":
    app = FastAPI(
        title="PurrFect Spots API",
        description="""
        PurrFect Spots API helps you share and discover cat locations.
        
        ## API Versioning
        All endpoints are available under `/api/v1/` prefix.
        Legacy routes (without prefix) are maintained for backward compatibility.
        
        ## Features
        * 📍 **Share Locations**: Upload photos of cats and their locations.
        * 🤖 **AI Detection**: Automatically detect cats in uploaded photos.
        * 🔐 **Authentication**: Secure login via Email/Password or Google OAuth.
        * 📊 **Pagination**: API-side pagination for efficient data loading.
        """,
        version="3.0.0",
        docs_url=None,  # SECURITY: Disabled in production
        redoc_url=None,  # SECURITY: Disabled in production
        openapi_url=None,  # SECURITY: Disabled in production
        default_response_class=ORJSONResponse,
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
        title="PurrFect Spots API",
        description="""
        PurrFect Spots API helps you share and discover cat locations.
        
        ## API Versioning
        All endpoints are available under `/api/v1/` prefix.
        Legacy routes (without prefix) are maintained for backward compatibility.
        
        ## Features
        * 📍 **Share Locations**: Upload photos of cats and their locations.
        * 🤖 **AI Detection**: Automatically detect cats in uploaded photos.
        * 🔐 **Authentication**: Secure login via Email/Password or Google OAuth.
        * 📊 **Pagination**: API-side pagination for efficient data loading.
        """,
        version="3.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
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

# ========== Background Tasks ==========
from tasks.cleanup_tasks import start_cleanup_jobs, stop_cleanup_jobs


@app.on_event("startup")
async def startup_event() -> None:
    await start_cleanup_jobs()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await stop_cleanup_jobs()


# ========== Rate Limiter ==========
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# ========== Exception Handlers ==========
from typing import cast

from starlette.types import ExceptionHandler

from utils.exception_handlers import (
    custom_http_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)


async def cancelled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.info(f"Operation cancelled: {request.url.path}")
    return JSONResponse(status_code=499, content={"detail": "Request cancelled"})


async def keyboard_interrupt_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.info("Server shutting down...")
    return JSONResponse(status_code=503, content={"detail": "Service shutting down"})


app.add_exception_handler(Exception, cast(ExceptionHandler, generic_exception_handler))
app.add_exception_handler(StarletteHTTPException, cast(ExceptionHandler, custom_http_exception_handler))
app.add_exception_handler(RequestValidationError, cast(ExceptionHandler, validation_exception_handler))
# import asyncio
# app.add_exception_handler(asyncio.CancelledError, cast(ExceptionHandler, cancelled_error_handler))


# ========== CORS Middleware ==========
allowed_origins = config.get_allowed_origins()
logger.info(f"CORS allowed origins: {allowed_origins}")

# SECURITY REVIEW: CORS Configuration
# allow_credentials=True is necessary for authentication cookies to work
# However, this can be a CSRF vulnerability if not properly configured
# Mitigations:
# 1. CSRF protection middleware is already enabled (see CSRFMiddleware)
# 2. SameSite cookies are used (see set_refresh_cookie in auth_utils.py)
# 3. Security headers (X-Frame-Options: DENY) prevent clickjacking
# 4. Content-Security-Policy prevents XSS attacks
#
# SECURITY: Only allow credentials from trusted origins
# Never use allow_origins=["*"] with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Required for cookie-based auth
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
        "X-CSRF-Token",  # Required for CSRF protection
    ],
    expose_headers=[
        "Content-Range",
        "X-Content-Range",
        "X-Request-ID",
        "X-CSRF-Token",
        "Content-Length",
        "Content-Type",
    ],
    max_age=86400,  # 24 hours
)


# ========== Health Check Endpoints ==========
@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "version": "3.0.0",
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


# Test endpoint - DISABLED IN PRODUCTION
# @app.get("/api/test-json")
# async def test_json_response():
#     """Test endpoint to verify JSON responses are working correctly"""
#     return JSONResponse(
#         content={
#             "success": True,
#             "message": "JSON response test successful (Reloaded)",
#             "api_version": "v1",
#             "data": {
#                 "test": "JSON parsing should work correctly",
#                 "content_type": "application/json",
#             },
#         },
#         headers={"Content-Type": CONTENT_TYPE_JSON},
#     )


# ========== API Routes ==========
# Include versioned API router (recommended)
app.include_router(api_v1_router)
app.include_router(admin_router, prefix="/api/v1")

# Include health check routes (no prefix, accessible at /health/*)
app.include_router(health_router)

# ========== Security Middleware ==========
# Order matters: First added = Last executed
# Execution order: GZip -> RequestId -> CSRF -> SecurityHeaders -> HTTPSRedirect

# HTTPS redirect (must be added last to run first)
app.add_middleware(HTTPSRedirectMiddleware)

# Trust X-Forwarded-For headers from proxies (e.g. AWS LB, Vercel)
# This prevents IP spoofing in rate limiting
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=os.getenv("TRUSTED_HOSTS", "*").split(","),
)

# Security headers (CSP, HSTS, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CSRF protection for state-changing requests
app.add_middleware(CSRFMiddleware)

# Request ID for tracing and audit logs
app.add_middleware(RequestIdMiddleware)

# ========== Compression ==========

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Vercel expects this to be available


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
