"""
CSRF Protection Middleware for Purrfect Spots API

Provides Double Submit Cookie pattern for CSRF protection.
This protects against Cross-Site Request Forgery attacks by:
1. Setting a cryptographically secure token in a cookie
2. Requiring the same token in a request header
3. Validating both tokens match using constant-time comparison
"""

import secrets
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import config
from app.logger import logger
from app.runtime_environment import is_production_environment


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection using Double Submit Cookie pattern.

    How it works:
    - On GET requests: Sets a CSRF token in a cookie (if not present)
    - On state-changing requests (POST, PUT, DELETE, PATCH):
      1. Reads token from cookie
      2. Reads token from X-CSRF-Token header
      3. Validates both tokens match
      4. Rejects request if tokens don't match or are missing

    Configuration:
    - exempt_paths: List of paths that don't require CSRF validation
    - Only active in production for auth endpoints
    """

    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    SAFE_METHODS: set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}
    COOKIE_AUTH_PATHS: set[str] = {"/api/v1/auth/refresh-token", "/api/v1/auth/logout"}

    def __init__(self, app: Any, exempt_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.is_production = is_production_environment()
        self.allowed_origins = {origin.rstrip("/") for origin in config.get_allowed_origins()}
        # Default exempt paths - APIs that don't need CSRF
        # (they use other auth mechanisms like OAuth tokens)
        # SECURITY REVIEW: Only exempt endpoints that are truly stateless or use other auth mechanisms
        self.exempt_paths = (
            exempt_paths
            or [
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/api/v1/auth/google",
                "/api/v1/auth/google/callback",
                "/api/v1/auth/login",
                "/api/v1/auth/register",
                "/api/v1/auth/refresh-token",  # Exempt: uses HttpOnly cookie (not JS-accessible), rotated on use, IP+UA bound
                "/api/v1/auth/logout",
                "/api/v1/auth/forgot-password",
                "/api/v1/auth/reset-password",
                # Stripe authenticates this endpoint with the
                # Stripe-Signature header; it cannot send our CSRF cookie.
                "/api/v1/subscription/webhook",
                # Public read-only endpoints (GET requests are already exempt by SAFE_METHODS)
                "/api/v1/gallery",
                "/api/v1/locations",
                # Cat detection endpoint - uses API key authentication, not session-based
                "/api/v1/cat-detection",
            ]
        )

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in self.SAFE_METHODS:
            return await self._handle_safe_method(request, call_next)

        origin_error = self._validate_cookie_auth_origin(request)
        if origin_error:
            return origin_error

        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        if self._has_manual_authorization(request):
            return await call_next(request)

        if not self.is_production:
            return await self._handle_development_request(request, call_next)
        return await self._handle_production_request(request, call_next)

    async def _handle_safe_method(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if request.method == "GET":
            response = self._set_csrf_cookie(request, response)
        return response

    def _validate_cookie_auth_origin(self, request: Request) -> Response | None:
        if not self._requires_same_origin_check(request):
            return None

        origin = self._extract_request_origin(request)
        if origin and origin in self.allowed_origins:
            return None

        logger.warning(
            "Blocked cross-site cookie-auth request: path=%s origin=%s referer=%s",
            request.url.path,
            origin,
            request.headers.get("referer"),
        )
        return self._csrf_error_response(
            "CSRF_ORIGIN_MISMATCH",
            "Cross-site request blocked. Please retry from the Purrfect Spots app.",
        )

    @staticmethod
    def _has_manual_authorization(request: Request) -> bool:
        return request.headers.get("Authorization") is not None or request.headers.get("authorization") is not None

    async def _handle_development_request(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_HEADER_NAME)
        if cookie_token and header_token and not secrets.compare_digest(cookie_token, header_token):
            logger.warning("CSRF token mismatch in development mode")
        return await call_next(request)

    async def _handle_production_request(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning("CSRF token missing")
            return self._csrf_error_response(
                "CSRF_TOKEN_MISSING",
                "CSRF token missing. Please refresh and try again.",
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning("CSRF token mismatch")
            return self._csrf_error_response(
                "CSRF_TOKEN_MISMATCH",
                "CSRF token validation failed. Please refresh and try again.",
            )

        return await call_next(request)

    @staticmethod
    def _csrf_error_response(error_code: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": True, "error_code": error_code, "message": message},
        )

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from CSRF validation"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _requires_same_origin_check(self, request: Request) -> bool:
        """Require same-origin validation for cookie-authenticated exempt endpoints."""
        return (
            self.is_production
            and request.url.path in self.COOKIE_AUTH_PATHS
            and bool(request.cookies.get("refresh_token"))
        )

    def _extract_request_origin(self, request: Request) -> str | None:
        """Extract the request origin from Origin or Referer headers."""
        origin = request.headers.get("origin")
        if origin:
            return origin.rstrip("/")

        referer = request.headers.get("referer")
        if not referer:
            return None

        parsed = urlsplit(referer)
        if not parsed.scheme or not parsed.netloc:
            return None

        return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")

    def _set_csrf_cookie(self, request: Request, response: Response) -> Response:
        """Set CSRF token cookie if not already present"""
        if self.CSRF_COOKIE_NAME not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(  # NOSONAR python:S3330 - CSRF Double-Submit-Cookie pattern requires JS-readable token
                key=self.CSRF_COOKIE_NAME,
                value=token,
                httponly=False,  # NOSONAR python:S3330 - CSRF Double-Submit-Cookie pattern requires JS-readable token
                secure=self.is_production,
                # IMPORTANT: SameSite=None is required for cross-origin requests
                # (frontend on purrfectspots.xyz, backend on vercel.app)
                samesite="none" if self.is_production else "lax",
                max_age=3600 * 24,  # 24 hours
                path="/",
            )
        return response
