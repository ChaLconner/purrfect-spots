"""
Tests for API routes (integration tests)
"""

from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routes.gallery import get_gallery_service


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client) -> None:
        """Test root endpoint returns healthy status"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_endpoint(self, client) -> None:
        """Test /health/live endpoint"""
        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_ready_endpoint(self, client) -> None:
        """Test /health/ready response endpoint"""
        response = client.get("/health/ready")

        # In test environment, DB check might be "unhealthy" but we expect 200 or 503
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data


class TestAPIVersioning:
    """Test API versioning"""

    def test_v1_gallery_endpoint(self, client) -> None:
        """Test that /api/v1/gallery works"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(
            return_value={
                "data": [],
                "total": 0,
                "limit": 20,
                "offset": 0,
                "has_more": False,
            }
        )

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/")

        assert response.status_code == 200

        app.dependency_overrides = {}

    def test_v1_health_not_versioned(self, client) -> None:
        """Test that health endpoints are not versioned"""
        response = client.get("/health")
        assert response.status_code == 200

        # Should not exist under /api/v1
        response = client.get("/api/v1/health")
        assert response.status_code == 404
