"""
Tests for user service
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from exceptions import PurrfectSpotsException
from services.user_service import UserService


@pytest.mark.asyncio
class TestUserService:
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock = MagicMock()
        mock.auth = MagicMock()
        mock.auth.sign_in_with_password = AsyncMock()
        return mock

    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase admin client"""
        mock = MagicMock()

        # Create a chainable mock object
        chain_mock = MagicMock()
        chain_mock.select.return_value = chain_mock
        chain_mock.eq.return_value = chain_mock
        chain_mock.maybe_single.return_value = chain_mock
        chain_mock.single.return_value = chain_mock
        chain_mock.update.return_value = chain_mock
        chain_mock.upsert.return_value = chain_mock
        chain_mock.is_.return_value = chain_mock
        chain_mock.order.return_value = chain_mock
        chain_mock.limit.return_value = chain_mock

        # Default execute return
        chain_mock.execute = AsyncMock(return_value=MagicMock(data=[], count=0))

        mock.table = MagicMock(return_value=chain_mock)
        mock.auth = MagicMock()
        mock.auth.admin = MagicMock()
        mock.auth.admin.create_user = AsyncMock()

        return mock

    @pytest.fixture
    async def user_service(self, mock_supabase, mock_supabase_admin):
        """Create UserService instance with mocked dependencies"""
        # Patch the async getter
        with patch(
            "services.user_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase_admin)
        ):
            service = UserService(mock_supabase)
            yield service

    async def test_get_user_by_id_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by ID"""
        user_id = "user-123"
        mock_result = MagicMock(data=[{"id": user_id, "email": "test@example.com", "name": "Test User"}])

        # Configure the mock chain return value
        chain = mock_supabase_admin.table.return_value
        chain.select.return_value.eq.return_value.execute.return_value = mock_result

        user = await user_service.get_user_by_id(user_id)

        assert user is not None
        assert user.id == user_id
        mock_supabase_admin.table.assert_called_with("users")

    async def test_get_user_by_email_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by email"""
        email = "test@example.com"
        mock_result = MagicMock(data={"email": email, "id": "u1"})

        chain = mock_supabase_admin.table.return_value
        chain.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        user_data = await user_service.get_user_by_email(email)

        assert user_data is not None
        assert user_data["email"] == email

    async def test_get_user_by_username_success(self, user_service, mock_supabase_admin):
        """Test retrieving user by username"""
        username = "testuser"
        mock_result = MagicMock(data={"id": "u1", "username": username, "email": "e@t.com", "name": "Test User"})

        chain = mock_supabase_admin.table.return_value
        chain.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_result

        user = await user_service.get_user_by_username(username)

        assert user is not None
        assert user.username == username

    async def test_authenticate_user_no_user(self, user_service, mock_supabase):
        """Test authentication with no user in response"""
        mock_res = MagicMock(user=None, session=None)
        mock_supabase.auth.sign_in_with_password.return_value = mock_res

        result = await user_service.authenticate_user("e@t.com", "pass")
        assert result is None

    async def test_update_user_profile_success(self, user_service, mock_supabase_admin):
        """Test successful profile update"""
        user_id = "u1"
        update_data = {"name": "New Name"}
        mock_result = MagicMock(data=[{"id": user_id, "name": "New Name"}])

        chain = mock_supabase_admin.table.return_value
        chain.update.return_value.eq.return_value.execute.return_value = mock_result

        result = await user_service.update_user_profile(user_id, update_data)
        assert result["name"] == "New Name"

    async def test_update_user_profile_not_found(self, user_service, mock_supabase_admin):
        """Test update failure when user not found"""
        chain = mock_supabase_admin.table.return_value
        chain.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with pytest.raises(PurrfectSpotsException, match="Failed to update profile"):
            await user_service.update_user_profile("u1", {"name": "X"})
