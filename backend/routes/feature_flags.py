"""
Feature Flags API Routes
Exposes feature flag status to frontend clients.
DEPRECATED: These endpoints are currently unused and scheduled for removal.
"""

from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel

from services.feature_flags import FeatureFlagService

router = APIRouter(prefix="/feature-flags", tags=["Feature Flags"])


class FeatureFlagsResponse(BaseModel):
    """Response model for feature flags."""

    flags: dict[str, bool]


@router.get("", response_model=FeatureFlagsResponse, deprecated=True)
async def get_feature_flags(response: Response) -> FeatureFlagsResponse:
    """
    Get all feature flags and their current status.

    DEPRECATED: Frontend uses consolidated config or env vars.
    Sunset: 2026-07-01
    """
    response.headers["X-API-Warn"] = "Deprecated: This endpoint is scheduled for removal on 2026-07-01."
    return FeatureFlagsResponse(flags=FeatureFlagService.get_all_flags())


@router.get("/{flag_name}", deprecated=True)
async def get_feature_flag(flag_name: str, response: Response) -> dict[str, Any]:
    """
    Check if a specific feature flag is enabled.

    DEPRECATED: Frontend uses consolidated config or env vars.
    Sunset: 2026-07-01
    """
    response.headers["X-API-Warn"] = "Deprecated: This endpoint is scheduled for removal on 2026-07-01."
    is_enabled = FeatureFlagService.is_enabled(flag_name)
    return {"flag": flag_name.upper(), "enabled": is_enabled}
