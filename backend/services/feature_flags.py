"""
Feature Flag Service
Manages feature toggles for the application.
Currently uses Environment variables and defaults.
Future: Integrate with PostHog or Database.
"""

import os


class FeatureFlagService:
    """
    Simple Feature Flag service.
    """

    # Define default flags here
    _DEFAULTS = {
        "ENABLE_NEW_UI": False,
        "ENABLE_POSTGIS_SEARCH": False,  # Feature flag for our new migration
        "ENABLE_AI_DETECTION_V2": False,
        "MAINTENANCE_MODE": False,
    }

    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        Priority:
        1. Environment Variable (FEATURE_FLAG_NAME=true)
        2. Application Config
        3. Default value
        4. False
        """
        flag_name = feature_name.upper()

        # 1. Check Env Var (prefixed with FEATURE_)
        env_key = f"FEATURE_{flag_name}"
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val.lower() == "true"

        # 2. Check Defaults
        return cls._DEFAULTS.get(flag_name, False)

    @classmethod
    def get_all_flags(cls) -> dict[str, bool]:
        """
        Get all defined flags and their current status.
        Useful for frontend initialization.
        """
        flags = {}
        # Iterate over defaults to know what flags exist
        for key in cls._DEFAULTS:
            flags[key] = cls.is_enabled(key)
        return flags


# Global instance not needed as methods are classmethods, but for DI consistency:
feature_flags = FeatureFlagService()
