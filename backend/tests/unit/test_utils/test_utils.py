"""
Tests for utility functions

# nosec python:S1313 - Hardcoded IP addresses are intentional test fixtures
# These are private/test IPs used only for unit testing, not real addresses
"""

import io
from unittest.mock import MagicMock, patch

import pytest


class TestFileProcessing:
    """Test suite for file processing utilities"""

    def test_validate_coordinates_valid(self) -> None:
        """Test coordinate validation with valid values"""
        from utils.file_processing import validate_coordinates

        lat, lng = validate_coordinates("13.7563", "100.5018")

        assert lat == pytest.approx(13.7563)
        assert lng == pytest.approx(100.5018)

    def test_validate_coordinates_invalid_lat(self) -> None:
        """Test coordinate validation with invalid latitude"""
        from fastapi import HTTPException

        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("91", "100")  # Lat > 90
        assert excinfo.value.status_code == 400

    def test_validate_coordinates_invalid_lng(self) -> None:
        """Test coordinate validation with invalid longitude"""
        from fastapi import HTTPException

        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("13", "181")  # Lng > 180
        assert excinfo.value.status_code == 400

    def test_validate_coordinates_non_numeric(self) -> None:
        """Test coordinate validation with non-numeric values"""
        from fastapi import HTTPException

        from utils.file_processing import validate_coordinates

        with pytest.raises(HTTPException) as excinfo:
            validate_coordinates("abc", "100")
        assert excinfo.value.status_code == 400

    def test_validate_location_data(self) -> None:
        """Test location data validation and cleaning"""
        from utils.file_processing import validate_location_data

        location, description = validate_location_data("  Test Location  ", "  Test description  ")

        assert location == "Test Location"
        assert description == "Test description"

    def test_validate_location_data_empty_name(self) -> None:
        """Test location validation with empty name"""
        from fastapi import HTTPException

        from utils.file_processing import validate_location_data

        with pytest.raises(HTTPException) as excinfo:
            validate_location_data("", "description")
        assert excinfo.value.status_code == 400

    def test_validate_location_data_long_name(self) -> None:
        """Test location validation with long name truncates it"""
        from utils.file_processing import validate_location_data

        long_name = "A" * 300  # Very long name

        # Should truncate, not raise error
        name, _ = validate_location_data(long_name, "desc")

        assert len(name) == 100
        assert name == "A" * 100


