"""
Tests for Environment Utilities
"""

import os
from unittest.mock import patch

from utils.env import get_env, is_dev, is_production


class TestEnvUtils:
    """Test suite for environment utilities"""

    def test_is_dev_when_environment_is_development(self):
        """Test is_dev returns True when ENVIRONMENT is development"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert is_dev() is True

    def test_is_dev_when_environment_is_dev(self):
        """Test is_dev returns True when ENVIRONMENT is dev (case insensitive)"""
        with patch.dict(os.environ, {"ENVIRONMENT": "DEVELOPMENT"}):
            assert is_dev() is True

    def test_is_dev_default_when_no_environment(self):
        """Test is_dev returns True by default when ENVIRONMENT not set"""
        with patch.dict(os.environ, {}, clear=True):
            assert is_dev() is True

    def test_is_dev_when_environment_is_production(self):
        """Test is_dev returns False when ENVIRONMENT is production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert is_dev() is False

    def test_is_production_when_environment_is_production(self):
        """Test is_production returns True when ENVIRONMENT is production"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert is_production() is True

    def test_is_production_when_environment_is_prod_uppercase(self):
        """Test is_production with uppercase PRODUCTION"""
        with patch.dict(os.environ, {"ENVIRONMENT": "PRODUCTION"}):
            assert is_production() is True

    def test_is_production_default_when_no_environment(self):
        """Test is_production returns False by default"""
        with patch.dict(os.environ, {}, clear=True):
            assert is_production() is False

    def test_is_production_when_environment_is_development(self):
        """Test is_production returns False when ENVIRONMENT is development"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert is_production() is False

    def test_get_env_with_existing_variable(self):
        """Test get_env returns value when variable exists"""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            assert get_env("TEST_VAR") == "test_value"

    def test_get_env_with_missing_variable_default_empty(self):
        """Test get_env returns empty string when variable missing and no default"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_env("MISSING_VAR") == ""

    def test_get_env_with_missing_variable_custom_default(self):
        """Test get_env returns custom default when variable missing"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_env("MISSING_VAR", "custom_default") == "custom_default"

    def test_get_env_prefers_actual_value_over_default(self):
        """Test get_env returns actual value even when default is provided"""
        with patch.dict(os.environ, {"TEST_VAR": "actual_value"}):
            assert get_env("TEST_VAR", "default_value") == "actual_value"

    def test_get_env_empty_string_value(self):
        """Test get_env can return empty string if that's the actual value"""
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            assert get_env("TEST_VAR", "default") == ""
