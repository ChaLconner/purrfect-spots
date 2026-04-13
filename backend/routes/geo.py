"""Geolocation helper routes."""

from typing import Any

from fastapi import APIRouter

from logger import logger
from utils.http_client import get_shared_httpx_client

router = APIRouter(prefix="/geo", tags=["Geolocation"])


@router.get("/ip-location")
async def get_ip_location() -> dict[str, Any]:
    """Return an approximate location derived from the request IP."""
    client = get_shared_httpx_client()

    try:
        response = await client.get("https://ipapi.co/json/")
        response.raise_for_status()
        data = response.json()

        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return {"latitude": None, "longitude": None}

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
    except Exception as exc:
        logger.warning("IP geolocation lookup failed: %s", exc)
        return {"latitude": None, "longitude": None}