class TestImageUtils:
    """Test suite for image utility functions"""

    def test_get_image_dimensions_valid(self) -> None:
        """Test getting image dimensions from valid image"""
        from PIL import Image

        from utils.image_utils import get_image_dimensions

        # Create a real test image
        img = Image.new("RGB", (1920, 1080), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        width, height = get_image_dimensions(image_bytes)

        assert width == 1920
        assert height == 1080

    def test_get_image_dimensions_invalid(self) -> None:
        """Test getting image dimensions from invalid data"""
        from utils.image_utils import get_image_dimensions

        width, height = get_image_dimensions(b"not an image")

        # Should return (0, 0) for invalid images
        assert width == 0
        assert height == 0

    @patch("utils.image_utils.logger")
    def test_optimize_image(self, mock_logger) -> None:
        """Test image optimization default behavior (JPEG)"""
        from PIL import Image

        from utils.image_utils import optimize_image

        # Create a test image
        img = Image.new("RGB", (3000, 2000), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=100)
        original_bytes = buffer.getvalue()

        optimized_bytes, content_type = optimize_image(original_bytes, "image/jpeg", max_dimension=1920)

        assert optimized_bytes is not None
        assert content_type == "image/webp"
        # Optimized should be resized
        opt_img = Image.open(io.BytesIO(optimized_bytes))
        assert max(opt_img.size) <= 1920

    def test_optimize_image_rgba(self) -> None:
        """Test optimization of RGBA images (transparency to white bg)"""
        from PIL import Image

        from utils.image_utils import optimize_image

        # Create RGBA image
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        optimized_bytes, content_type = optimize_image(buffer.getvalue(), "image/png")

        # Should convert to WebP (default) and handle transparency
        assert content_type == "image/webp"
        opt_img = Image.open(io.BytesIO(optimized_bytes))
        assert opt_img.mode == "RGB"

    def test_optimize_image_vertical_resize(self) -> None:
        """Test resizing logic for tall images"""
        from PIL import Image

        from utils.image_utils import optimize_image

        img = Image.new("RGB", (1000, 3000), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")

        optimized_bytes, _ = optimize_image(
            buffer.getvalue(),
            "image/jpeg",
            max_dimension=1000,  # Restrict to 1000
        )

        opt_img = Image.open(io.BytesIO(optimized_bytes))
        w, h = opt_img.size
        assert h == 1000
        assert w < 1000  # Aspect ratio preserved (approx 333)

    def test_optimize_image_target_format_webp(self) -> None:
        """Test forcing WEBP format"""
        from PIL import Image

        from utils.image_utils import optimize_image

        img = Image.new("RGB", (100, 100), color="yellow")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")

        optimized_bytes, content_type = optimize_image(buffer.getvalue(), "image/jpeg", target_format="WEBP")

        assert content_type == "image/webp"
        opt_img = Image.open(io.BytesIO(optimized_bytes))
        assert opt_img.format == "WEBP"

    def test_optimize_image_gif_passthrough(self) -> None:
        """Test GIF images are passed through untouched"""
        from PIL import Image

        from utils.image_utils import optimize_image

        # Create a simple GIF
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="GIF")
        original_bytes = buffer.getvalue()

        optimized_bytes, _ = optimize_image(original_bytes, "image/gif")

        # Should return original
        assert optimized_bytes == original_bytes
        # Content type might be normalized but check behavior

    def test_optimize_image_corrupted(self) -> None:
        """Test graceful handling of corrupted images"""
        from utils.image_utils import optimize_image

        bad_data = b"not an image"

        optimized_bytes, content_type = optimize_image(bad_data, "image/jpeg")

        # Should return original data on failure
        assert optimized_bytes == bad_data
        assert content_type == "image/jpeg"

    def test_is_valid_image(self) -> None:
        """Test image validation"""
        from PIL import Image

        from utils.image_utils import is_valid_image

        # Valid image
        img = Image.new("RGB", (100, 100), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        assert is_valid_image(buffer.getvalue()) is True

        # Invalid data
        assert is_valid_image(b"not an image") is False


class TestFileUtils:
    """Test suite for file utilities"""

    def test_get_safe_file_extension_from_content_type(self) -> None:
        """Test getting file extension from content type"""
        from utils.file_utils import get_safe_file_extension

        assert get_safe_file_extension("photo.jpg", "image/jpeg") == ".jpg"
        assert get_safe_file_extension("photo.png", "image/png") == ".png"
        assert get_safe_file_extension("photo.gif", "image/gif") == ".gif"
        assert get_safe_file_extension("photo.webp", "image/webp") == ".webp"

    def test_get_safe_file_extension_fallback(self) -> None:
        """Test file extension fallback to filename"""
        from utils.file_utils import get_safe_file_extension

        # Should fallback to filename extension if content type unknown
        ext = get_safe_file_extension("photo.jpeg", "application/octet-stream")
        assert ext in [".jpeg", ".jpg"]

    def test_validate_image_file_valid(self) -> None:
        """Test image file validation with valid params"""
        from utils.file_utils import validate_image_file

        # Should not raise
        validate_image_file("image/jpeg", 1024 * 1024)  # 1MB

    def test_validate_image_file_too_large(self) -> None:
        """Test image file validation with file too large"""
        from utils.file_utils import validate_image_file

        with pytest.raises(ValueError):
            validate_image_file("image/jpeg", 15 * 1024 * 1024)  # 15MB

    def test_validate_image_file_wrong_type(self) -> None:
        """Test image file validation with wrong content type"""
        from utils.file_utils import validate_image_file

        with pytest.raises(ValueError):
            validate_image_file("application/pdf", 1024 * 1024)


class TestRateLimiter:
    """Test suite for rate limiter"""

    def test_get_user_id_from_request_authenticated(self) -> None:
        """Test user ID extraction from authenticated request"""
        import jwt

        from limiter import get_user_id_from_request

        # Create a valid JWT token for testing
        with patch("config.config.JWT_SECRET", "secret_key_at_least_32_chars_long_for_security"):
            token = jwt.encode(
                {"sub": "user-123", "iss": "purrfect-spots"},
                "secret_key_at_least_32_chars_long_for_security",
                algorithm="HS256",
            )

            mock_request = MagicMock()
            mock_request.headers.get.return_value = f"Bearer {token}"
            mock_request.client.host = "127.0.0.1"

            result = get_user_id_from_request(mock_request)

        assert result == "user:user-123"

    def test_get_user_id_from_request_unauthenticated(self) -> None:
        """Test user ID extraction from unauthenticated request"""
        from limiter import get_user_id_from_request

        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""
        mock_request.client.host = "192.168.1.1"

        result = get_user_id_from_request(mock_request)

        # Should fall back to IP
        assert result == "192.168.1.1"


class TestAuthUtils:
    """Test suite for authentication utilities"""

    def test_decode_token_missing(self) -> None:
        """Test decoding missing token"""
        from utils.auth_utils import decode_token

        with pytest.raises(ValueError, match="Token is missing"):
            decode_token("")

    def test_decode_token_valid(self) -> None:
        """Test decoding valid token"""
        import jwt

        from utils.auth_utils import decode_token

        secret = "test_secret_key_at_least_32_chars"
        payload = {"sub": "user123"}
        token = jwt.encode(payload, secret, algorithm="HS256")

        with patch("config.config.JWT_SECRET", secret):
            decoded = decode_token(token)
            assert decoded["sub"] == "user123"

    def test_decode_token_expired(self) -> None:
        """Test decoding expired token"""
        import time

        import jwt

        from utils.auth_utils import decode_token

        secret = "test_secret_key_at_least_32_chars"
        payload = {"sub": "user123", "exp": int(time.time()) - 3600}
        token = jwt.encode(payload, secret, algorithm="HS256")

        with patch("config.config.JWT_SECRET", secret), pytest.raises(ValueError, match="Token has expired"):
            decode_token(token)

    def test_decode_token_invalid_secret(self) -> None:
        """Test decoding token with invalid secret"""
        import jwt

        from utils.auth_utils import decode_token

        secret = "test_secret_key_at_least_32_chars"
        payload = {"sub": "user123"}
        token = jwt.encode(payload, secret, algorithm="HS256")

        with (
            patch("config.config.JWT_SECRET", "different_secret_key_at_least_32_chars"),
            pytest.raises(ValueError, match="Invalid token"),
        ):
            decode_token(token)

    def test_get_client_info(self) -> None:
        """Test extracting client info from request"""
        from utils.auth_utils import get_client_info

        mock_request = MagicMock()
        mock_request.client.host = "1.2.3.4"
        mock_request.headers = {"user-agent": "test-agent"}

        ip, ua = get_client_info(mock_request)
        assert ip == "1.2.3.4"
        assert ua == "test-agent"

    def test_get_client_info_forwarded(self) -> None:
        """Test extracting client info with X-Forwarded-For"""
        from utils.auth_utils import get_client_info

        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "5.6.7.8, 1.2.3.4"}
        mock_request.client = None

        ip, _ = get_client_info(mock_request)
        assert ip == "5.6.7.8"

    def test_get_client_info_real_ip(self) -> None:
        """Test extracting client info with X-Real-IP"""
        from utils.auth_utils import get_client_info

        mock_request = MagicMock()
        mock_request.headers = {"X-Real-IP": "9.10.11.12"}
        mock_request.client = None

        ip, _ = get_client_info(mock_request)
        assert ip == "9.10.11.12"

    def test_set_refresh_cookie(self) -> None:
        """Test setting refresh cookie on response"""
        from utils.auth_utils import set_refresh_cookie

        mock_response = MagicMock()
        with (
            patch("config.config.JWT_REFRESH_EXPIRATION_DAYS", 7),
            patch("config.config.is_production", return_value=False),
        ):
            set_refresh_cookie(mock_response, "refresh-123")

        mock_response.set_cookie.assert_called_once()
        args, kwargs = mock_response.set_cookie.call_args
        assert kwargs["key"] == "refresh_token"
        assert kwargs["value"] == "refresh-123"
        assert kwargs["httponly"] is True
        assert kwargs["secure"] is False
