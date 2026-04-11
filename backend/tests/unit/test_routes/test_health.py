from typing import Any
from unittest.mock import patch


def test_health_check(client: Any) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root(client: Any) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_dependencies_redacted_in_production(client: Any) -> None:
    with (
        patch("routes.health.config.is_production", return_value=True),
        patch("routes.health.config.EXPOSE_DETAILED_HEALTH", False),
        patch(
            "routes.health.check_database",
            return_value={"status": "healthy", "latency_ms": 12.3, "connection": "active"},
        ),
        patch("routes.health.check_redis", return_value={"status": "healthy", "used_memory_mb": 42}),
        patch("routes.health.check_s3", return_value={"status": "healthy", "bucket": "secret-bucket"}),
        patch(
            "routes.health.check_google_vision",
            return_value={"status": "configured", "credentials_path": "secret.json"},
        ),
        patch("routes.health.check_sentry", return_value={"status": "configured", "environment": "production"}),
    ):
        response = client.get("/health/dependencies")

    assert response.status_code == 200
    data = response.json()
    assert "environment" not in data
    assert data["dependencies"]["database"] == {"status": "healthy", "latency_ms": 12.3}
    assert data["dependencies"]["s3"] == {"status": "healthy"}


def test_health_metrics_redacted_in_production(client: Any) -> None:
    with (
        patch("routes.health.config.is_production", return_value=True),
        patch("routes.health.config.EXPOSE_DETAILED_HEALTH", False),
    ):
        response = client.get("/health/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "environment" not in data
    assert "python_version" not in data
