"""
Security middleware for Purrfect Spots API

Provides:
- HTTPS redirect for production
- Strict Transport Security (HSTS)
- Content Security Policy (CSP)
- XSS protection headers
- Clickjacking protection
"""

import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp
from typing import Callable, Awaitable


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP to HTTPS in production.
    Checks X-Forwarded-Proto header set by reverse proxies (Vercel, nginx, etc.)
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Only enforce in production
        if self.is_production:
            # Check for forwarded proto (set by reverse proxy)
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "")

            # Also check CF-Visitor header (Cloudflare)
            cf_visitor = request.headers.get("CF-Visitor", "")

            is_http = forwarded_proto == "http" or '"scheme":"http"' in cf_visitor

            if is_http:
                url = request.url.replace(scheme="https")
                return RedirectResponse(url, status_code=301)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - Content-Security-Policy: Prevents XSS and data injection
    - Strict-Transport-Security: Forces HTTPS for 1 year
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Legacy XSS protection
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Allow self, data URIs (for base64 images), and specific Google domains for Maps/Fonts
        if self.is_production:
            # Production CSP (API Only)
            # Remove unsafe-inline as we only serve JSON
            csp_policy = (
                "default-src 'none'; frame-ancestors 'none';connect-src 'self';img-src 'self' data: https: blob:;"
            )
        else:
            # Dev CSP (allowing docs etc)
            csp_policy = (
                "default-src 'self'; "
                "img-src 'self' data: https: blob:; "
                "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://accounts.google.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://maps.googleapis.com https://accounts.google.com https://*.sentry.io; "
                "frame-src 'self' https://accounts.google.com; "
                "frame-ancestors 'none';"
            )

        response.headers["Content-Security-Policy"] = csp_policy

        # SECURITY: Add CSP reporting endpoint for monitoring CSP violations
        # This helps detect and respond to XSS attacks in real-time
        if self.is_production:
            # Report CSP violations to Sentry (or your monitoring service)
            # Using report-uri directive
            csp_report_policy = csp_policy + " report-uri https://sentry.io/api/security/csp-report"
            response.headers["Content-Security-Policy-Report-Only"] = csp_report_policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(self), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # HSTS - Only in production (1 year max-age)
        if self.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response
