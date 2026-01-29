"""
Tests for authentication services

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing authentication
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService
from user_models.user import User


class TestAuthService:
    """Test suite for AuthService"""

    @pytest.fixture
    def auth_service(self, mock_supabase):
        """Create AuthService instance with mocked supabase"""
        # Patch dependencies.get_supabase_admin_client to return the mock
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase):
            service = AuthService(mock_supabase)
            service.supabase_admin = mock_supabase
            return service

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

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service):
        """Test changing password successfully"""
        user_id = "user-123"
        current_password = "old_password"
        new_password = "new_password"

        # Hash current password for fixture
        from services.password_service import password_service
        hashed_current = password_service.hash_password(current_password)

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
            auth_service.supabase_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = (
                mock_update_response
            )
            # Mock password validation and token service
            with patch("services.auth_service.password_service") as mock_pw_service:
                mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))
                # Restore hash_password for the service call (though validation is mocked)
                mock_pw_service.hash_password.return_value = "new_hash"
                mock_pw_service.verify_password.return_value = True

                with patch("services.auth_service.get_token_service") as mock_ts:
                    mock_token_service = MagicMock()
                    mock_token_service.blacklist_all_user_tokens = AsyncMock(return_value=None)
                    mock_ts.return_value = mock_token_service
                    
                    with patch("services.auth_service.email_service"):
                        result = await auth_service.change_password(user_id, current_password, new_password)
                        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_incorrect(self, auth_service):
        """Test changing password with incorrect current password"""
        user_id = "user-123"
        real_password = "real_password"

        from services.password_service import password_service
        hashed = password_service.hash_password(real_password)
        
        mock_user = User(
            id=user_id,
            password_hash=hashed,
            email="test@test.com",
            name="Test",
            created_at="2024-01-01T00:00:00Z",
        )

        with patch.object(auth_service, "get_user_by_id", return_value=mock_user):
             with patch("services.auth_service.password_service") as mock_pw_service:
                mock_pw_service.validate_new_password = AsyncMock(return_value=(True, None))
                mock_pw_service.verify_password.return_value = False
                
                # Also mock the Supabase Auth login fallback to fail
                auth_service.supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
                
                with pytest.raises(ValueError, match="Incorrect current password"):
                    await auth_service.change_password(user_id, "wrong_password", "new_password")

    def test_update_user_profile(self, auth_service):
        """Test updating user profile"""
        user_id = "user-123"
        update_data = {"name": "Updated Name"}

        mock_response = MagicMock()
        mock_response.data = [{"id": user_id, "name": "Updated Name"}]
        auth_service.supabase_admin.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

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

        auth_service.supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = auth_service.get_user_by_id(mock_user.id)
        assert result is not None
        assert result.id == mock_user.id

    def test_get_user_by_id_not_found(self, auth_service):
        """Test getting user by ID when user doesn't exist"""
        mock_result = MagicMock()
        mock_result.data = []
        auth_service.supabase_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = auth_service.get_user_by_id("nonexistent")
        assert result is None
