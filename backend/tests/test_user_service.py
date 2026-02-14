"""
Tests for user service
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from supabase import Client

from exceptions import PurrfectSpotsException
from services.user_service import UserService
from user_models.user import User


class TestUserService:
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock = MagicMock()
        mock.auth = MagicMock()
        mock.table.return_value = mock
        return mock

    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase admin client"""
        mock = MagicMock()
        mock.auth = MagicMock()
        mock.auth.admin = MagicMock()
        mock.table = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.eq.return_value = mock
        mock.single.return_value = mock
        mock.update.return_value = mock
        mock.upsert.return_value = mock
        mock.is_.return_value = mock
        mock.order.return_value = mock
        mock.limit.return_value = mock
        mock.execute.return_value = MagicMock(data=[], count=0)
        return mock

    @pytest.fixture
    def user_service(self, mock_supabase, mock_supabase_admin):
        """Create UserService instance with mocked dependencies"""
        with patch("services.user_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = UserService(mock_supabase)
            return service

    def test_get_user_by_id_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by ID"""
        user_id = "user-123"
        mock_supabase_admin.execute.return_value = MagicMock(data=[{
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User"
        }])
        
        user = user_service.get_user_by_id(user_id)
        
        assert user is not None
        assert user.id == user_id
        mock_supabase_admin.table.assert_called_with("users")

    def test_get_user_by_email_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by email"""
        email = "test@example.com"
        mock_supabase_admin.execute.return_value = MagicMock(data={"email": email, "id": "u1"})
        
        user_data = user_service.get_user_by_email(email)
        
        assert user_data is not None
        assert user_data["email"] == email

    @patch("services.user_service.email_service")
    def test_create_user_with_password_success(self, mock_email_service, user_service, mock_supabase_admin):
        """Test creating user with password and generating link"""
        email = "new@example.com"
        password = "secret-password"
        name = "New User"
        
        # Mock res from generate_link
        mock_res = MagicMock()
        mock_res.user = MagicMock(id="new-u1", email=email, created_at="2024-01-01")
        mock_res.properties = MagicMock(action_link="https://confirm.com/link")
        mock_supabase_admin.auth.admin.generate_link.return_value = mock_res
        
        mock_email_service.send_confirmation_email.return_value = True
        
        result = user_service.create_user_with_password(email, password, name)
        
        assert result["id"] == "new-u1"
        assert result["email"] == email
        assert result["verification_required"] is True
        mock_email_service.send_confirmation_email.assert_called_once_with(email, "https://confirm.com/link")

    def test_create_unverified_user_success(self, user_service, mock_supabase_admin):
        """Test creating unverified user via admin API"""
        email = "unverified@example.com"
        
        mock_res = MagicMock()
        mock_res.user = MagicMock(id="un-u1", email=email, created_at="2024-01-01")
        mock_supabase_admin.auth.admin.create_user.return_value = mock_res
        
        result = user_service.create_unverified_user(email, "pass", "Unverified")
        
        assert result["id"] == "un-u1"
        assert result["verification_required"] is True

    def test_create_or_get_user_oauth(self, user_service, mock_supabase_admin):
        """Test creating or getting user for OAuth flow"""
        user_data = {
            "id": "google-123",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "picture": "pic.jpg"
        }
        
        mock_supabase_admin.upsert.return_value = mock_supabase_admin
        mock_supabase_admin.execute.return_value = MagicMock(data=[user_data])
        
        user = user_service.create_or_get_user(user_data)
        
        assert user.id == "google-123"
        assert user.email == "oauth@example.com"
        mock_supabase_admin.table.assert_called_with("users")

    def test_authenticate_user_success(self, user_service, mock_supabase):
        """Test user authentication"""
        email = "auth@example.com"
        
        mock_res = MagicMock()
        mock_res.user = MagicMock(id="au1", email=email)
        mock_res.user.user_metadata = {"name": "Auth User"}
        mock_res.session = MagicMock(access_token="atoken", refresh_token="rtoken")
        mock_supabase.auth.sign_in_with_password.return_value = mock_res
        
        result = user_service.authenticate_user(email, "password123")
        
        assert result is not None
        assert result["access_token"] == "atoken"
        assert result["id"] == "au1"

    @pytest.mark.asyncio
    @patch("utils.async_client.async_supabase")
    async def test_update_user_profile_async(self, mock_async_supabase, user_service):
        """Test async user profile update with JWT"""
        user_id = "u1"
        update_data = {"name": "Updated Name"}
        jwt_token = "valid-jwt"
        
        mock_async_supabase.update = AsyncMock(return_value=[{"id": user_id, "name": "Updated Name"}])
        
        result = await user_service.update_user_profile(user_id, update_data, jwt_token)
        
        assert result["name"] == "Updated Name"
        mock_async_supabase.update.assert_called_once()

    def test_get_user_by_id_failure(self, user_service, mock_supabase_admin):
        """Test retrieving user by ID when not found"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])
        assert user_service.get_user_by_id("none") is None

    def test_get_user_by_id_exception(self, user_service, mock_supabase_admin):
        """Test retrieving user by ID with exception"""
        mock_supabase_admin.execute.side_effect = Exception("DB Error")
        assert user_service.get_user_by_id("err") is None

    def test_get_user_by_email_failure(self, user_service, mock_supabase_admin):
        """Test retrieving user by email when not found"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])
        assert user_service.get_user_by_email("none@test.com") is None

    def test_get_user_by_username_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by username"""
        mock_supabase_admin.execute.return_value = MagicMock(data={"username": "catlady", "id": "u1", "email": "c@t.com", "name": "Cat Lady"})
        user = user_service.get_user_by_username("catlady")
        assert user is not None
        assert user.id == "u1"

    def test_get_user_by_username_exception(self, user_service, mock_supabase_admin):
        """Test retrieving user by username with exception"""
        mock_supabase_admin.execute.side_effect = Exception("DB Error")
        assert user_service.get_user_by_username("catlady") is None

    @patch("services.user_service.email_service")
    def test_create_user_failure_no_user(self, mock_email_service, user_service, mock_supabase_admin):
        """Test user creation failure when generate_link returns no user"""
        mock_res = MagicMock(user=None)
        mock_supabase_admin.auth.admin.generate_link.return_value = mock_res
        with pytest.raises(PurrfectSpotsException, match="Failed to create user"):
            user_service.create_user_with_password("f@t.com", "pass", "fail")

    @patch("services.user_service.email_service")
    def test_create_user_failure_no_link(self, mock_email_service, user_service, mock_supabase_admin):
        """Test user creation failure when no action_link is returned"""
        mock_res = MagicMock()
        mock_res.user = MagicMock(id="u1")
        mock_res.properties = MagicMock()
        del mock_res.properties.action_link
        mock_supabase_admin.auth.admin.generate_link.return_value = mock_res
        with pytest.raises(PurrfectSpotsException, match="Failed to generate confirmation link"):
            user_service.create_user_with_password("f@t.com", "pass", "fail")

    @patch("services.user_service.email_service")
    def test_create_user_email_send_failure(self, mock_email_service, user_service, mock_supabase_admin):
        """Test user creation when email fails but user is created"""
        mock_res = MagicMock()
        mock_res.user = MagicMock(id="u1", created_at="2024", email="e@t.com")
        mock_res.properties = MagicMock(action_link="link")
        mock_supabase_admin.auth.admin.generate_link.return_value = mock_res
        mock_email_service.send_confirmation_email.return_value = False
        
        result = user_service.create_user_with_password("e@t.com", "pass", "Name")
        assert result["id"] == "u1"

    def test_create_unverified_user_failure(self, user_service, mock_supabase_admin):
        """Test unverified user creation failure"""
        mock_supabase_admin.auth.admin.create_user.return_value = None
        with pytest.raises(PurrfectSpotsException, match="Failed to create user"):
            user_service.create_unverified_user("e@t.com", "pass", "User")

    def test_get_user_by_email_exception(self, user_service, mock_supabase_admin):
        """Test retrieving user by email with exception"""
        mock_supabase_admin.execute.side_effect = Exception("DB Error")
        assert user_service.get_user_by_email("err@test.com") is None

    def test_create_user_alias(self, user_service, mock_supabase_admin):
        """Test the create_user alias"""
        # Just ensure it calls create_user_with_password
        with patch.object(user_service, "create_user_with_password") as mock_create:
            user_service.create_user("e@t.com", "p", "n")
            mock_create.assert_called_once_with("e@t.com", "p", "n")

    def test_create_unverified_user_conflict(self, user_service, mock_supabase_admin):
        """Test unverified user creation conflict (already exists)"""
        mock_supabase_admin.auth.admin.create_user.side_effect = Exception("Email already registered")
        from exceptions import ConflictError
        with pytest.raises(ConflictError):
            user_service.create_unverified_user("e@t.com", "pass", "User")

    def test_create_unverified_user_unique_constraint(self, user_service, mock_supabase_admin):
        """Test unverified user creation with unique constraint error"""
        mock_supabase_admin.auth.admin.create_user.side_effect = Exception("unique constraint violation")
        from exceptions import ConflictError
        with pytest.raises(ConflictError):
            user_service.create_unverified_user("e@t.com", "pass", "User")

    def test_create_or_get_user_missing_id(self, user_service):
        """Test create_or_get_user with missing ID"""
        with pytest.raises( PurrfectSpotsException, match="Database error"): # Error handling wraps it
             user_service.create_or_get_user({})

    def test_authenticate_user_failure(self, user_service, mock_supabase):
        """Test authentication failure"""
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid")
        assert user_service.authenticate_user("e@t.com", "wrong") is None

    def test_get_user_by_username_not_found(self, user_service, mock_supabase_admin):
        """Test retrieving user by username when not found"""
        mock_supabase_admin.execute.return_value = MagicMock(data=None)
        assert user_service.get_user_by_username("none") is None

    @patch("services.user_service.email_service")
    def test_create_user_email_conflict(self, mock_email_service, user_service, mock_supabase_admin):
        """Test user creation conflict"""
        mock_supabase_admin.auth.admin.generate_link.side_effect = Exception("Email already registered")
        from exceptions import ConflictError
        with pytest.raises(ConflictError):
            user_service.create_user_with_password("existing@t.com", "pass", "User")

    def test_authenticate_user_no_user(self, user_service, mock_supabase):
        """Test authentication with no user in response"""
        mock_res = MagicMock(user=None, session=None)
        mock_supabase.auth.sign_in_with_password.return_value = mock_res
        assert user_service.authenticate_user("e@t.com", "pass") is None

    @pytest.mark.asyncio
    @patch("utils.async_client.async_supabase")
    async def test_update_user_profile_not_found(self, mock_async_supabase, user_service):
        """Test update failure when user not found"""
        mock_async_supabase.update = AsyncMock(return_value=[])
        with pytest.raises(PurrfectSpotsException, match="User not found"):
            await user_service.update_user_profile("u1", {"name": "X"}, "token")

    @pytest.mark.asyncio
    async def test_update_user_profile_sync_fallback(self, user_service, mock_supabase_admin):
        """Test sync fallback for user profile update without JWT"""
        user_id = "u2"
        update_data = {"bio": "New bio"}
        
        # We need a real-ish object for res.data to work correctly with .data[0]
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_supabase_admin.execute.return_value = MockResponse([{"id": user_id, "bio": "New bio"}])
        
        result = await user_service.update_user_profile(user_id, update_data)
        assert result["bio"] == "New bio"

    @pytest.mark.asyncio
    async def test_update_user_profile_sync_not_found(self, user_service, mock_supabase_admin):
        """Test sync fallback when user is not found"""
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_supabase_admin.execute.return_value = MockResponse([])
        with pytest.raises(PurrfectSpotsException, match="User not found"):
            await user_service.update_user_profile("nonexistent", {"name": "X"})
