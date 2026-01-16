"""
Tests for authentication services
"""

from unittest.mock import MagicMock, patch

import pytest

from services.auth_service import AuthService
from user_models.user import User


class TestAuthService:
    """Test suite for AuthService"""

    @pytest.fixture
    def auth_service(self, mock_supabase):
        """Create AuthService instance with mocked supabase"""
        # Patch dependencies.get_supabase_admin_client to return the mock
        with patch(
            "dependencies.get_supabase_admin_client", return_value=mock_supabase
        ):
            service = AuthService(mock_supabase)
            service.supabase_admin = mock_supabase
            return service

    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        result = auth_service.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        result = auth_service.verify_password("wrong_password", hashed)
        assert result is False

    def test_create_or_get_user_new(self, auth_service):
        """Test creating a new user via OAuth data"""
        user_data = {
            "id": "new-user-123",
            "email": "new@example.com",
            "name": "New User",
            "picture": "http://example.com/pic.jpg",
            "google_id": "google-123",
        }

        # Mock upsert response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "new-user-123",
                "email": "new@example.com",
                "name": "New User",
                "picture": "http://example.com/pic.jpg",
                "bio": None,
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        # Service uses supabase_admin which is our mock_supabase
        auth_service.supabase_admin.table.return_value.upsert.return_value.execute.return_value = mock_response

        user = auth_service.create_or_get_user(user_data)

        assert user.id == "new-user-123"
        assert user.email == "new@example.com"
        auth_service.supabase_admin.table.assert_called_with("users")

    def test_change_password_success(self, auth_service):
        """Test changing password successfully"""
        user_id = "user-123"
        current_password = "old_password"
        new_password = "new_password"

        # Mock get_user_by_id
        hashed_current = auth_service.hash_password(current_password)

        mock_user = User(
            id=user_id,
            password_hash=hashed_current,
            email="test@test.com",
            name="Test",
            created_at="2024-01-01T00:00:00Z",
        )

        with patch.object(auth_service, "get_user_by_id", return_value=mock_user):
            # Mock update
            mock_update_response = MagicMock()
            auth_service.supabase_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

            result = auth_service.change_password(
                user_id, current_password, new_password
            )
            assert result is True

    def test_change_password_incorrect(self, auth_service):
        """Test changing password with incorrect current password"""
        user_id = "user-123"
        real_password = "real_password"

        hashed = auth_service.hash_password(real_password)
        mock_user = User(
            id=user_id,
            password_hash=hashed,
            email="test@test.com",
            name="Test",
            created_at="2024-01-01T00:00:00Z",
        )

        with patch.object(auth_service, "get_user_by_id", return_value=mock_user):
            with pytest.raises(ValueError, match="Incorrect current password"):
                auth_service.change_password(user_id, "wrong_password", "new_password")

    def test_update_user_profile(self, auth_service):
        """Test updating user profile"""
        user_id = "user-123"
        update_data = {"name": "Updated Name"}

        mock_response = MagicMock()
        mock_response.data = [{"id": user_id, "name": "Updated Name"}]
        auth_service.supabase_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = auth_service.update_user_profile(user_id, update_data)

        assert result["name"] == "Updated Name"

    def test_get_user_by_id_found(self, auth_service, mock_user):
        """Test getting user by ID when user exists"""
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": mock_user.id,
                "email": mock_user.email,
                "name": mock_user.name,
                "created_at": "2024-01-01",
            }
        ]

        auth_service.supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = auth_service.get_user_by_id(mock_user.id)
        assert result is not None
        assert result.id == mock_user.id

    def test_get_user_by_id_not_found(self, auth_service):
        """Test getting user by ID when user doesn't exist"""
        mock_result = MagicMock()
        mock_result.data = []
        auth_service.supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        result = auth_service.get_user_by_id("nonexistent")
        assert result is None
