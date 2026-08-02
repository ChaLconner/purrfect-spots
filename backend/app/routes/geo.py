"""Geolocation helper routes."""

import ipaddress
from time import monotonic
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Request

from app.logger import logger
from app.utils.auth_utils import get_client_info
from app.utils.http_client import get_shared_httpx_client

router = APIRouter(prefix="/geo", tags=["Geolocation"])

IP_GEOLOCATION_URL = "https://ipapi.co"
IP_GEOLOCATION_SUCCESS_TTL_SECONDS = 600
IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS = 900
_ip_location_cache: dict[str, tuple[float, dict[str, float | None]]] = {}
_ip_location_cache_state = {"rate_limit_backoff_until": 0.0}


def _empty_location() -> dict[str, None]:
    return {"latitude": None, "longitude": None}


def _get_public_client_ip(request: Request) -> str | None:
    client_ip, _ = get_client_info(request)
    try:
        parsed_ip = ipaddress.ip_address(client_ip)
    except ValueError:
        return None
    return str(parsed_ip) if parsed_ip.is_global else None


@router.get("/ip-location")
async def get_ip_location(request: Request) -> dict[str, Any]:
    """Return an approximate location derived from the request IP."""
    client_ip = _get_public_client_ip(request)
    if not client_ip:
        return _empty_location()

    now = monotonic()
    cached = _ip_location_cache.get(client_ip)
    if cached and now < cached[0]:
        return dict(cached[1])

    if now < _ip_location_cache_state["rate_limit_backoff_until"]:
        logger.info("Skipping IP geolocation lookup during rate-limit cooldown")
        return _empty_location()

    client = get_shared_httpx_client()
    lookup_url = f"{IP_GEOLOCATION_URL}/{quote(client_ip, safe='')}/json/"

    try:
        response = await client.get(lookup_url)
        response.raise_for_status()
        data = response.json()

        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return _empty_location()

        result: dict[str, float | None] = {
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
        if len(_ip_location_cache) >= 1024:
            _ip_location_cache.pop(next(iter(_ip_location_cache)))
        _ip_location_cache[client_ip] = (now + IP_GEOLOCATION_SUCCESS_TTL_SECONDS, result)
        _ip_location_cache_state["rate_limit_backoff_until"] = 0.0
        return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            _ip_location_cache_state["rate_limit_backoff_until"] = now + IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS
            logger.info(
                "IP geolocation rate-limited by upstream; suppressing lookups for %s seconds",
                IP_GEOLOCATION_RATE_LIMIT_COOLDOWN_SECONDS,
            )
        else:
            logger.warning("IP geolocation lookup failed: %s", exc)
        return _empty_location()
    except Exception as exc:
        logger.warning("IP geolocation lookup failed: %s", exc)
        return _empty_location()
