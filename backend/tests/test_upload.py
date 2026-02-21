import io
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client():
    """Create test client using AsyncClient"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestUploadRoute:
    """Test upload endpoint functionality"""

    @pytest.fixture
    def mock_current_user(self, mock_user):
        """Override auth dependency"""
        return mock_user

    @pytest.fixture
    def mock_storage_service(self):
        """Create mock storage service"""
        service = MagicMock()
        service.upload_file = AsyncMock(return_value="https://s3.example.com/cat.jpg")
        return service

    @pytest.fixture
    def mock_cat_detection_service(self):
        """Create mock cat detection service"""
        service = MagicMock()
        service.detect_cats = AsyncMock(
            return_value={
                "has_cats": True,
                "cat_count": 1,
                "confidence": 0.95,
                "suitable_for_cat_spot": True,
                "cats_detected": [{"name": "cat", "score": 0.95}],
            }
        )
        return service

    async def test_upload_test_endpoint(self, client):
        """Test that upload test endpoint works"""
        response = await client.get("/api/v1/upload/test")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Upload endpoint is working!"

    async def test_upload_requires_authentication(self, client, sample_image_bytes):
        """Test that upload requires authentication"""
        files = {"file": ("cat.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
        data = {"lat": "13.7563", "lng": "100.5018", "location_name": "Test Cat Spot"}

        response = await client.post("/api/v1/upload/cat", files=files, data=data)

        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]

    @pytest.fixture
    def mock_limiter(self):
        """Mock the rate limiter"""
        with patch("routes.upload.limiter") as mock:
            mock.limit = MagicMock(side_effect=lambda limit_value: lambda func: func)
            yield mock

    async def test_upload_with_mock_auth(
        self,
        client,
        sample_image_bytes,
        mock_user,
        mock_supabase,
        mock_storage_service,
        mock_cat_detection_service,
        mock_limiter,
    ):
        """Test upload with mocked authentication and services"""
        from dependencies import get_async_supabase_client
        from main import app
        from middleware.auth_middleware import get_current_user
        from routes.upload import get_cat_detection_service, get_quota_service, get_storage_service

        # Mock quota service
        mock_quota_service = MagicMock()
        mock_quota_service.check_and_increment = AsyncMock(return_value=True)

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
        app.dependency_overrides[get_cat_detection_service] = lambda: mock_cat_detection_service
        app.dependency_overrides[get_async_supabase_client] = lambda: mock_supabase
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        # Mock supabase admin insert
        mock_admin = MagicMock()
        mock_admin.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(
                data=[
                    {
                        "id": "new-photo-123",
                        "user_id": mock_user.id,
                        "location_name": "Test Cat Spot",
                        "latitude": 13.7563,
                        "longitude": 100.5018,
                        "image_url": "https://s3.example.com/cat.jpg",
                        "uploaded_at": datetime.now().isoformat(),
                    }
                ]
            )
        )

        with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
            mock_get_admin.return_value = mock_admin

            with patch("routes.upload.process_uploaded_image", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = (sample_image_bytes, "image/jpeg", "jpg")

                files = {"file": ("cat.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
                data = {
                    "lat": "13.7563",
                    "lng": "100.5018",
                    "location_name": "Test Cat Spot",
                    "description": "A friendly cat",
                    "tags": json.dumps(["orange", "friendly"]),
                }

                response = await client.post("/api/v1/upload/cat", files=files, data=data)

        # Clean up overrides
        app.dependency_overrides = {}

        assert response.status_code == 201
        result = response.json()
        assert result["success"] is True
        assert "photo" in result


class TestParsingFunctions:
    """Test helper functions in upload route"""

    def test_parse_tags_valid_json(self):
        """Test parsing valid JSON tags"""
        from routes.upload import parse_tags

        tags_json = json.dumps(["orange", "cute", "sleeping"])
        result = parse_tags(tags_json)

        assert result == ["orange", "cute", "sleeping"]

    def test_parse_tags_with_hashtags(self):
        """Test that hashtags are stripped from tags"""
        from routes.upload import parse_tags

        tags_json = json.dumps(["#orange", "#cute"])
        result = parse_tags(tags_json)

        assert result == ["orange", "cute"]

    def test_parse_tags_empty_string(self):
        """Test parsing empty string"""
        from routes.upload import parse_tags

        result = parse_tags("")

        assert result == []

    def test_parse_tags_none(self):
        """Test parsing None"""
        from routes.upload import parse_tags

        result = parse_tags(None)

        assert result == []

    def test_parse_tags_invalid_json(self):
        """Test parsing invalid JSON"""
        from routes.upload import parse_tags

        result = parse_tags("not valid json")

        assert result == []

    def test_parse_tags_normalizes_case(self):
        """Test that tags are lowercase"""
        from routes.upload import parse_tags

        tags_json = json.dumps(["ORANGE", "CuTe", "Sleeping"])
        result = parse_tags(tags_json)

        assert result == ["orange", "cute", "sleeping"]

    def test_parse_tags_max_limit(self):
        """Test that max 20 tags are returned"""
        from routes.upload import parse_tags

        many_tags = [f"tag{i}" for i in range(30)]
        tags_json = json.dumps(many_tags)
        result = parse_tags(tags_json)

        assert len(result) == 20

    def test_parse_tags_trims_whitespace(self):
        """Test that whitespace is trimmed from tags"""
        from routes.upload import parse_tags

        tags_json = json.dumps(["  orange  ", "  cute  "])
        result = parse_tags(tags_json)

        assert result == ["orange", "cute"]

    def test_parse_tags_filters_empty(self):
        """Test that empty tags are filtered"""
        from routes.upload import parse_tags

        tags_json = json.dumps(["orange", "", "  ", "cute"])
        result = parse_tags(tags_json)

        assert result == ["orange", "cute"]

    def test_format_tags_for_description_with_tags(self):
        """Test formatting tags into description"""
        from routes.upload import format_tags_for_description

        result = format_tags_for_description(["orange", "cute"], "A nice cat")

        assert "A nice cat" in result
        assert "#orange" in result
        assert "#cute" in result

    def test_format_tags_for_description_empty_tags(self):
        """Test formatting with no tags"""
        from routes.upload import format_tags_for_description

        result = format_tags_for_description([], "A nice cat")

        assert result == "A nice cat"

    def test_format_tags_for_description_empty_description(self):
        """Test formatting with no description"""
        from routes.upload import format_tags_for_description

        result = format_tags_for_description(["orange"], "")

        assert result == "#orange"


class TestUploadValidation:
    """Test validation in upload process"""

    @pytest.fixture
    def mock_limiter(self):
        """Mock the rate limiter"""
        with patch("routes.upload.limiter") as mock:
            mock.limit = MagicMock(side_effect=lambda limit_value: lambda func: func)
            yield mock

    async def test_upload_rejects_no_cats(self, client, sample_image_bytes, mock_user, mock_supabase, mock_limiter):
        """Test that upload rejects images without cats"""
        from dependencies import get_async_supabase_client
        from main import app
        from middleware.auth_middleware import get_current_user
        from routes.upload import get_cat_detection_service, get_quota_service, get_storage_service

        # Create cat detection that returns no cats
        mock_detection = MagicMock()
        mock_detection.detect_cats = AsyncMock(
            return_value={
                "has_cats": False,
                "cat_count": 0,
                "confidence": 0,
                "suitable_for_cat_spot": False,
                "cats_detected": [],
            }
        )

        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock(return_value="https://s3.example.com/cat.jpg")
        mock_storage.delete_file = AsyncMock()
        # Mock quota service
        mock_quota_service = MagicMock()
        mock_quota_service.check_and_increment = AsyncMock(return_value=True)

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_cat_detection_service] = lambda: mock_detection
        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_async_supabase_client] = lambda: mock_supabase
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        with patch("routes.upload.process_uploaded_image", new_callable=AsyncMock) as mock_process:
            mock_process.return_value = (sample_image_bytes, "image/jpeg", "jpg")

            files = {"file": ("dog.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
            data = {
                "lat": "13.7563",
                "lng": "100.5018",
                "location_name": "Test Location",
            }

            response = await client.post("/api/v1/upload/cat", files=files, data=data)

        # Clean up overrides
        app.dependency_overrides = {}

        assert response.status_code == 400
        assert "No cats detected" in response.json()["detail"]

    async def test_upload_validates_coordinates(
        self, client, sample_image_bytes, mock_user, mock_supabase, mock_limiter
    ):
        """Test that invalid coordinates are rejected"""
        from dependencies import get_async_supabase_client
        from main import app
        from middleware.auth_middleware import get_current_user
        from routes.upload import get_quota_service

        # Mock quota service
        mock_quota_service = MagicMock()
        mock_quota_service.check_and_increment = AsyncMock(return_value=True)

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_async_supabase_client] = lambda: mock_supabase
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        with patch("routes.upload.process_uploaded_image", new_callable=AsyncMock) as mock_process:
            mock_process.return_value = (sample_image_bytes, "image/jpeg", "jpg")

            files = {"file": ("cat.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
            data = {
                "lat": "invalid",  # Invalid
                "lng": "100.5018",
                "location_name": "Test Location",
                "cat_detection_data": json.dumps({"has_cats": True, "cat_count": 1}),
            }

            with patch("routes.upload.validate_coordinates") as mock_validate:
                from fastapi import HTTPException

                mock_validate.side_effect = HTTPException(status_code=400, detail="Invalid coordinate format")

                response = await client.post("/api/v1/upload/cat", files=files, data=data)

        # Clean up overrides
        app.dependency_overrides = {}

        assert response.status_code == 400


class TestUploadWithPredetectedCats:
    """Test upload with pre-detected cat data"""

    @pytest.fixture
    def mock_limiter(self):
        """Mock the rate limiter"""
        with patch("routes.upload.limiter") as mock:
            mock.limit = MagicMock(side_effect=lambda limit_value: lambda func: func)
            yield mock

    async def test_upload_ignores_client_detection_data(
        self,
        client,
        sample_image_bytes,
        mock_user,
        mock_supabase,
        mock_limiter,
    ):
        """
        Test that upload IGNORES client-provided cat detection data and uses server result.
        Security Fix Verification.
        """
        from dependencies import get_async_supabase_client
        from main import app
        from middleware.auth_middleware import get_current_user
        from routes.upload import get_cat_detection_service, get_quota_service, get_storage_service

        mock_storage = MagicMock()
        mock_storage.upload_file = AsyncMock(return_value="https://s3.example.com/cat.jpg")

        # Mock quota service
        mock_quota_service = MagicMock()
        mock_quota_service.check_and_increment = AsyncMock(return_value=True)

        # Mock DETECTION service to return a specific "Server Truth"
        mock_cat_detection_service = MagicMock()
        # Server says: 1 cat, confidence 0.95
        mock_cat_detection_service.detect_cats = AsyncMock(
            return_value={
                "has_cats": True,
                "cat_count": 1,
                "confidence": 0.95,
                "suitable_for_cat_spot": False,
                "cats_detected": [{"name": "cat", "score": 0.95}],
            }
        )

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_async_supabase_client] = lambda: mock_supabase
        app.dependency_overrides[get_cat_detection_service] = lambda: mock_cat_detection_service
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        mock_admin = MagicMock()
        mock_admin.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(
                data=[
                    {
                        "id": "new-photo-123",
                        "user_id": mock_user.id,
                        "location_name": "Test Cat Spot",
                        "latitude": 13.7563,
                        "longitude": 100.5018,
                        "image_url": "https://s3.example.com/cat.jpg",
                        "uploaded_at": datetime.now().isoformat(),
                    }
                ]
            )
        )

        with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
            mock_get_admin.return_value = mock_admin

            with patch("routes.upload.process_uploaded_image", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = (sample_image_bytes, "image/jpeg", "jpg")

                # Client sends "Fake" data: 2 cats, 0.98 confidence
                cat_detection_data = json.dumps(
                    {
                        "has_cats": True,
                        "cat_count": 99,  # Exaggerated to prove it's ignored
                        "confidence": 0.98,
                        "suitable_for_cat_spot": True,
                    }
                )

                files = {"file": ("cat.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")}
                data = {
                    "lat": "13.7563",
                    "lng": "100.5018",
                    "location_name": "Test Cat Spot",
                    "cat_detection_data": cat_detection_data,
                }

                response = await client.post("/api/v1/upload/cat", files=files, data=data)

        # Clean up overrides
        app.dependency_overrides = {}

        assert response.status_code == 201
        result = response.json()

        # ASSERTION: Result should match SERVER mock (cat_count=1), NOT client data (cat_count=99)
        assert result["cat_detection"]["cat_count"] == 1
        assert result["cat_detection"]["confidence"] == pytest.approx(0.95)
