"""
Tests for file processing utilities
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile


class TestProcessUploadedImage:
    """Test process_uploaded_image function"""

    @pytest.fixture
    def create_mock_upload_file(self):
        """Factory fixture for creating mock upload files"""

        def _create(content: bytes, filename: str = "test.jpg", content_type: str = "image/jpeg"):
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.read = AsyncMock(return_value=content)
            mock_file.seek = AsyncMock()

            # Setup file.file for streaming upload logic
            mock_inner_file = MagicMock()
            mock_inner_file.tell.return_value = len(content)
            mock_file.file = mock_inner_file

            return mock_file

        return _create

    @pytest.mark.asyncio
    async def test_process_valid_jpeg(self, create_mock_upload_file, sample_image_bytes):
        """Test processing a valid JPEG image"""
        mock_file = create_mock_upload_file(sample_image_bytes, "cat.jpg", "image/jpeg")

        with patch("utils.file_processing.validate_image_file"):
            with patch("utils.file_processing.is_valid_image", return_value=True):
                with patch("utils.file_processing.optimize_image") as mock_optimize:
                    mock_optimize.return_value = (sample_image_bytes, "image/jpeg")
                    with patch(
                        "utils.file_processing.get_safe_file_extension",
                        return_value=".jpg",
                    ):
                        from utils.file_processing import process_uploaded_image

                        (
                            contents,
                            content_type,
                            extension,
                        ) = await process_uploaded_image(mock_file, optimize=False)

                        assert contents == mock_file.file
                        assert content_type == "image/jpeg"
                        assert extension == "jpg"

    @pytest.mark.asyncio
    async def test_process_invalid_file_type(self, create_mock_upload_file):
        """Test rejection of invalid file types"""
        mock_file = create_mock_upload_file(b"not an image", "test.txt", "text/plain")

        with patch("utils.file_processing.validate_image_file") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid file type")

            from utils.file_processing import process_uploaded_image

            with pytest.raises(HTTPException) as excinfo:
                await process_uploaded_image(mock_file)

            assert excinfo.value.status_code == 400

    @pytest.mark.asyncio
    async def test_process_file_too_large(self, create_mock_upload_file):
        """Test rejection of files exceeding size limit"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        mock_file = create_mock_upload_file(large_content, "large.jpg", "image/jpeg")

        with patch("utils.file_processing.validate_image_file") as mock_validate:
            mock_validate.side_effect = ValueError("File too large")

            from utils.file_processing import process_uploaded_image

            with pytest.raises(HTTPException) as excinfo:
                await process_uploaded_image(mock_file)

            assert excinfo.value.status_code == 400

    @pytest.mark.asyncio
    async def test_process_corrupted_image(self, create_mock_upload_file):
        """Test rejection of corrupted image files"""
        mock_file = create_mock_upload_file(b"corrupted data", "test.jpg", "image/jpeg")

        with patch("utils.file_processing.validate_image_file"):
            with patch("utils.file_processing.is_valid_image", return_value=False):
                from utils.file_processing import process_uploaded_image

                with pytest.raises(HTTPException) as excinfo:
                    await process_uploaded_image(mock_file)

                assert excinfo.value.status_code == 400
                assert "invalid" in excinfo.value.detail.lower() or "corrupted" in excinfo.value.detail.lower()

    @pytest.mark.asyncio
    async def test_process_without_optimization(self, create_mock_upload_file, sample_image_bytes):
        """Test processing without optimization"""
        mock_file = create_mock_upload_file(sample_image_bytes, "cat.jpg", "image/jpeg")

        with patch("utils.file_processing.validate_image_file"):
            with patch("utils.file_processing.is_valid_image", return_value=True):
                with patch("utils.file_processing.optimize_image") as mock_optimize:
                    with patch(
                        "utils.file_processing.get_safe_file_extension",
                        return_value=".jpg",
                    ):
                        from utils.file_processing import process_uploaded_image

                        await process_uploaded_image(mock_file, optimize=False)

                        # optimize_image should not be called
                        mock_optimize.assert_not_called()


class TestReadFileForDetection:
    """Test read_file_for_detection function"""

    @pytest.mark.asyncio
    async def test_read_valid_file(self, sample_image_bytes):
        """Test reading a valid file for detection"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=sample_image_bytes)
        mock_file.seek = AsyncMock()

        with patch("utils.file_processing.validate_image_file"):
            from utils.file_processing import read_file_for_detection

            contents = await read_file_for_detection(mock_file)

            assert contents == sample_image_bytes
            mock_file.seek.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_read_invalid_file(self):
        """Test reading an invalid file for detection"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"text content")

        with patch("utils.file_processing.validate_image_file") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid file type")

            from utils.file_processing import read_file_for_detection

            with pytest.raises(HTTPException) as excinfo:
                await read_file_for_detection(mock_file)

            assert excinfo.value.status_code == 400


