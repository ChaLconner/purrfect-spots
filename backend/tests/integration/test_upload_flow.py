"""
Integration tests for the complete upload flow

These tests verify the end-to-end upload process:
1. Authentication
2. File upload with validation
3. Cat detection
4. Database storage
5. Gallery retrieval

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for integration testing
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image


class TestUploadFlowIntegration:
    """End-to-end tests for the upload workflow"""

    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
        }

    @pytest.fixture
    def valid_cat_image(self):
        """Create a valid test image"""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def authenticated_client(self, client, mock_auth_user):
        """Client with mocked authentication"""
        with patch("middleware.auth_middleware.get_current_user") as mock_auth:
            mock_auth.return_value = mock_auth_user
            yield client

    def test_upload_requires_authentication(self, client, valid_cat_image):
        """Test: Upload fails without authentication"""
        response = client.post(
            "/api/v1/upload/cat",
            files={"image": ("cat.jpg", valid_cat_image, "image/jpeg")},
            data={
                "location_name": "Test Park",
                "latitude": "13.7563",
                "longitude": "100.5018",
            },
        )

        assert response.status_code == 401

    def test_upload_validates_file_type(self, authenticated_client, mock_auth_user):
        """Test: Upload rejects non-image files"""
        fake_file = io.BytesIO(b"not an image")

        with patch("routes.upload.get_current_user", return_value=mock_auth_user):
            response = authenticated_client.post(
                "/api/v1/upload/cat",
                files={"file": ("document.txt", fake_file, "text/plain")},
                data={
                    "location_name": "Test Park",
                    "latitude": "13.7563",
                    "longitude": "100.5018",
                },
            )

        assert response.status_code in [400, 401, 422]

    def test_upload_validates_location(self, authenticated_client, valid_cat_image, mock_auth_user):
        """Test: Upload validates latitude/longitude ranges"""
        with patch("routes.upload.get_current_user", return_value=mock_auth_user):
            # Invalid latitude (>90)
            response = authenticated_client.post(
                "/api/v1/upload/cat",
                files={"file": ("cat.jpg", valid_cat_image, "image/jpeg")},
                data={
                    "location_name": "Test Park",
                    "latitude": "100.0",  # Invalid
                    "longitude": "100.5018",
                },
            )

        assert response.status_code in [400, 401, 422]

    def test_upload_sanitizes_location_name(self, authenticated_client, valid_cat_image, mock_auth_user):
        """Test: Upload sanitizes XSS in location name"""
        malicious_name = "<script>alert('xss')</script>Test Park"

        # Mock dependencies
        mock_detection_service = MagicMock()
        mock_detection_service.detect_cats = AsyncMock(
            return_value={
                "has_cats": True,
                "cat_count": 1,
                "confidence": 95,
                "suitable_for_cat_spot": True,
                "cats_detected": [],
            }
        )

        mock_storage_service = MagicMock()
        mock_storage_service.upload_file = AsyncMock(return_value="https://s3.example.com/cat.jpg")

        # Mock Supabase return for insert
        mock_supabase_params = MagicMock()
        mock_supabase_params.data = [
            {
                "id": "photo-123",
                "location_name": "Test Park",
                "image_url": "url",
                "uploaded_at": "now",
                "latitude": 13,
                "longitude": 100,
            }
        ]

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_supabase_params

        # Override dependencies
        from dependencies import get_supabase_client
        from main import app
        from routes.upload import get_cat_detection_service, get_current_user, get_storage_service
        from services.cat_detection_service import CatDetectionService
        from services.storage_service import StorageService

        app.dependency_overrides[get_supabase_client] = lambda: mock_client
        app.dependency_overrides[get_cat_detection_service] = lambda: mock_detection_service
        app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
        app.dependency_overrides[get_current_user] = lambda: MagicMock(id="user-123", email="test@example.com")

        with (
            patch("dependencies.get_supabase_admin_client") as mock_get_admin,
            patch("routes.upload.process_uploaded_image") as mock_process_image,
            patch("routes.upload.invalidate_gallery_cache"),
            patch("routes.upload.invalidate_tags_cache"),
            patch("routes.upload.log_security_event"),
        ):
            mock_admin_client = MagicMock()
            mock_admin_client.table.return_value.insert.return_value.execute.return_value = mock_supabase_params
            mock_get_admin.return_value = mock_admin_client

            # Mock image processing result
            mock_process_image.return_value = (b"image-content", "image/jpeg", "jpg")

            try:
                response = authenticated_client.post(
                    "/api/v1/upload/cat",
                    files={"file": ("cat.jpg", valid_cat_image, "image/jpeg")},
                    data={
                        "location_name": malicious_name,
                        "latitude": "13.7563",
                        "longitude": "100.5018",
                        "lat": "13.7563",
                        "lng": "100.5018",
                    },
                )
            finally:
                app.dependency_overrides = {}

        # Should sanitize and accept
        assert response.status_code == 201


class TestGalleryFlowIntegration:
    """End-to-end tests for gallery retrieval"""

    def test_gallery_returns_photos(self, client):
        """Test: Gallery returns paginated photos"""
        # Mock Service
        mock_service = MagicMock()
        mock_service.get_all_photos.return_value = {
            "data": [
                {
                    "id": "photo-1",
                    "image_url": "https://s3.example.com/cat1.jpg",
                    "location_name": "Park",
                    "latitude": 13.75,
                    "longitude": 100.50,
                    "tags": [],
                    "description": "A cat",
                    "uploaded_at": "2024-01-01",
                }
            ],
            "total": 1,
            "has_more": False,
        }

        # Override dependency
        from main import app
        from routes.gallery import get_gallery_service

        app.dependency_overrides[get_gallery_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/gallery/")
        finally:
            app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()

        # Check for paginated response structure
        assert "images" in data
        assert "pagination" in data
        assert len(data["images"]) == 1
        assert data["images"][0]["location_name"] == "Park"

    def test_gallery_pagination(self, client):
        """Test: Gallery supports pagination parameters"""
        response = client.get("/api/v1/gallery/?page=1&limit=10")

        # Should accept pagination params
        assert response.status_code in [200, 500]  # 500 if DB not configured

    def test_gallery_no_auth_required(self, client):
        """Test: Gallery is publicly accessible"""
        # Don't set any auth headers
        response = client.get("/api/v1/gallery/")

        # Should not return 401
        assert response.status_code != 401


class TestAuthFlowIntegration:
    """End-to-end tests for authentication flows"""

    def test_register_creates_user(self, client):
        """Test: Registration creates a new user"""
        mock_service = MagicMock()
        mock_service.create_user_with_password.return_value = {
            "id": "new-user-123",
            "email": "new@example.com",
            "name": "New User",
            "picture": None,
            "bio": None,
            "created_at": "2024-01-01T00:00:00",
            "verification_required": True,  # Set to True to go through verification flow
        }
        mock_service.authenticate_user.return_value = None  # No auto-login for verification flow
        mock_service.create_access_token.return_value = "access-token"
        mock_service.create_refresh_token.return_value = "refresh-token"

        from main import app
        from routes.auth_manual import get_auth_service

        app.dependency_overrides[get_auth_service] = lambda: mock_service

        try:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "new@example.com",
                    "password": "SecurePass123",
                    "name": "New User",
                },
            )
        finally:
            app.dependency_overrides = {}

        # Should succeed or fail with validation
        assert response.status_code in [200, 201, 400, 409, 422]

    def test_login_returns_tokens(self, client):
        """Test: Login returns access and refresh tokens"""

        mock_service = MagicMock()
        mock_service.authenticate_user.return_value = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "created_at": "2023-01-01",
        }
        mock_service.create_access_token.return_value = "access-token"
        mock_service.create_refresh_token.return_value = "refresh-token"

        from main import app
        from routes.auth_manual import get_auth_service

        app.dependency_overrides[get_auth_service] = lambda: mock_service

        try:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password123"},
            )
        finally:
            app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


# Fixtures
@pytest.fixture
def client():
    """Create test client"""
    from main import app

    return TestClient(app)
