"""Geolocation helper routes."""

from time import monotonic
from typing import Any

import httpx
from fastapi import APIRouter

from logger import logger
from utils.http_client import get_shared_httpx_client

router = APIRouter(prefix="/geo", tags=["Geolocation"])

IP_GEOLOCATION_URL = "https://ipapi.co/json/"
IP_GEOLOCATION_SUCCESS_TTL_SECONDS = 600
IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS = 900
_cached_ip_location: dict[str, float | None] = {"latitude": None, "longitude": None}
_cached_ip_location_expires_at = 0.0
_rate_limit_backoff_until = 0.0


@router.get("/ip-location")
async def get_ip_location() -> dict[str, Any]:
    """Return an approximate location derived from the request IP."""
    global _cached_ip_location_expires_at, _rate_limit_backoff_until  # noqa: PLW0603
    now = monotonic()
    if now < _cached_ip_location_expires_at:
        return dict(_cached_ip_location)

    if now < _rate_limit_backoff_until:
        logger.info("Skipping IP geolocation lookup during rate-limit cooldown")
        return {"latitude": None, "longitude": None}

    client = get_shared_httpx_client()

    try:
        response = await client.get(IP_GEOLOCATION_URL)
        response.raise_for_status()
        data = response.json()

        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return {"latitude": None, "longitude": None}

        result = {
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
        _cached_ip_location.update(result)
        _cached_ip_location_expires_at = now + IP_GEOLOCATION_SUCCESS_TTL_SECONDS
        _rate_limit_backoff_until = 0.0
        return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            _rate_limit_backoff_until = now + IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS
            logger.info(
                "IP geolocation rate-limited by upstream; suppressing lookups for %s seconds",
                IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS,
            )
        else:
            logger.warning("IP geolocation lookup failed: %s", exc)
        return {"latitude": None, "longitude": None}
    except Exception as exc:
        logger.warning("IP geolocation lookup failed: %s", exc)
        return {"latitude": None, "longitude": None}
