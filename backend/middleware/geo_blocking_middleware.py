"""
Geo-blocking middleware for Purrfect Spots API

Provides geographic access control based on IP address country detection.
Uses MaxMind GeoLite2 database or IP-API for country detection.
"""

import os
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from logger import logger
from utils.http_client import get_shared_httpx_client


class GeoBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to block access from specific countries.
    Uses IP-API.com for geolocation (free tier: 45 requests/minute).

    For production, consider using MaxMind GeoLite2 database locally.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        # Blocked country codes (ISO 3166-1 alpha-2)
        # These can be configured via environment variable
        blocked_countries_str = os.getenv("BLOCKED_COUNTRIES", "")
        self.blocked_countries = (
            {code.strip().upper() for code in blocked_countries_str.split(",") if code.strip()}
            if blocked_countries_str
            else set()
        )

        # Admin-only paths that need geo-blocking
        self.admin_paths = ["/admin"]

        # Cache for IP geolocation (simple in-memory cache)
        self._geo_cache: dict[str, str] = {}
        self._geo_cache_ttl = 3600  # 1 hour cache
        self._geo_cache_time: dict[str, float] = {}

    async def _get_country_code(self, ip_address: str) -> str | None:
        """Get country code for IP address using IP-API.com"""
        import time

        # Check cache first
        now = time.time()
        if ip_address in self._geo_cache:
            cache_age = now - self._geo_cache_time.get(ip_address, 0)
            if cache_age < self._geo_cache_ttl:
                return self._geo_cache[ip_address]

        # Skip for local/loopback addresses
        if ip_address in ("127.0.0.1", "::1", "localhost"):
            return None

        try:
            client = get_shared_httpx_client()
            response = await client.get(f"http://ip-api.com/json/{ip_address}?fields=countryCode,status", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    country_code = data.get("countryCode", "")
                    self._geo_cache[ip_address] = country_code
                    self._geo_cache_time[ip_address] = now
                    return country_code
        except Exception as e:
            logger.warning(f"Geo-blocking lookup failed for {ip_address}: {e}")

        return None

    def _is_admin_path(self, path: str) -> bool:
        """Check if the request path is an admin endpoint"""
        return any(path.startswith(admin_path) for admin_path in self.admin_paths)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Only enforce in production or if explicitly configured
        if not self.is_production and not self.blocked_countries:
            return await call_next(request)

        # Only check admin paths
        if not self._is_admin_path(request.url.path):
            return await call_next(request)

        # Get client IP (respecting proxy headers)
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Get country code
        country_code = await self._get_country_code(client_ip)

        if country_code and country_code in self.blocked_countries:
            logger.warning(
                f"Geo-blocking: Access denied from {country_code} | ip={client_ip} | path={request.url.path}"
            )
            return JSONResponse(status_code=403, content={"detail": "Access denied from your region"})

        return await call_next(request)
