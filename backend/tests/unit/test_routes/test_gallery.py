"""
Original gallery tests - updated for new pagination API
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from main import app
from routes.gallery import get_gallery_service
from utils.security import protect_public_coordinates


def test_get_gallery_empty(client) -> None:
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


def test_get_gallery_with_data(client, mock_cat_photo) -> None:
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


def test_get_gallery_error(client) -> None:
    """Test gallery endpoint handles errors gracefully"""
    mock_service = MagicMock()
    mock_service.get_all_photos = AsyncMock(side_effect=Exception("Database error"))

    app.dependency_overrides[get_gallery_service] = lambda: mock_service

    response = client.get("/api/v1/gallery/")
    assert response.status_code == 500
    assert "Failed to fetch gallery images" in response.json()["message"]

    app.dependency_overrides = {}


def test_get_locations(client) -> None:
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
    expected_lat, expected_lng = protect_public_coordinates(10, 10, seed="1")
    assert response.json()[0]["latitude"] == pytest.approx(expected_lat, abs=1e-5)
    assert response.json()[0]["longitude"] == pytest.approx(expected_lng, abs=1e-5)


def test_get_ip_location(client) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"latitude": "13.7563", "longitude": "100.5018"}
    mock_response.raise_for_status.return_value = None

    with (
        patch("routes.geo._cached_ip_location", {"latitude": None, "longitude": None}),
        patch("routes.geo._cached_ip_location_expires_at", 0.0),
        patch("routes.geo._rate_limit_backoff_until", 0.0),
        patch("routes.geo.get_shared_httpx_client") as mock_get_client,
    ):
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        response = client.get("/api/v1/geo/ip-location")

    assert response.status_code == 200
    assert response.json() == {"latitude": 13.7563, "longitude": 100.5018}


def test_get_ip_location_returns_nulls_on_failure(client) -> None:
    with (
        patch("routes.geo._cached_ip_location", {"latitude": None, "longitude": None}),
        patch("routes.geo._cached_ip_location_expires_at", 0.0),
        patch("routes.geo._rate_limit_backoff_until", 0.0),
        patch("routes.geo.get_shared_httpx_client") as mock_get_client,
    ):
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("lookup failed"))
        mock_get_client.return_value = mock_client

        response = client.get("/api/v1/geo/ip-location")

    assert response.status_code == 200
    assert response.json() == {"latitude": None, "longitude": None}


def test_get_ip_location_skips_lookup_during_rate_limit_cooldown(client) -> None:
    request = httpx.Request("GET", "https://ipapi.co/json/")
    response = httpx.Response(429, request=request)
    status_error = httpx.HTTPStatusError("Too Many Requests", request=request, response=response)

    with (
        patch("routes.geo._cached_ip_location", {"latitude": None, "longitude": None}),
        patch("routes.geo._cached_ip_location_expires_at", 0.0),
        patch("routes.geo._rate_limit_backoff_until", 0.0),
        patch("routes.geo.get_shared_httpx_client") as mock_get_client,
    ):
        mock_client = MagicMock()
        mock_client.get = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = status_error
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client

        first_response = client.get("/api/v1/geo/ip-location")
        second_response = client.get("/api/v1/geo/ip-location")

    assert first_response.status_code == 200
    assert first_response.json() == {"latitude": None, "longitude": None}
    assert second_response.status_code == 200
    assert second_response.json() == {"latitude": None, "longitude": None}
    assert mock_client.get.await_count == 1


def test_get_viewport(client) -> None:
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
    expected_lat, expected_lng = protect_public_coordinates(10, 10, seed="1")
    assert response.json()["images"][0]["latitude"] == pytest.approx(expected_lat, abs=1e-5)
    assert response.json()["images"][0]["longitude"] == pytest.approx(expected_lng, abs=1e-5)


def test_get_viewport_accepts_uuid_ids(client) -> None:
    photo_id = uuid4()
    user_id = uuid4()
    mock_service = MagicMock()
    mock_service.get_nearby_photos = AsyncMock(
        return_value=[
            {
                "id": photo_id,
                "user_id": user_id,
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
    data = response.json()
    assert data["images"][0]["id"] == str(photo_id)
    assert data["images"][0]["user_id"] == str(user_id)


def test_search_locations(client) -> None:
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
    expected_lat, expected_lng = protect_public_coordinates(10, 10, seed="1")
    assert response.json()["results"][0]["latitude"] == pytest.approx(expected_lat, abs=1e-5)
    assert response.json()["results"][0]["longitude"] == pytest.approx(expected_lng, abs=1e-5)


def test_get_popular_tags(client) -> None:
    mock_service = MagicMock()
    mock_service.get_popular_tags = AsyncMock(return_value=[{"tag": "cute", "count": 10}])
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    response = client.get("/api/v1/gallery/popular-tags")
    assert response.status_code == 200
    assert len(response.json()["tags"]) == 1


def test_get_photo(client) -> None:
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
    expected_lat, expected_lng = protect_public_coordinates(10, 10, seed="1")
    assert response.json()["latitude"] == pytest.approx(expected_lat, abs=1e-5)
    assert response.json()["longitude"] == pytest.approx(expected_lng, abs=1e-5)


def test_delete_photo(client) -> None:
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
