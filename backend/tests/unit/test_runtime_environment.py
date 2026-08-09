import os
from unittest.mock import patch

from app.runtime_environment import is_production_environment, resolve_environment


def test_vercel_environment_is_used_when_explicit_environment_is_missing() -> None:
    with patch.dict(os.environ, {"VERCEL_ENV": "production"}, clear=True):
        assert resolve_environment() == "production"
        assert is_production_environment()


def test_explicit_environment_takes_precedence_over_vercel() -> None:
    with patch.dict(os.environ, {"ENVIRONMENT": "preview", "VERCEL_ENV": "production"}, clear=True):
        assert resolve_environment() == "preview"
        assert not is_production_environment()
