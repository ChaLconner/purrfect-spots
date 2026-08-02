import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.middleware.auth_middleware import get_current_user
from app.schemas.user import User

client = TestClient(app)


def get_valid_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# Helper to mock auth
def mock_get_current_user():
    return User(id="test-user", email="test@test.com", name="Test User", created_at=None)


class TestCatDetectionRouteExtended:
    @pytest.fixture
    def override_auth(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield
        app.dependency_overrides = {}

    def test_detect_cats_endpoint_success(self, override_auth) -> None:
        mock_vision = MagicMock()
        mock_vision.detect_cats.return_value = {
            "has_cats": True,
            "confidence": 95.0,
            "cat_count": 1,
            "labels": ["cat"],
            "cat_labels": [{"description": "cat", "score": 95.0}],
            "cat_objects": [],
            "image_quality": "Good",
            "reasoning": "Test",
        }

        with patch("app.services.google_vision.GoogleVisionService.detect_cats", side_effect=mock_vision.detect_cats):
            files = {"file": ("cat.jpg", get_valid_jpeg_bytes(), "image/jpeg")}
            response = client.post("/api/v1/detect/cats", files=files)
            assert response.status_code == 200
            assert response.json()["has_cats"] is True

    def test_detect_cats_endpoint_no_cat(self, override_auth) -> None:
        mock_vision = MagicMock()
        mock_vision.detect_cats.return_value = {
            "has_cats": False,
            "confidence": 10.0,
            "cat_count": 0,
            "labels": ["dog"],
            "cat_labels": [],
            "cat_objects": [],
            "image_quality": "Good",
            "reasoning": "It is a dog",
        }

        with patch("app.services.google_vision.GoogleVisionService.detect_cats", side_effect=mock_vision.detect_cats):
            files = {"file": ("dog.jpg", get_valid_jpeg_bytes(), "image/jpeg")}
            response = client.post("/api/v1/detect/cats", files=files)
            assert response.status_code == 200
            assert response.json()["has_cats"] is False

    def test_detect_cats_endpoint_reports_service_unavailable(self, override_auth) -> None:
        from app.dependencies import get_cat_detection_service

        mock_detection_service = MagicMock()
        mock_detection_service.detect_cats = AsyncMock(
            return_value={
                "has_cats": False,
                "cat_count": 0,
                "confidence": 0,
                "cats_detected": [],
                "image_quality": "Unknown",
                "suitable_for_cat_spot": False,
                "reasoning": "Cat verification service unavailable. Please try again later.",
                "service_available": False,
                "fallback_active": True,
            }
        )
        app.dependency_overrides[get_cat_detection_service] = lambda: mock_detection_service

        files = {"file": ("cat.jpg", get_valid_jpeg_bytes(), "image/jpeg")}
        response = client.post("/api/v1/detect/cats", files=files)

        assert response.status_code == 503
        assert response.json()["detail"] == "Cat verification service unavailable. Please try again later."

    def test_analyze_suitability_endpoint(self, override_auth) -> None:
        mock_vision = MagicMock()
        mock_vision.analyze_cat_spot_suitability.return_value = {
            "suitability_score": 80,
            "environment_type": "Park",
            "safety_factors": {
                "safe_from_traffic": True,
                "has_shelter": True,
                "food_source_nearby": False,
                "water_access": False,
                "escape_routes": True,
            },
            "pros": [],
            "cons": [],
            "recommendations": [],
            "best_times": [],
        }

        with patch(
            "app.services.google_vision.GoogleVisionService.analyze_cat_spot_suitability",
            side_effect=mock_vision.analyze_cat_spot_suitability,
        ):
            files = {"file": ("park.jpg", get_valid_jpeg_bytes(), "image/jpeg")}
            response = client.post("/api/v1/detect/spot-analysis", files=files)
            assert response.status_code == 200
            assert response.json()["suitability_score"] == 80
