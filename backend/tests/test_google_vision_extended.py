import io
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from services.google_vision import GoogleVisionService


class TestGoogleVisionServiceExtended:
    @pytest.fixture
    def mock_vision_client(self):
        with patch("google.cloud.vision.ImageAnnotatorClient") as mock_client_cls:
            mock_instance = MagicMock()
            mock_client_cls.from_service_account_info.return_value = mock_instance
            mock_client_cls.from_service_account_json.return_value = mock_instance
            yield mock_instance

    def test_init_with_service_account_env(self, mock_vision_client):
        json_creds = '{"type": "service_account", "project_id": "test"}'
        with patch.dict(os.environ, {"GOOGLE_VISION_SERVICE_ACCOUNT": json_creds}):
            with patch("services.google_vision.VISION_AVAILABLE", True):
                service = GoogleVisionService()
                assert service.is_initialized is True
                assert service.client is not None

    def test_init_with_key_path(self, mock_vision_client):
        with patch.dict(os.environ, {"GOOGLE_VISION_SERVICE_ACCOUNT": "", "GOOGLE_VISION_KEY_PATH": "/tmp/key.json"}):  # noqa: S108
            with patch("os.path.exists", return_value=True):
                with patch("services.google_vision.VISION_AVAILABLE", True):
                    service = GoogleVisionService()
                    assert service.is_initialized is True

    def test_init_fallback(self):
        # When VISION_AVAILABLE is False
        with patch("services.google_vision.VISION_AVAILABLE", False):
            service = GoogleVisionService()
            assert service.is_initialized is False

    def test_detect_cats_success(self, mock_vision_client):
        # Mock vision response
        mock_response = MagicMock()
        mock_response.error.message = None

        label = MagicMock()
        label.description = "cat"
        label.score = 0.95
        mock_response.label_annotations = [label]

        obj = MagicMock()
        obj.name = "Cat"
        obj.score = 0.95
        mock_response.localized_object_annotations = [obj]

        mock_vision_client.label_detection.return_value = mock_response
        mock_vision_client.object_localization.return_value = mock_response

        # Mock upload file
        mock_file = MagicMock()
        mock_file.filename = "cat.jpg"
        mock_file.file.read.side_effect = [b"imagedata", b""]  # Chunked read

        with patch.dict(os.environ, {"GOOGLE_VISION_SERVICE_ACCOUNT": "{}"}):
            with patch("services.google_vision.VISION_AVAILABLE", True):
                service = GoogleVisionService()
                # Bypass init logic since we mocked client class
                service.client = mock_vision_client
                service.is_initialized = True

                result = service.detect_cats(mock_file)
                assert result["has_cats"] is True
                assert result["confidence"] > 90

    def test_fallback_cat_detection(self):
        # Mock PIL
        with patch("PIL.Image.open") as mock_open_img:
            mock_img = MagicMock()
            mock_img.size = (800, 600)
            mock_img.format = "JPEG"
            mock_open_img.return_value = mock_img

            mock_file = MagicMock()
            mock_file.filename = "kitty.jpg"
            mock_file.file.read.return_value = b"fakeimage"

            # Init service in fallback mode
            with patch("services.google_vision.VISION_AVAILABLE", False):
                service = GoogleVisionService()

                result = service.detect_cats(mock_file)
                assert result["has_cats"] is True, f"Result: {result}"
                assert result["reasoning"].startswith("Fallback detection")

    def test_analyze_suitability(self, mock_vision_client):
        # Setup detect_cats to return specific result
        service = GoogleVisionService()
        service.detect_cats = MagicMock(return_value={"has_cats": True, "labels": ["park", "tree", "grass"]})

        result = service.analyze_cat_spot_suitability(MagicMock())
        assert result["environment_type"] == "Public park"
        assert result["suitability_score"] > 50
