import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from middleware.auth_middleware import get_current_user
from user_models.user import User

client = TestClient(app)

# Helper to mock auth
async def mock_get_current_user():
    return User(id="test-user", email="test@test.com", name="Test User", created_at=None)

class TestCatDetectionRouteExtended:
    
    @pytest.fixture
    def override_auth(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield
        app.dependency_overrides = {}

    def test_detect_cats_endpoint_success(self, override_auth):
        mock_vision = MagicMock()
        mock_vision.detect_cats.return_value = {
            "has_cats": True,
            "confidence": 95.0,
            "cat_count": 1,
            "labels": ["cat"],
            "cat_labels": [{"description": "cat", "score": 95.0}],
            "cat_objects": [],
            "image_quality": "Good",
            "reasoning": "Test"
        }
        
        with patch("services.google_vision.GoogleVisionService.detect_cats", side_effect=mock_vision.detect_cats):
             # Remove patch for save_detection_result as it doesn't exist
             files = {"file": ("cat.jpg", b"fakeimage", "image/jpeg")}
             # URL is /api/v1/detect/cats based on router prefix /api/v1 + /detect + /cats
             response = client.post("/api/v1/detect/cats", files=files)
             assert response.status_code == 200
             assert response.json()["has_cats"] is True

    def test_detect_cats_endpoint_no_cat(self, override_auth):
        mock_vision = MagicMock()
        mock_vision.detect_cats.return_value = {
            "has_cats": False,
            "confidence": 10.0,
            "cat_count": 0,
            "labels": ["dog"],
            "cat_labels": [],
            "cat_objects": [],
            "image_quality": "Good",
            "reasoning": "It is a dog"
        }
        
        with patch("services.google_vision.GoogleVisionService.detect_cats", side_effect=mock_vision.detect_cats):
             files = {"file": ("dog.jpg", b"fakeimage", "image/jpeg")}
             response = client.post("/api/v1/detect/cats", files=files)
             assert response.status_code == 200
             assert response.json()["has_cats"] is False

    def test_analyze_suitability_endpoint(self, override_auth):
        mock_vision = MagicMock()
        mock_vision.analyze_cat_spot_suitability.return_value = {
            "suitability_score": 80,
            "environment_type": "Park",
            "safety_factors": {
                "safe_from_traffic": True,
                "has_shelter": True,
                "food_source_nearby": False,
                "water_access": False,
                "escape_routes": True
            },
            "pros": [],
            "cons": [],
            "recommendations": [],
            "best_times": []
        }
        
        with patch("services.google_vision.GoogleVisionService.analyze_cat_spot_suitability", side_effect=mock_vision.analyze_cat_spot_suitability):
             files = {"file": ("park.jpg", b"fakeimage", "image/jpeg")}
             response = client.post("/api/v1/detect/spot-analysis", files=files)
             assert response.status_code == 200
             assert response.json()["suitability_score"] == 80