class TestValidateCoordinates:
    """Test validate_coordinates function"""

    def test_valid_coordinates(self):
        """Test with valid latitude and longitude"""
        from utils.file_processing import validate_coordinates

        lat, lng = validate_coordinates("13.7563", "100.5018")

        assert lat == pytest.approx(13.7563)
        assert lng == pytest.approx(100.5018)

    def test_valid_negative_coordinates(self):
        """Test with valid negative coordinates"""
        from utils.file_processing import validate_coordinates

        lat, lng = validate_coordinates("-33.8688", "151.2093")

        assert lat == pytest.approx(-33.8688)
        assert lng == pytest.approx(151.2093)

    def test_boundary_coordinates(self):
        """Test with boundary values"""
        from utils.file_processing import validate_coordinates

        # Test maximum values
        lat, lng = validate_coordinates("90", "180")
        assert lat == pytest.approx(90)
        assert lng == pytest.approx(180)

        # Test minimum values
        lat, lng = validate_coordinates("-90", "-180")
        assert lat == pytest.approx(-90)
        assert lng == pytest.approx(-180)

    def test_invalid_latitude_too_high(self):
        """Test rejection of latitude > 90"""
        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("91", "100")

        assert excinfo.value.status_code == 400
        assert "Latitude" in excinfo.value.detail

    def test_invalid_latitude_too_low(self):
        """Test rejection of latitude < -90"""
        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("-91", "100")

        assert excinfo.value.status_code == 400

    def test_invalid_longitude_too_high(self):
        """Test rejection of longitude > 180"""
        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("45", "181")

        assert excinfo.value.status_code == 400
        assert "Longitude" in excinfo.value.detail

    def test_invalid_longitude_too_low(self):
        """Test rejection of longitude < -180"""
        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("45", "-181")

        assert excinfo.value.status_code == 400

    def test_non_numeric_coordinates(self):
        """Test rejection of non-numeric coordinates"""
        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("abc", "100")

        assert excinfo.value.status_code == 400
        assert "Invalid coordinate format" in excinfo.value.detail


class TestValidateLocationData:
    """Test validate_location_data function"""

    def test_valid_location_data(self):
        """Test with valid location name and description"""
        from utils.file_processing import validate_location_data

        name, desc = validate_location_data("Cat Park", "A nice park with cats")

        assert name == "Cat Park"
        assert desc == "A nice park with cats"

    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        from utils.file_processing import validate_location_data

        name, desc = validate_location_data("  Cat Park  ", "  Description  ")

        assert name == "Cat Park"
        assert desc == "Description"

    def test_empty_description_allowed(self):
        """Test that empty description is allowed"""
        from utils.file_processing import validate_location_data

        name, desc = validate_location_data("Cat Park", "")

        assert name == "Cat Park"
        assert desc == ""

    def test_none_description_allowed(self):
        """Test that None description is allowed"""
        from utils.file_processing import validate_location_data

        name, desc = validate_location_data("Cat Park", None)

        assert name == "Cat Park"
        assert desc == ""

    def test_empty_location_name_rejected(self):
        """Test rejection of empty location name"""
        from utils.file_processing import validate_location_data

        with pytest.raises(HTTPException) as excinfo:
            validate_location_data("", "Description")

        assert excinfo.value.status_code == 400
        assert "required" in excinfo.value.detail.lower()

    def test_whitespace_only_name_rejected(self):
        """Test rejection of whitespace-only location name"""
        from utils.file_processing import validate_location_data

        with pytest.raises(HTTPException) as excinfo:
            validate_location_data("   ", "Description")

        assert excinfo.value.status_code == 400

    def test_short_location_name_rejected(self):
        """Test rejection of location name shorter than 3 characters"""
        from utils.file_processing import validate_location_data

        with pytest.raises(HTTPException) as excinfo:
            validate_location_data("AB", "Description")

        assert excinfo.value.status_code == 400
        assert "3 characters" in excinfo.value.detail

    def test_long_location_name_truncated(self):
        """Test truncation of location name longer than 100 characters"""
        from utils.file_processing import validate_location_data

        long_name = "A" * 101

        name, _ = validate_location_data(long_name, "Description")

        assert len(name) == 100
        assert name == "A" * 100

    def test_long_description_truncated(self):
        """Test truncation of description longer than 1000 characters"""
        from utils.file_processing import validate_location_data

        long_desc = "A" * 1001

        _, desc = validate_location_data("Cat Park", long_desc)

        assert len(desc) == 1000
        assert desc == "A" * 1000

    def test_boundary_location_name_length(self):
        """Test boundary cases for location name length"""
        from utils.file_processing import validate_location_data

        # Exactly 3 characters - should pass
        name, _ = validate_location_data("ABC", "")
        assert name == "ABC"

        # Exactly 100 characters - should pass
        long_name = "A" * 100
        name, _ = validate_location_data(long_name, "")
        assert name == long_name
