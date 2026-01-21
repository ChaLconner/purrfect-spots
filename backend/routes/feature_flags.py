"""
Feature Flags API Routes
Exposes feature flag status to frontend clients.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from services.feature_flags import FeatureFlagService

router = APIRouter(prefix="/feature-flags", tags=["Feature Flags"])


class FeatureFlagsResponse(BaseModel):
    """Response model for feature flags."""

    flags: dict[str, bool]


@router.get("/", response_model=FeatureFlagsResponse)
async def get_feature_flags():
    """
    Get all feature flags and their current status.

    This endpoint is public and can be called by the frontend
    to determine which features to enable/disable in the UI.
    """
    return FeatureFlagsResponse(flags=FeatureFlagService.get_all_flags())


@router.get("/{flag_name}")
async def get_feature_flag(flag_name: str):
    """
    Check if a specific feature flag is enabled.

    Args:
        flag_name: Name of the feature flag to check

    Returns:
        Object with flag name and enabled status
    """
    is_enabled = FeatureFlagService.is_enabled(flag_name)
    return {"flag": flag_name.upper(), "enabled": is_enabled}
