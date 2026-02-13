"""
CSRF Protection Middleware for Purrfect Spots API

Provides Double Submit Cookie pattern for CSRF protection.
This protects against Cross-Site Request Forgery attacks by:
1. Setting a cryptographically secure token in a cookie
2. Requiring the same token in a request header
3. Validating both tokens match using constant-time comparison
"""

import os
import secrets

from typing import Any, Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from logger import logger


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

    def __init__(self, app: Any, exempt_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        # Default exempt paths - APIs that don't need CSRF
        # (they use other auth mechanisms like OAuth tokens)
        # SECURITY REVIEW: Only exempt endpoints that are truly stateless or use other auth mechanisms
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/google",
            "/api/v1/auth/google/callback",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            # "/api/v1/auth/refresh-token",  # Protected by CSRF
            "/api/v1/auth/logout",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            # Public read-only endpoints (GET requests are already exempt by SAFE_METHODS)
            "/api/v1/gallery",
            "/api/v1/locations",
            # Cat detection endpoint - uses API key authentication, not session-based
            "/api/v1/cat-detection",
        ]

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip CSRF for safe methods (GET, HEAD, OPTIONS, TRACE)
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            # Set CSRF token cookie on safe requests for later use
            if request.method == "GET" and not request.url.path.startswith("/api"):
                response = self._set_csrf_cookie(request, response)
            return response

        # Skip exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # In development, CSRF is optional (easier testing)
        if not self.is_production:
            # Still validate if tokens are provided
            cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
            header_token = request.headers.get(self.CSRF_HEADER_NAME)
            if cookie_token and header_token:
                if not secrets.compare_digest(cookie_token, header_token):
                    logger.warning(f"CSRF token mismatch in dev mode: path={request.url.path}")
            return await call_next(request)

        # Production: Full CSRF validation
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(
                f"CSRF token missing: path={request.url.path}, "
                f"cookie_present={bool(cookie_token)}, header_present={bool(header_token)}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "error_code": "CSRF_TOKEN_MISSING",
                    "message": "CSRF token missing. Please refresh and try again.",
                },
            )

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF token mismatch: path={request.url.path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "error_code": "CSRF_TOKEN_MISMATCH",
                    "message": "CSRF token validation failed. Please refresh and try again.",
                },
            )

        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from CSRF validation"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _set_csrf_cookie(self, request: Request, response: Response) -> Response:
        """Set CSRF token cookie if not already present"""
        if self.CSRF_COOKIE_NAME not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=self.CSRF_COOKIE_NAME,
                value=token,
                httponly=False,  # JavaScript needs to read this
                secure=self.is_production,
                samesite="strict" if self.is_production else "lax",
                max_age=3600 * 24,  # 24 hours
                path="/",
            )
        return response
