from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import app
from middleware.auth_middleware import get_current_user_from_credentials
from routes.profile import get_admin_gallery_service, get_auth_service, get_gallery_service, get_storage_service


class TestProfileRoutes:
    """Test suite for Profile routes"""

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

    def test_get_profile(self, client, mock_user, mock_auth_service):
        """Test getting current user profile"""
        mock_auth_service.get_user_by_id.return_value = mock_user

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        response = client.get("/api/v1/profile/")

        # Cleanup
        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name

    def test_update_profile(self, client, mock_user, mock_auth_service):
        """Test updating user profile"""
        updated_user_data = {
            "id": mock_user.id,
            "email": mock_user.email,
            "name": "Updated Name",
            "bio": "Updated Bio",
            "picture": mock_user.picture,
            "created_at": mock_user.created_at,
        }
        mock_auth_service.update_user_profile.return_value = updated_user_data

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"name": "Updated Name", "bio": "Updated Bio"}
        response = client.put("/api/v1/profile/", json=payload)

        # Cleanup
        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["name"] == "Updated Name"
        assert data["user"]["bio"] == "Updated Bio"

    def test_update_profile_no_data(self, client, mock_user, mock_auth_service):
        """Test updating profile with no data"""
        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {}
        response = client.put("/api/v1/profile/", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 400

    def test_get_user_uploads(self, client, mock_user, mock_gallery_service, mock_cat_photo):
        """Test getting user uploads"""
        mock_gallery_service.get_user_photos.return_value = [mock_cat_photo]

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_admin_gallery_service] = lambda: mock_gallery_service

        response = client.get("/api/v1/profile/uploads")

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert len(data["uploads"]) == 1
        assert data["uploads"][0]["location_name"] == mock_cat_photo["location_name"]

    def test_upload_profile_picture(
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

        async def mock_process_impl(*args, **kwargs):
            return (sample_image_bytes, "image/jpeg", "jpg")

        with patch("routes.profile.process_uploaded_image", side_effect=mock_process_impl) as mock_process:

            files = {"file": ("avatar.jpg", sample_image_bytes, "image/jpeg")}
            response = client.post("/api/v1/profile/picture", files=files)

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["picture"] == "https://example.com/new-avatar.jpg"
        # Note: The endpoint no longer calls update_user_profile - frontend handles that

    def test_change_password(self, client, mock_user, mock_auth_service):
        """Test changing password"""
        # change_password is async, mock it as AsyncMock
        mock_auth_service.change_password = AsyncMock(return_value=True)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"current_password": "old_password", "new_password": "new_password"}
        response = client.put("/api/v1/profile/password", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    def test_change_password_failure(self, client, mock_user, mock_auth_service):
        """Test changing password failure"""
        # change_password is async, mock it as AsyncMock
        mock_auth_service.change_password = AsyncMock(return_value=False)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

        payload = {"current_password": "wrong_password", "new_password": "new_password"}
        response = client.put("/api/v1/profile/password", json=payload)

        app.dependency_overrides = {}

        assert response.status_code == 400
