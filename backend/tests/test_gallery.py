"""
Original gallery tests - updated for new pagination API
"""
from unittest.mock import MagicMock
from main import app
from routes.gallery import get_gallery_service

def test_get_gallery_empty(client):
    """Test gallery endpoint returns empty list when no photos exist"""
    mock_service = MagicMock()
    mock_service.get_all_photos.return_value = {
        "data": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
        "has_more": False
    }
    
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
    mock_service.get_all_photos.return_value = {
        "data": [mock_cat_photo],
        "total": 1,
        "limit": 20,
        "offset": 0,
        "has_more": False
    }
    
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
    mock_service.get_all_photos.side_effect = Exception("Database error")
    
    app.dependency_overrides[get_gallery_service] = lambda: mock_service
    
    response = client.get("/api/v1/gallery/")
    assert response.status_code == 500
    assert "Failed to fetch gallery images" in response.json()["detail"]
    
    app.dependency_overrides = {}
