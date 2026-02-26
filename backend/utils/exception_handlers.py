import os

import sentry_sdk
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from logger import logger
from utils.security import log_security_event

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CONTENT_TYPE_JSON = "application/json"


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

    detail = "An internal server error occurred."
    if ENVIRONMENT == "development":
        detail = str(exc)

    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers={"Content-Type": CONTENT_TYPE_JSON},
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

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Content-Type": CONTENT_TYPE_JSON},
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

    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "errors": exc.errors()},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
