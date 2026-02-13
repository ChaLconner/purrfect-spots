"""
Tests for API routes (integration tests)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from main import app
from routes.gallery import get_gallery_service


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_json_test_endpoint(self, client):
        """Test JSON response endpoint"""
        response = client.get("/api/test-json")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_version" in data


class TestGalleryRoutes:
    """Test gallery API routes"""

    def test_get_gallery_empty(self, client):
        """Test gallery endpoint returns empty list when no photos exist"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(return_value={
            "data": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        })

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/")

        assert response.status_code == 200
        data = response.json()
        assert data["images"] == []
        assert data["pagination"]["total"] == 0

        app.dependency_overrides = {}

    def test_get_gallery_with_data(self, client, mock_cat_photo):
        """Test gallery endpoint returns correct data format"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(return_value={
            "data": [mock_cat_photo],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        })

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1
        assert data["images"][0]["location_name"] == "Test Cat Spot"
        assert data["pagination"]["total"] == 1

        app.dependency_overrides = {}

    def test_get_gallery_pagination(self, client, mock_cat_photo):
        """Test gallery endpoint pagination parameters"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(return_value={
            "data": [mock_cat_photo],
            "total": 50,
            "limit": 10,
            "offset": 20,
            "has_more": True,
        })

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 20
        assert data["pagination"]["has_more"] is True

        app.dependency_overrides = {}

    def test_get_gallery_by_page(self, client, mock_cat_photo):
        """Test gallery endpoint with page parameter"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(return_value={
            "data": [mock_cat_photo],
            "total": 50,
            "limit": 10,
            "offset": 10,
            "has_more": True,
        })

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/?page=2&limit=10")

        assert response.status_code == 200
        # Page 2 with limit 10 should have offset 10
        mock_service.get_all_photos.assert_called_with(
            limit=10,
            offset=10,  # (2-1) * 10
            include_total=True,
            user_id=None,
        )

        app.dependency_overrides = {}

    def test_get_gallery_all_endpoint(self, client, mock_cat_photo):
        """Test /gallery/all endpoint for backward compatibility"""
        mock_service = MagicMock()
        mock_service.get_all_photos_simple = AsyncMock(return_value=[mock_cat_photo])

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/all")

        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) == 1

        app.dependency_overrides = {}

    def test_get_locations(self, client, mock_cat_photo):
        """Test locations endpoint for map display"""
        mock_service = MagicMock()
        mock_service.get_map_locations = AsyncMock(return_value=[mock_cat_photo])

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/locations")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["latitude"] == pytest.approx(13.7563)
        assert data[0]["longitude"] == pytest.approx(100.5018)

        app.dependency_overrides = {}

    def test_search_locations(self, client, mock_cat_photo):
        """Test search endpoint"""
        mock_service = MagicMock()
        mock_service.search_photos = AsyncMock(return_value=[mock_cat_photo])

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/search?q=Cat")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["query"] == "Cat"

        app.dependency_overrides = {}

    def test_search_by_tags(self, client, mock_cat_photo):
        """Test search endpoint with tags"""
        mock_service = MagicMock()
        mock_service.search_photos = AsyncMock(return_value=[mock_cat_photo])

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/search?tags=orange,friendly")

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["orange", "friendly"]

        app.dependency_overrides = {}

    def test_get_popular_tags(self, client):
        """Test popular tags endpoint"""
        mock_service = MagicMock()
        mock_service.get_popular_tags = AsyncMock(return_value=[
            {"tag": "cute", "count": 10},
            {"tag": "orange", "count": 8},
        ])

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/popular-tags")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2
        assert data["tags"][0]["tag"] == "cute"

        app.dependency_overrides = {}

    def test_gallery_error_handling(self, client):
        """Test gallery endpoint handles errors gracefully"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(side_effect=Exception("Database error"))

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/")

        assert response.status_code == 500
        assert "Failed to fetch gallery images" in response.json()["detail"]

        app.dependency_overrides = {}


class TestAPIVersioning:
    """Test API versioning"""

    def test_v1_gallery_endpoint(self, client):
        """Test that /api/v1/gallery works"""
        mock_service = MagicMock()
        mock_service.get_all_photos = AsyncMock(return_value={
            "data": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        })

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        response = client.get("/api/v1/gallery/")

        assert response.status_code == 200

        app.dependency_overrides = {}

    def test_v1_health_not_versioned(self, client):
        """Test that health endpoints are not versioned"""
        response = client.get("/health")
        assert response.status_code == 200

        # Should not exist under /api/v1
        response = client.get("/api/v1/health")
        assert response.status_code == 404
