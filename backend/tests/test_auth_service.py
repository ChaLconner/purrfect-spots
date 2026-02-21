"""
Tests for authentication services

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService
from user_models.user import User
from utils.datetime_utils import utc_now


@pytest.mark.asyncio
class TestAuthService:
    """Test suite for AuthService"""

    TEST_USER_ID = "user-123"
    TEST_EMAIL = "test@test.com"
    TEST_NAME = "Test User"
    OLD_PASSWORD = "old_password"
    NEW_PASSWORD = "new_password"

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock = MagicMock()
        mock.auth = MagicMock()
        return mock

    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase Admin client"""
        mock = MagicMock()
        mock.auth = MagicMock()
        mock.auth.admin = MagicMock()
        # Ensure async methods are awaited if called directly, though mostly accessed via properties
        return mock

    @pytest.fixture
    def mock_user_service_instance(self):
        """Mock UserService instance with AsyncMock methods"""
        mock = MagicMock()
        mock.create_or_get_user = AsyncMock()
        mock.get_user_by_id = AsyncMock()
        mock.update_user_profile = AsyncMock()
        mock.authenticate_user = AsyncMock()
        mock.create_unverified_user = AsyncMock()
        mock.get_user_by_email = AsyncMock()
        return mock

    @pytest.fixture
    def auth_service(self, mock_supabase, mock_supabase_admin, mock_user_service_instance):
        """Create AuthService instance with mocked dependencies"""
        # Patch the class so when AuthService init calls UserService(), it returns our mock
        with patch("services.auth_service.UserService", return_value=mock_user_service_instance):
            service = AuthService(mock_supabase, mock_supabase_admin)
            # Ensure the service uses our mock instance (it should by virtue of patch, but explicit check helper)
            yield service

    async def test_create_or_get_user_new(self, auth_service, mock_user_service_instance):
        """Test creating a new user via OAuth data"""
        user_data = {
            "id": "new-user-123",
            "email": "new@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
            "google_id": "google-123",
        }

        # Mock user service return
        expected_user = User(
            id="new-user-123",
            email="new@example.com",
            name="New User",
            picture="https://example.com/pic.jpg",
            created_at=utc_now(),
        )
        mock_user_service_instance.create_or_get_user.return_value = expected_user

        user = await auth_service.create_or_get_user(user_data)

        assert user.id == "new-user-123"
        assert user.email == "new@example.com"
        mock_user_service_instance.create_or_get_user.assert_called_once_with(user_data)

    async def test_change_password_success(self, auth_service, mock_user_service_instance, mock_supabase_admin):
        """Test changing password successfully"""
        user_id = self.TEST_USER_ID
        current_password = self.OLD_PASSWORD
        new_password = self.NEW_PASSWORD

        # Mock user retrieval
        mock_user = User(
            id=user_id,
            email="test@test.com",
            name="Test",
            created_at=utc_now(),
        )
        mock_user_service_instance.get_user_by_id.return_value = mock_user

        # Mock password validation
        with patch("services.auth_service.password_service") as mock_pw_service:
            mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))
            # AuthService now calls authenticate_user for verification instead of password_service.verify_password manually
            mock_user_service_instance.authenticate_user.return_value = {"id": user_id}

            with patch("services.auth_service.get_token_service") as mock_ts_getter:
                mock_token_service = MagicMock()
                mock_token_service.blacklist_all_user_tokens = AsyncMock(return_value=None)
                mock_ts_getter.return_value = mock_token_service

                # Mock email service
                with patch("services.auth_service.email_service"):
                    # Mock admin client update
                    mock_supabase_admin.auth.admin.update_user_by_id = AsyncMock()

                    result = await auth_service.change_password(user_id, current_password, new_password)

                    assert result is True
                    mock_supabase_admin.auth.admin.update_user_by_id.assert_called_once_with(
                        user_id, {"password": new_password}
                    )

    async def test_change_password_incorrect(self, auth_service, mock_user_service_instance):
        """Test changing password with incorrect current password"""
        user_id = "user-123"

        mock_user = User(
            id=user_id,
            email="test@test.com",
            name="Test",
            created_at=utc_now(),
        )
        mock_user_service_instance.get_user_by_id.return_value = mock_user

        with patch("services.auth_service.password_service") as mock_pw_service:
            mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))

            # Mock authentication failure
            mock_user_service_instance.authenticate_user.return_value = None

            with pytest.raises(ValueError, match="Incorrect current password"):
                await auth_service.change_password(user_id, "wrong_password", "new_password")

    async def test_update_user_profile(self, auth_service, mock_user_service_instance):
        """Test updating user profile"""
        user_id = "user-123"
        update_data = {"name": "Updated Name"}

        mock_user_service_instance.update_user_profile.return_value = {"id": user_id, "name": "Updated Name"}

        result = await auth_service.update_user_profile(user_id, update_data)

        assert result["name"] == "Updated Name"
        mock_user_service_instance.update_user_profile.assert_called_once()
        # Check args
        args = mock_user_service_instance.update_user_profile.call_args
        assert args[0][0] == user_id
        assert args[0][1] == update_data

    async def test_get_user_by_id_found(self, auth_service, mock_user_service_instance):
        """Test getting user by ID when user exists"""
        mock_user = User(id="user-123", email="test@test.com", name="Test", created_at=utc_now())
        mock_user_service_instance.get_user_by_id.return_value = mock_user

        result = await auth_service.get_user_by_id("user-123")
        assert result is not None
        assert result.id == "user-123"

    async def test_get_user_by_id_not_found(self, auth_service, mock_user_service_instance):
        """Test getting user by ID when user doesn't exist"""
        mock_user_service_instance.get_user_by_id.return_value = None

        result = await auth_service.get_user_by_id("nonexistent")
        assert result is None
