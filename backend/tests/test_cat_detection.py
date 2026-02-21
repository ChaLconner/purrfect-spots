"""
Tests for cat detection service
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCatDetectionService:
    """Test suite for CatDetectionService"""

    @pytest.fixture
    def detection_service(self):
        """Create CatDetectionService instance with mocked vision service"""
        # Patch at the location where GoogleVisionService is imported
        with patch("services.google_vision.GoogleVisionService") as MockVision:
            mock_vision = MagicMock()
            MockVision.return_value = mock_vision

            from services.cat_detection_service import CatDetectionService

            service = CatDetectionService()
            service.vision_service = mock_vision
            return service

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile"""
        mock_file = MagicMock()
        mock_file.filename = "cat_photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read = MagicMock(return_value=b"fake image data")
        mock_file.seek = MagicMock()
        return mock_file

    async def test_detect_cats_with_cats(self, detection_service, mock_upload_file):
        """Test cat detection when cats are present"""
        detection_service.vision_service.detect_cats = AsyncMock(
            return_value={
                "has_cats": True,
                "cat_count": 2,
                "confidence": 95,
                "cat_objects": [
                    {"name": "cat", "score": 0.95},
                    {"name": "cat", "score": 0.88},
                ],
                "cat_labels": [],
                "image_quality": "Good",
                "reasoning": "Clear image with visible cats",
            }
        )

        result = await detection_service.detect_cats(mock_upload_file)

        assert result["has_cats"] is True
        assert result["cat_count"] == 2
        assert result["confidence"] >= 90

    async def test_detect_cats_no_cats(self, detection_service, mock_upload_file):
        """Test cat detection when no cats are present"""
        detection_service.vision_service.detect_cats = AsyncMock(
            return_value={
                "has_cats": False,
                "cat_count": 0,
                "confidence": 0,
                "cat_objects": [],
                "cat_labels": [],
                "image_quality": "Good",
                "reasoning": "No cats detected in image",
            }
        )

        result = await detection_service.detect_cats(mock_upload_file)

        assert result["has_cats"] is False
        assert result["cat_count"] == 0

    async def test_analyze_cat_spot_suitability(self, detection_service, mock_upload_file):
        """Test spot analysis for suitable location"""
        detection_service.vision_service.analyze_cat_spot_suitability = AsyncMock(
            return_value={
                "suitability_score": 85,
                "environment_type": "park",
                "pros": ["Shaded area", "Near water"],
                "cons": ["Near road"],
                "recommendations": ["Add shelter"],
                "best_times": ["Morning", "Evening"],
            }
        )

        result = await detection_service.analyze_cat_spot_suitability(mock_upload_file)

        assert result["suitability_score"] >= 80
        assert result["environment_type"] == "park"

    async def test_detect_cats_error_handling(self, detection_service, mock_upload_file):
        """Test error handling in cat detection"""
        detection_service.vision_service.detect_cats = AsyncMock(side_effect=Exception("Vision API error"))

        result = await detection_service.detect_cats(mock_upload_file)

        assert result["fallback_active"] is True
        assert result["has_cats"] is True
        assert result["confidence"] == 0
        assert "Fallback mode active" in result["reasoning"]

    def test_prepare_image(self, detection_service):
        """Test image preparation"""
        from PIL import Image

        # Create a test image
        img = Image.new("RGBA", (2000, 1500), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = detection_service.prepare_image(image_bytes)

        # Should be converted to RGB and resized
        assert result.mode == "RGB"
        assert max(result.size) <= 1024


class TestGoogleVisionServiceInit:
    """Test Google Vision Service initialization"""

    def test_cat_label_keywords_exist(self):
        """Test that cat keywords are defined"""
        with patch.dict("os.environ", {"GOOGLE_VISION_KEY_PATH": "dummy/path.json"}):
            with patch("google.cloud.vision.ImageAnnotatorClient"):
                from services.google_vision import GoogleVisionService

                service = GoogleVisionService()

                assert hasattr(service, "CAT_LABEL_KEYWORDS")
                assert "cat" in service.CAT_LABEL_KEYWORDS
                assert "kitten" in service.CAT_LABEL_KEYWORDS

    def test_confidence_thresholds_valid(self):
        """Test confidence threshold values are valid"""
        with patch.dict("os.environ", {"GOOGLE_VISION_KEY_PATH": "dummy/path.json"}):
            with patch("google.cloud.vision.ImageAnnotatorClient"):
                from services.google_vision import GoogleVisionService

                service = GoogleVisionService()

                assert 0 <= service.CAT_LABEL_SCORE_THRESHOLD <= 1
                assert 0 <= service.CAT_OBJECT_SCORE_THRESHOLD <= 1
