import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from services.cat_detection_service import CatDetectionService


class TestCatDetectionServiceExtended:
    """Extended test suite for CatDetectionService"""

    @pytest.fixture
    def mock_vision_service(self):
        with patch("services.google_vision.GoogleVisionService") as mock:
            yield mock.return_value

    @pytest.fixture
    def service(self, mock_vision_service):
        # We need to patch the import inside __init__ or patch where it's used
        with patch("services.cat_detection_service.CatDetectionService.__init__", return_value=None):
            service = CatDetectionService()
            service.vision_service = mock_vision_service
            return service

    @pytest.fixture
    def mock_upload_file(self):
        file = MagicMock(spec=UploadFile)
        file.filename = "test_cat.jpg"
        return file

    def test_prepare_image(self):
        # Create a real image for testing
        img = Image.new("RGB", (2000, 2000), color="red")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_bytes = img_byte_arr.getvalue()

        # Instantiate service normally to test the method
        with patch("services.google_vision.GoogleVisionService"):
            service = CatDetectionService()

        processed_img = service.prepare_image(img_bytes)

        # Check resizing logic (max 1024x1024)
        assert processed_img.size[0] <= 1024
        assert processed_img.size[1] <= 1024

        # Check invalid image
        with pytest.raises(HTTPException):
            service.prepare_image(b"invalid_bytes")

    @pytest.mark.asyncio
    async def test_detect_cats_success(self, service, mock_vision_service, mock_upload_file):
        # Mock vision result
        mock_vision_result = {
            "has_cats": True,
            "cat_count": 1,
            "confidence": 95.0,
            "cat_objects": [{"name": "Cat", "score": 0.95}],
            "image_quality": "Good",
            "reasoning": "Found a cat",
        }
        mock_vision_service.detect_cats.return_value = mock_vision_result

        result = service.detect_cats(mock_upload_file)

        assert result["has_cats"] is True
        assert result["confidence"] == 95
        assert len(result["cats_detected"]) == 1
        assert result["cats_detected"][0]["description"] == "Detected Cat"

    @pytest.mark.asyncio
    async def test_detect_cats_labels_fallback(self, service, mock_vision_service, mock_upload_file):
        # Mock vision result with ONLY labels, no objects
        mock_vision_result = {
            "has_cats": True,
            "cat_count": 1,
            "confidence": 80.0,
            "cat_objects": [],
            "cat_labels": [{"description": "Tabby", "score": 0.8}],
            "image_quality": "Medium",
            "reasoning": "Found cat label",
        }
        mock_vision_service.detect_cats.return_value = mock_vision_result

        result = service.detect_cats(mock_upload_file)

        assert result["has_cats"] is True
        assert len(result["cats_detected"]) == 1
        assert result["cats_detected"][0]["description"] == "Detected Tabby"

    @pytest.mark.asyncio
    async def test_detect_cats_error(self, service, mock_vision_service, mock_upload_file):
        mock_vision_service.detect_cats.side_effect = Exception("Vision API Error")

        with pytest.raises(HTTPException) as excinfo:
            service.detect_cats(mock_upload_file)

        assert excinfo.value.status_code == 500
        assert "Cat detection failed" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_analyze_spot_suitability(self, service, mock_vision_service, mock_upload_file):
        mock_result = {"suitability_score": 80}
        mock_vision_service.analyze_cat_spot_suitability.return_value = mock_result

        result = service.analyze_cat_spot_suitability(mock_upload_file)
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_analyze_spot_suitability_error(self, service, mock_vision_service, mock_upload_file):
        mock_vision_service.analyze_cat_spot_suitability.side_effect = Exception("Analysis Error")

        with pytest.raises(HTTPException) as excinfo:
            service.analyze_cat_spot_suitability(mock_upload_file)

        assert excinfo.value.status_code == 500
