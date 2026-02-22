"""
Tests for Feature Flag Service
"""

import os
from unittest.mock import patch

from services.feature_flags import FeatureFlagService


class TestFeatureFlagService:
    """Test suite for FeatureFlagService"""

    def test_is_enabled_default_false(self):
        """Test that unknown flags default to False"""
        assert FeatureFlagService.is_enabled("UNKNOWN_FLAG") is False

    def test_is_enabled_default_true(self):
        """Test that ENABLE_NEW_UI defaults to False"""
        with patch.dict(os.environ, {}, clear=False):
            # Remove any env var that might exist
            if "FEATURE_ENABLE_NEW_UI" in os.environ:
                del os.environ["FEATURE_ENABLE_NEW_UI"]
            assert FeatureFlagService.is_enabled("ENABLE_NEW_UI") is False

    def test_is_enabled_from_env_true(self):
        """Test that environment variable overrides default (true)"""
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "true"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is True

    def test_is_enabled_from_env_false(self):
        """Test that environment variable overrides default (false)"""
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "false"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is False

    def test_is_enabled_from_env_case_insensitive(self):
        """Test that 'TRUE' in various cases works"""
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "TRUE"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is True
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "True"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is True

    def test_is_enabled_from_env_invalid_value(self):
        """Test that invalid env values default to False"""
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "yes"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is False
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "1"}):
            assert FeatureFlagService.is_enabled("TEST_FLAG") is False

    def test_is_enabled_default_postgis(self):
        """Test ENABLE_POSTGIS_SEARCH default"""
        with patch.dict(os.environ, {}, clear=False):
            if "FEATURE_ENABLE_POSTGIS_SEARCH" in os.environ:
                del os.environ["FEATURE_ENABLE_POSTGIS_SEARCH"]
            assert FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH") is False

    def test_is_enabled_default_ai_v2(self):
        """Test ENABLE_AI_DETECTION_V2 default"""
        with patch.dict(os.environ, {}, clear=False):
            if "FEATURE_ENABLE_AI_DETECTION_V2" in os.environ:
                del os.environ["FEATURE_ENABLE_AI_DETECTION_V2"]
            assert FeatureFlagService.is_enabled("ENABLE_AI_DETECTION_V2") is False

    def test_is_enabled_default_maintenance(self):
        """Test MAINTENANCE_MODE default"""
        with patch.dict(os.environ, {}, clear=False):
            if "FEATURE_MAINTENANCE_MODE" in os.environ:
                del os.environ["FEATURE_MAINTENANCE_MODE"]
            assert FeatureFlagService.is_enabled("MAINTENANCE_MODE") is False

    def test_get_all_flags_defaults(self):
        """Test get_all_flags returns all default flags"""
        with patch.dict(os.environ, {}, clear=False):
            # Clear any existing feature flags
            for key in os.environ:
                if key.startswith("FEATURE_"):
                    del os.environ[key]

            flags = FeatureFlagService.get_all_flags()
            assert "ENABLE_NEW_UI" in flags
            assert "ENABLE_POSTGIS_SEARCH" in flags
            assert "ENABLE_AI_DETECTION_V2" in flags
            assert "MAINTENANCE_MODE" in flags
            assert flags["ENABLE_NEW_UI"] is False
            assert flags["ENABLE_POSTGIS_SEARCH"] is False
            assert flags["ENABLE_AI_DETECTION_V2"] is False
            assert flags["MAINTENANCE_MODE"] is False

    def test_get_all_flags_with_env_override(self):
        with patch.dict(
            os.environ,
            {
                "FEATURE_ENABLE_NEW_UI": "true",
                "FEATURE_MAINTENANCE_MODE": "true",
            },
            clear=False,
        ):
            flags = FeatureFlagService.get_all_flags()
            assert flags["ENABLE_NEW_UI"] is True
            assert flags["MAINTENANCE_MODE"] is True
            assert flags["ENABLE_POSTGIS_SEARCH"] is False
            assert flags["ENABLE_AI_DETECTION_V2"] is False

    def test_feature_flag_name_normalization(self):
        """Test that feature flag names are normalized to uppercase"""
        with patch.dict(os.environ, {"FEATURE_TEST_FLAG": "true"}):
            # All these should work
            assert FeatureFlagService.is_enabled("test_flag") is True
            assert FeatureFlagService.is_enabled("TEST_FLAG") is True
            assert FeatureFlagService.is_enabled("Test_Flag") is True
