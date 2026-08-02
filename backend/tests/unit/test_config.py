from unittest.mock import patch

from app.config import config


def test_explicit_cors_origins_are_authoritative() -> None:
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "https://staging.example.com",
            "FRONTEND_URL": "https://production.example.com",
            "VERCEL_URL": "preview.example.vercel.app",
        },
        clear=True,
    ):
        assert config.get_allowed_origins() == ["https://staging.example.com"]


def test_production_without_explicit_cors_uses_only_configured_frontend() -> None:
    with patch.dict(
        "os.environ",
        {"ENVIRONMENT": "production", "FRONTEND_URL": "https://production.example.com"},
        clear=True,
    ):
        assert config.get_allowed_origins() == ["https://production.example.com"]


def test_development_cors_defaults_do_not_include_production_origins() -> None:
    with patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=True):
        origins = config.get_allowed_origins()

    assert "http://localhost:5173" in origins
    assert "https://purrfectspots.xyz" not in origins
