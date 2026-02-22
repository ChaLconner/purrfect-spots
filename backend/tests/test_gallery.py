"""
Original gallery tests - updated for new pagination API
"""

from unittest.mock import AsyncMock, MagicMock

from main import app
from routes.gallery import get_gallery_service


def test_get_gallery_empty(client):
    """Test gallery endpoint returns empty list when no photos exist"""
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
    data = response.json()
    assert data["images"] == []
    assert data["pagination"]["total"] == 0

    app.dependency_overrides = {}


def test_get_gallery_with_data(client, mock_cat_photo):
    """Test gallery endpoint returns correct data format"""
    mock_service = MagicMock()
    mock_service.get_all_photos = AsyncMock(
        return_value={
            "data": [mock_cat_photo],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        }
    )

    app.dependency_overrides[get_gallery_service] = lambda: mock_service

    response = client.get("/api/v1/gallery/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) == 1
    assert data["images"][0]["location_name"] == "Test Cat Spot"
    assert data["images"][0]["image_url"] == "https://example.com/cat.jpg"
    assert data["pagination"]["total"] == 1

    app.dependency_overrides = {}


def test_get_gallery_error(client):
    """Test gallery endpoint handles errors gracefully"""
    mock_service = MagicMock()
    mock_service.get_all_photos = AsyncMock(side_effect=Exception("Database error"))

    app.dependency_overrides[get_gallery_service] = lambda: mock_service

    response = client.get("/api/v1/gallery/")
    assert response.status_code == 500
    assert "Failed to fetch gallery images" in response.json()["detail"]

    app.dependency_overrides = {}


def test_get_all_gallery(client):
    mock_service = MagicMock()
    mock_service.get_all_photos_simple = AsyncMock(
        return_value=[
            {
                "id": "1",
                "image_url": "url",
                "latitude": 10,
                "longitude": 10,
                "location_name": "loc",
                "uploaded_at": "2024-03-20T10:00:00Z",
            }
        ]
    )
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/all")
    assert response.status_code == 200
    assert len(response.json()["images"]) == 1


def test_get_locations(client):
    mock_service = MagicMock()
    mock_service.get_map_locations = AsyncMock(
        return_value=[
            {
                "id": "1",
                "image_url": "url",
                "latitude": 10,
                "longitude": 10,
                "location_name": "loc",
                "uploaded_at": "2024-03-20T10:00:00Z",
            }
        ]
    )
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/locations")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_viewport(client):
    mock_service = MagicMock()
    mock_service.get_nearby_photos = AsyncMock(
        return_value=[
            {
                "id": "1",
                "image_url": "url",
                "latitude": 10,
                "longitude": 10,
                "location_name": "loc",
                "uploaded_at": "2024-03-20T10:00:00Z",
            }
        ]
    )
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/viewport?north=10&south=5&east=10&west=5")
    assert response.status_code == 200
    assert len(response.json()["images"]) == 1


def test_search_locations(client):
    mock_service = MagicMock()
    mock_service.search_photos = AsyncMock(
        return_value=[
            {
                "id": "1",
                "image_url": "url",
                "latitude": 10,
                "longitude": 10,
                "location_name": "loc",
                "uploaded_at": "2024-03-20T10:00:00Z",
            }
        ]
    )
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/search?q=cat&tags=cute")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_popular_tags(client):
    mock_service = MagicMock()
    mock_service.get_popular_tags = AsyncMock(return_value=[{"tag": "cute", "count": 10}])
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/popular-tags")
    assert response.status_code == 200
    assert len(response.json()["tags"]) == 1


def test_get_photo(client):
    mock_service = MagicMock()
    mock_service.get_photo_by_id = AsyncMock(
        return_value={
            "id": "1",
            "image_url": "url",
            "latitude": 10,
            "longitude": 10,
            "location_name": "loc",
            "uploaded_at": "2024-03-20T10:00:00Z",
        }
    )
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 200
    assert response.json()["id"] == "1"


def test_delete_photo(client):
    from middleware.auth_middleware import get_current_user_from_credentials

    mock_service = MagicMock()
    mock_service.verify_photo_ownership = AsyncMock(return_value={"id": "1", "image_url": "url"})
    mock_service.process_photo_deletion = AsyncMock()
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    app.dependency_overrides[get_current_user_from_credentials] = lambda: MagicMock(id="user1")
    response = client.delete("/api/v1/gallery/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 202
    assert response.json()["message"] == "Deletion scheduled"
    app.dependency_overrides.clear()
