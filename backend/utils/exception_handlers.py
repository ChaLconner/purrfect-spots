import os

import sentry_sdk
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import config
from logger import logger
from utils.security import log_security_event

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CONTENT_TYPE_JSON = "application/json"

# Get allowed origins once for exception handlers
_allowed_origins = config.get_allowed_origins()


def _get_cors_origin_for_request(request: Request) -> str:
    """
    Get appropriate CORS origin header for request.
    Returns request origin if it's in allowed list, otherwise empty.
    This prevents CORS wildcard security issues.
    """
    origin = request.headers.get("origin", "")
    if origin in _allowed_origins:
        return origin
    # For same-origin requests or non-browser clients
    return _allowed_origins[0] if _allowed_origins else ""


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Capture exception in Sentry
    if SENTRY_DSN:
        sentry_sdk.capture_exception(exc)

    logger.error(f"Unhandled Exception: {exc}", exc_info=True)

    # SECURITY: Log security event for audit trail
    # This helps track potential attacks and system issues
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user_id = getattr(request.state, "user_id", None)  # Get user_id from request state if available

    log_security_event(
        event_type="unhandled_exception",
        user_id=user_id,
        details={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:200],  # Limit length to prevent log injection
            "path": request.url.path,
            "method": request.method,
        },
        severity="ERROR",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    cors_origin = _get_cors_origin_for_request(request)

    # Return generic message to client, detailed error stays in logs
    # In development, show the error for easier debugging
    detail = "Internal Server Error"
    if ENVIRONMENT == "development":
        detail = str(exc)

    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers={
            "Content-Type": CONTENT_TYPE_JSON,
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": CONTENT_TYPE_JSON},
    )


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # SECURITY: Log security event for HTTP exceptions
    # This helps track potential attacks and system issues
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user_id = getattr(request.state, "user_id", None)  # Get user_id from request state if available

    # Log security event for HTTP exceptions (4xx, 5xx)
    if exc.status_code >= 400:
        log_security_event(
            event_type="http_exception",
            user_id=user_id,
            details={
                "status_code": exc.status_code,
                "exception_detail": str(exc.detail)[:200],  # Limit length to prevent log injection
                "path": request.url.path,
                "method": request.method,
            },
            severity="WARNING" if exc.status_code < 500 else "ERROR",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    cors_origin = _get_cors_origin_for_request(request)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Content-Type": CONTENT_TYPE_JSON,
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": CONTENT_TYPE_JSON},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # SECURITY: Log security event for validation errors
    # This helps track potential attacks and system issues
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    user_id = getattr(request.state, "user_id", None)  # Get user_id from request state if available

    log_security_event(
        event_type="validation_error",
        user_id=user_id,
        details={
            "validation_errors": str(exc.errors())[:500],  # Limit length to prevent log injection
            "path": request.url.path,
            "method": request.method,
        },
        severity="WARNING",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.warning(f"Validation Error: {exc}")

    cors_origin = _get_cors_origin_for_request(request)

    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
        headers={
            "Content-Type": CONTENT_TYPE_JSON,
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        }
        if cors_origin
        else {"Content-Type": CONTENT_TYPE_JSON},
    )
