import os
from typing import Any
from unittest.mock import patch

from app.routes.health import check_google_vision


def test_health_check(client: Any) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client: Any) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_google_vision_health_accepts_service_account_json(tmp_path: Any) -> None:
    missing_key_path = tmp_path / "missing-google-vision.json"
    service_account_json = (
        '{"type":"service_account","project_id":"test-project","private_key":"test-key",'
        '"client_email":"vision@example.com","token_uri":"https://oauth2.googleapis.com/token"}'
    )

    with patch.dict(
        os.environ,
        {
            "GOOGLE_VISION_SERVICE_ACCOUNT": service_account_json,
            "GOOGLE_VISION_KEY_PATH": str(missing_key_path),
            "GOOGLE_APPLICATION_CREDENTIALS": "",
        },
    ):
        result = check_google_vision()

    assert result["status"] == "configured"
    assert result["credentials_type"] == "service_account_json"


def test_health_dependencies_redacted_in_production(client: Any) -> None:
    with (
        patch("app.routes.health.config.is_production", return_value=True),
        patch(
            "app.routes.health.check_database",
            return_value={"status": "healthy", "latency_ms": 12.3, "connection": "active"},
        ),
        patch("app.routes.health.check_redis", return_value={"status": "healthy", "used_memory_mb": 42}),
        patch("app.routes.health.check_s3", return_value={"status": "healthy", "bucket": "secret-bucket"}),
        patch(
            "app.routes.health.check_google_vision",
            return_value={"status": "configured", "credentials_path": "secret.json"},
        ),
        patch("app.routes.health.check_sentry", return_value={"status": "configured", "environment": "production"}),
    ):
        response = client.get("/health/dependencies")

    assert response.status_code == 200
    data = response.json()
    assert "environment" not in data
    assert data["dependencies"]["database"] == {"status": "healthy", "latency_ms": 12.3}
    assert data["dependencies"]["s3"] == {"status": "healthy"}


def test_health_metrics_redacted_in_production(client: Any) -> None:
    with (
        patch("app.routes.health.config.is_production", return_value=True),
    ):
        response = client.get("/health/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "environment" not in data
    assert "python_version" not in data


def test_health_details_cannot_be_enabled_in_production(client: Any) -> None:
    with (
        patch("app.routes.health.config.is_production", return_value=True),
        patch(
            "app.routes.health.check_database",
            return_value={"status": "healthy", "connection": "must-not-leak"},
        ),
        patch("app.routes.health.check_redis", return_value={"status": "healthy"}),
        patch("app.routes.health.check_s3", return_value={"status": "healthy", "bucket": "must-not-leak"}),
        patch("app.routes.health.check_google_vision", return_value={"status": "configured"}),
        patch("app.routes.health.check_sentry", return_value={"status": "configured"}),
    ):
        response = client.get("/health/dependencies")

    assert response.status_code == 200
    assert "connection" not in response.json()["dependencies"]["database"]
    assert "bucket" not in response.json()["dependencies"]["s3"]
