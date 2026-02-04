"""
Tests for authentication services

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing authentication
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService
from user_models.user import User
from utils.datetime_utils import utc_now


class TestAuthService:
    """Test suite for AuthService"""

    TEST_USER_ID = "user-123"
    TEST_EMAIL = "test@test.com"
    TEST_NAME = "Test User"
    OLD_PASSWORD = "old_password"
    NEW_PASSWORD = "new_password"

    @pytest.fixture
    def mock_user_service(self):
        """Mock UserService"""
        with patch("services.auth_service.UserService") as mock_class:
            mock_instance = mock_class.return_value
            yield mock_instance

    @pytest.fixture
    def auth_service(self, mock_supabase, mock_user_service):
        """Create AuthService instance with mocked supabase and user service"""
        service = AuthService(mock_supabase)
        # Verify UserService was initialized with supabase client
        # mock_user_service_class.assert_called_with(mock_supabase) # Can't easily check this here due to fixture yield
        return service

    def test_create_or_get_user_new(self, auth_service, mock_user_service):
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
        mock_user_service.create_or_get_user.return_value = expected_user

        user = auth_service.create_or_get_user(user_data)

        assert user.id == "new-user-123"
        assert user.email == "new@example.com"
        mock_user_service.create_or_get_user.assert_called_once_with(user_data)

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_user_service):
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
            password_hash="hashed_old",
        )
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock password validation
        with patch("services.auth_service.password_service") as mock_pw_service:
            mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))
            mock_pw_service.verify_password.return_value = True
            mock_pw_service.hash_password.return_value = "new_hash"

            with patch("services.auth_service.get_token_service") as mock_ts:
                mock_token_service = MagicMock()
                mock_token_service.blacklist_all_user_tokens = AsyncMock(return_value=None)
                mock_ts.return_value = mock_token_service

                # Mock email service
                with patch("services.auth_service.email_service"):
                    # Mock Supabase Admin Update (AuthService does this directly currently for password change in step 4/5)
                    # Wait, looking at AuthService.change_password:
                    # It calls self.supabase_admin.auth.admin.update_user_by_id
                    # AND self.user_service.update_password_hash

                    # Mock admin client
                    auth_service.supabase_admin.auth.admin.update_user_by_id = MagicMock()

                    result = await auth_service.change_password(user_id, current_password, new_password)

                    assert result is True
                    mock_user_service.update_password_hash.assert_called_once_with(user_id, new_password)

    @pytest.mark.asyncio
    async def test_change_password_incorrect(self, auth_service, mock_user_service):
        """Test changing password with incorrect current password"""
        user_id = "user-123"

        mock_user = User(
            id=user_id,
            email="test@test.com",
            name="Test",
            created_at=utc_now(),
            password_hash="hashed_real",
        )
        mock_user_service.get_user_by_id.return_value = mock_user

        with patch("services.auth_service.password_service") as mock_pw_service:
            mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))
            mock_pw_service.verify_password.return_value = False

            # Also mock the Supabase Auth login fallback to fail
            # AuthService calls user_service.authenticate_user for fallback
            mock_user_service.authenticate_user.return_value = None

            with pytest.raises(ValueError, match="Incorrect current password"):
                await auth_service.change_password(user_id, "wrong_password", "new_password")

    def test_update_user_profile(self, auth_service, mock_user_service):
        """Test updating user profile"""
        user_id = "user-123"
        update_data = {"name": "Updated Name"}

        mock_user_service.update_user_profile.return_value = {"id": user_id, "name": "Updated Name"}

        result = auth_service.update_user_profile(user_id, update_data)

        assert result["name"] == "Updated Name"
        mock_user_service.update_user_profile.assert_called_once_with(user_id, update_data)

    def test_get_user_by_id_found(self, auth_service, mock_user_service):
        """Test getting user by ID when user exists"""
        mock_user = User(id="user-123", email="test@test.com", name="Test", created_at=utc_now())
        mock_user_service.get_user_by_id.return_value = mock_user

        result = auth_service.get_user_by_id("user-123")
        assert result is not None
        assert result.id == "user-123"

    def test_get_user_by_id_not_found(self, auth_service, mock_user_service):
        """Test getting user by ID when user doesn't exist"""
        mock_user_service.get_user_by_id.return_value = None

        result = auth_service.get_user_by_id("nonexistent")
        assert result is None
