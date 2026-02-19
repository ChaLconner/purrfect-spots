from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from middleware.auth_middleware import get_current_user_from_credentials
from routes.profile import get_admin_gallery_service, get_auth_service, get_storage_service


@pytest.fixture
async def client():
    """Create test client using AsyncClient"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestProfileRoute:
    @pytest.fixture
    def mock_auth_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_gallery_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_storage_service(self):
        service = MagicMock()
        service.upload_file = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_get_profile(self, client, mock_user, mock_auth_service):
        """Test getting current user profile"""
        mock_auth_service.get_user_by_id.return_value = mock_user

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        response = await client.get("/api/v1/profile/")

        # Cleanup
        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name

    @pytest.mark.asyncio
    async def test_update_profile(self, client, mock_user, mock_auth_service):
        """Test updating user profile"""
        updated_user_data = {
            "id": mock_user.id,
            "email": mock_user.email,
            "name": "Updated Name",
            "bio": "Updated Bio",
            "picture": mock_user.picture,
            "created_at": mock_user.created_at,
        }
        # Update is async now
        mock_auth_service.update_user_profile = AsyncMock(return_value=updated_user_data)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"name": "Updated Name", "bio": "Updated Bio"}
        response = await client.put("/api/v1/profile/", json=payload)

        # Cleanup
        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["name"] == "Updated Name"
        assert data["user"]["bio"] == "Updated Bio"

    @pytest.mark.asyncio
    async def test_update_profile_no_data(self, client, mock_user, mock_auth_service):
        """Test updating profile with no data"""
        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {}
        response = await client.put("/api/v1/profile/", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_uploads(self, client, mock_user, mock_gallery_service, mock_cat_photo):
        """Test getting user uploads"""
        mock_gallery_service.get_user_photos = AsyncMock(return_value=[mock_cat_photo])

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_admin_gallery_service] = lambda: mock_gallery_service

        response = await client.get("/api/v1/profile/uploads")

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert len(data["uploads"]) == 1
        assert data["uploads"][0]["location_name"] == mock_cat_photo["location_name"]

    @pytest.mark.asyncio
    async def test_upload_profile_picture(
        self,
        client,
        mock_user,
        mock_auth_service,
        mock_storage_service,
        sample_image_bytes,
    ):
        """Test uploading profile picture"""
        mock_storage_service.upload_file.return_value = "https://example.com/new-avatar.jpg"

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        app.dependency_overrides[get_storage_service] = lambda: mock_storage_service

        mock_process = AsyncMock(return_value=(sample_image_bytes, "image/jpeg", "jpg"))
        with patch("routes.profile.process_uploaded_image", new=mock_process):
            files = {"file": ("avatar.jpg", sample_image_bytes, "image/jpeg")}
            response = await client.post("/api/v1/profile/picture", files=files)

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["picture"] == "https://example.com/new-avatar.jpg"

    @pytest.mark.asyncio
    async def test_change_password(self, client, mock_user, mock_auth_service):
        """Test changing password"""
        # change_password is async, mock it as AsyncMock
        mock_auth_service.change_password = AsyncMock(return_value=True)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"current_password": "old_password", "new_password": "new_password"}
        response = await client.put("/api/v1/profile/password", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    @pytest.mark.asyncio
    async def test_change_password_failure(self, client, mock_user, mock_auth_service):
        """Test changing password failure"""
        # change_password is async, mock it as AsyncMock
        mock_auth_service.change_password = AsyncMock(return_value=False)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"current_password": "wrong_password", "new_password": "new_password"}
        response = await client.put("/api/v1/profile/password", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 400
