"""
Integration tests for Health Check endpoints

These tests verify that health check endpoints:
1. Return correct status codes
2. Check actual dependency connectivity
3. Handle failures gracefully
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Integration tests for /health/* endpoints"""

    def test_liveness_returns_alive(self, client):
        """Test: GET /health/live returns alive status"""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "version" in data

    def test_liveness_no_cache(self, client):
        """Test: Liveness endpoint has no-cache headers"""
        response = client.get("/health/live")

        assert "no-cache" in response.headers.get("Cache-Control", "")

    def test_readiness_returns_status(self, client):
        """Test: GET /health/ready returns readiness status"""
        response = client.get("/health/ready")

        # Can be 200 (ready) or 503 (not ready) depending on dependencies
        assert response.status_code in [200, 503]

        data = response.json()
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data

    def test_readiness_includes_all_checks(self, client):
        """Test: Readiness check includes all dependency checks"""
        response = client.get("/health/ready")
        data = response.json()

        expected_checks = ["database", "redis", "s3", "sentry"]
        for check in expected_checks:
            assert check in data["checks"], f"Missing check: {check}"

    def test_dependencies_detailed_status(self, client):
        """Test: GET /health/dependencies returns detailed info"""
        response = client.get("/health/dependencies")

        assert response.status_code == 200
        data = response.json()

        assert "dependencies" in data
        assert "health_score" in data
        assert "google_vision" in data["dependencies"]

    def test_metrics_returns_cache_stats(self, client):
        """Test: GET /health/metrics returns cache statistics"""
        response = client.get("/health/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "cache" in data
        assert "timestamp" in data
        assert "environment" in data


class TestHealthCheckDependencyFailures:
    """Test health check behavior when dependencies fail"""

    def test_readiness_unhealthy_when_database_down(self, client):
        """Test: Readiness returns 503 when database is down"""
        with patch("routes.health.check_database") as mock_db:
            mock_db.return_value = {
                "status": "unhealthy",
                "error": "Connection refused",
            }

            response = client.get("/health/ready")

            assert response.status_code == 503
            assert response.json()["status"] == "not_ready"

    def test_readiness_healthy_when_redis_down(self, client):
        """Test: Readiness is still ready when Redis is down (non-critical)"""
        with (
            patch("routes.health.check_database") as mock_db,
            patch("routes.health.check_redis") as mock_redis,
        ):
            mock_db.return_value = {"status": "healthy", "latency_ms": 50}
            mock_redis.return_value = {
                "status": "unhealthy",
                "error": "Connection refused",
            }

            response = client.get("/health/ready")

            # Should still be ready since Redis is optional
            assert response.status_code == 200


class TestHealthCheckAuthentication:
    """Test that health endpoints don't require authentication"""

    def test_live_no_auth_required(self, client):
        """Test: /health/live works without auth token"""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_ready_no_auth_required(self, client):
        """Test: /health/ready works without auth token"""
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]  # May fail if deps down

    def test_dependencies_no_auth_required(self, client):
        """Test: /health/dependencies works without auth token"""
        response = client.get("/health/dependencies")
        assert response.status_code == 200


# Fixtures
@pytest.fixture
def client():
    """Create test client"""
    from main import app

    return TestClient(app)
