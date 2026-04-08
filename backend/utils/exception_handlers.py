"""
Unified exception handlers for consistent error response format.

All error responses follow:
{
    "error": true,
    "error_code": "...",
    "message": "...",
    "details": {...},
    "request_id": "..."
}
"""

import os
from typing import Any

import sentry_sdk
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from logger import logger
from utils.security import log_security_event

from .exceptions import PurrfectSpotsException

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CONTENT_TYPE_JSON = "application/json"


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from request state (set by RequestIdMiddleware)."""
    return getattr(request.state, "request_id", None)


def _get_user_id(request: Request) -> str | None:
    """Extract user ID from request state if available."""
    return getattr(request.state, "user_id", None)


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build a unified error JSON response."""
    content: dict[str, Any] = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "detail": message,  # Standard FastAPI error key for backward compatibility
    }
    if details is not None:
        content["details"] = details
    if request_id is not None:
        content["request_id"] = request_id
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )


async def purrfect_spots_exception_handler(request: Request, exc: PurrfectSpotsException) -> JSONResponse:
    """Handle custom business-logic exceptions with unified format."""
    if SENTRY_DSN and exc.status_code >= 500:
        sentry_sdk.capture_exception(exc)

    request_id = _get_request_id(request)
    user_id = _get_user_id(request)

    logger.warning(
        f"Custom Exception: {exc.status_code} - {exc.error_code}: {exc.message}",
        extra={"details": exc.details, "user_id": user_id, "request_id": request_id},
    )

    if exc.status_code >= 400:
        log_security_event(
            event_type="purrfect_spots_exception",
            details={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "message": exc.message,
                "details": exc.details,
            },
            severity="ERROR" if exc.status_code >= 500 else "WARNING",
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with unified format."""
    if SENTRY_DSN:
        sentry_sdk.capture_exception(exc)

    request_id = _get_request_id(request)
    user_id = _get_user_id(request)

    logger.error("Unhandled Exception: %s", exc, exc_info=True)

    log_security_event(
        event_type="unhandled_exception",
        user_id=user_id,
        details={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:200],
            "path": request.url.path,
            "method": request.method,
        },
        severity="ERROR",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    message = "An internal server error occurred."
    if ENVIRONMENT == "development":
        message = str(exc)

    return _error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message=message,
        request_id=request_id,
    )


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions with unified format."""
    request_id = _get_request_id(request)
    user_id = _get_user_id(request)

    if exc.status_code >= 400:
        log_security_event(
            event_type="http_exception",
            user_id=user_id,
            details={
                "status_code": exc.status_code,
                "exception_detail": str(exc.detail)[:200],
                "path": request.url.path,
                "method": request.method,
            },
            severity="WARNING" if exc.status_code < 500 else "ERROR",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    # Map HTTP status codes to error codes
    status_to_code = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "EXTERNAL_SERVICE_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }

    error_code = status_to_code.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if exc.detail else "An error occurred"

    logger.warning("HTTP Exception: %s - %s", exc.status_code, message)

    return _error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        request_id=request_id,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with unified format."""
    request_id = _get_request_id(request)
    user_id = _get_user_id(request)

    log_security_event(
        event_type="validation_error",
        user_id=user_id,
        details={
            "validation_errors": str(exc.errors())[:500],
            "path": request.url.path,
            "method": request.method,
        },
        severity="WARNING",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Build structured error details
    errors: list[dict[str, Any]] = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(
            {
                "field": field,
                "reason": err.get("msg", "Invalid value"),
                "type": err.get("type", "validation_error"),
            }
        )

    logger.warning("Validation Error on %s %s: %s", request.method, request.url.path, errors)

    return _error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": errors},
        request_id=request_id,
    )
