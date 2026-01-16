"""
PurrFect Spots API - Main Application


Features:
- API versioning (/api/v1/*)
- Sentry error monitoring
- Rate limiting
- CORS configuration
"""

import os

# ========== Sentry Integration ==========
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

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

# Import versioned API router
from routes.api_v1 import router as api_v1_router
from routes.health import router as health_router

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        # Performance monitoring
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        # Profiling (requires additional setup)
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        # Send user info for debugging
        send_default_pii=False,
        # Enable breadcrumbs
        max_breadcrumbs=50,
        # Attach stack traces for non-exception events
        attach_stacktrace=True,
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

# ========== Rate Limiter ==========
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Get allowed origins once for exception handlers
_allowed_origins = config.get_allowed_origins()


def _get_cors_origin_for_request(request: Request) -> str:
    """
    Get appropriate CORS origin header for the request.
    Returns the request origin if it's in allowed list, otherwise empty.
    This prevents CORS wildcard security issues.
    """
    origin = request.headers.get("origin", "")
    if origin in _allowed_origins:
        return origin
    # For same-origin requests or non-browser clients
    return _allowed_origins[0] if _allowed_origins else ""


# ========== Exception Handlers ==========
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Capture exception in Sentry
    if SENTRY_DSN:
        sentry_sdk.capture_exception(exc)

    logger.error(f"Unhandled Exception: {exc}", exc_info=True)

    cors_origin = _get_cors_origin_for_request(request)

    # Return generic message to client, detailed error stays in logs
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": "application/json"},
    )


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    cors_origin = _get_cors_origin_for_request(request)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": "application/json"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc}")

    cors_origin = _get_cors_origin_for_request(request)

    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": "application/json"},
    )


# ========== CORS Middleware ==========
allowed_origins = config.get_allowed_origins()
logger.info(f"CORS allowed origins: {allowed_origins}")

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
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)


# ========== Health Check Endpoints ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "version": "3.0.0",
            "api_versions": ["v1"],
        },
        headers={"Content-Type": "application/json"},
    )


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "PurrFect Spots API is running",
            "sentry_enabled": bool(SENTRY_DSN),
        },
        headers={"Content-Type": "application/json"},
    )


@app.get("/api/test-json")
async def test_json_response():
    """Test endpoint to verify JSON responses are working correctly"""
    return JSONResponse(
        content={
            "success": True,
            "message": "JSON response test successful",
            "api_version": "v1",
            "data": {
                "test": "JSON parsing should work correctly",
                "content_type": "application/json",
            },
        },
        headers={"Content-Type": "application/json"},
    )


# ========== API Routes ==========
# Include versioned API router (recommended)
app.include_router(api_v1_router)

# Include health check routes (no prefix, accessible at /health/*)
app.include_router(health_router)

# ========== Security Middleware ==========
# Order matters: First added = Last executed
# Execution order: GZip -> RequestId -> CSRF -> SecurityHeaders -> HTTPSRedirect

# HTTPS redirect (must be added last to run first)
app.add_middleware(HTTPSRedirectMiddleware)

# Security headers (CSP, HSTS, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CSRF protection for state-changing requests
app.add_middleware(CSRFMiddleware)

# Request ID for tracing and audit logs
app.add_middleware(RequestIdMiddleware)

# ========== Compression ==========

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Legacy routes removed as of v3.0.0 - Use /api/v1/* endpoints instead
# All frontend code should use the apiV1 client from utils/api.ts
# ---------------------------------------------------------------
# DEPRECATED: The following legacy routes have been removed to prevent
# confusion and ensure consistent API versioning:
# - app.include_router(auth_manual.router)
# - app.include_router(auth_google.router)
# - app.include_router(profile.router)
# - app.include_router(upload.router)
# - app.include_router(cat_detection.router)
# - app.include_router(gallery.router)


# Vercel expects this to be available
handler = app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
