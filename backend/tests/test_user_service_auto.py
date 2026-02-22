from unittest.mock import AsyncMock, MagicMock

import pytest

from services.user_service import UserService


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    mock_admin = MagicMock()

    user_data = {
        "id": "1",
        "email": "a@a.com",
        "name": "A",
        "username": "A",
        "picture": "",
        "bio": None,
        "roles": {"name": "user", "role_permissions": []},
    }

    role_data = {"id": "user-role-id"}

    mock_eq_user = MagicMock()
    mock_eq_user.execute = AsyncMock(return_value=MagicMock(data=[user_data]))
    mock_eq_user.maybe_single.return_value.execute = AsyncMock(return_value=MagicMock(data=user_data))

    mock_eq_role = MagicMock()
    mock_eq_role.execute = AsyncMock(return_value=MagicMock(data=[role_data]))

    mock_select_user = MagicMock()
    mock_select_user.eq.return_value = mock_eq_user

    mock_select_role = MagicMock()
    mock_select_role.eq.return_value = mock_eq_role

    def table_mock(name):
        _table = MagicMock()
        if name == "roles":
            _table.select.return_value = mock_select_role
        else:
            _table.select.return_value = mock_select_user
        _table.upsert.return_value.execute = AsyncMock()

        _update = MagicMock()
        _update.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": "1", "updated": True}]))
        _table.update.return_value = _update
        return _table

    mock_admin.table = table_mock

    mock_admin.auth.admin.create_user = AsyncMock(
        return_value=MagicMock(user=MagicMock(id="1", email="a@a.com", created_at="2023"))
    )

    mock.auth.sign_in_with_password = AsyncMock(
        return_value=MagicMock(
            user=MagicMock(id="1", email="a@a.com", user_metadata={"name": "A"}, created_at="2023"),
            session=MagicMock(access_token="acc", refresh_token="ref"),
        )
    )

    return mock, mock_admin


@pytest.fixture
def user_service(mock_supabase):
    client, admin = mock_supabase
    return UserService(supabase_client=client, supabase_admin=admin)


@pytest.mark.asyncio
async def test_get_user_role_id(user_service):
    UserService._cached_user_role_id = None
    role_id = await user_service._get_user_role_id()
    assert role_id == "user-role-id"
    # test cached
    role_id2 = await user_service._get_user_role_id()
    assert role_id2 == "user-role-id"


@pytest.mark.asyncio
async def test_get_user_by_id(user_service):
    user = await user_service.get_user_by_id("1")
    assert user is not None
    assert user.id == "1"


@pytest.mark.asyncio
async def test_get_user_by_email(user_service):
    user = await user_service.get_user_by_email("a@a.com")
    assert user is not None
    assert user["id"] == "1"


@pytest.mark.asyncio
async def test_get_user_by_username(user_service):
    user = await user_service.get_user_by_username("A")
    assert user is not None


@pytest.mark.asyncio
async def test_create_unverified_user(user_service):
    user = await user_service.create_unverified_user("a@a.com", "pass", "A")
    assert user["id"] == "1"


@pytest.mark.asyncio
async def test_create_or_get_user(user_service):
    # Because get_user_by_id is called at the end and returns a mapped user
    UserService._cached_user_role_id = "user-role-id"
    user = await user_service.create_or_get_user({"id": "1", "email": "a@a.com", "name": "A"})
    assert user is not None


@pytest.mark.asyncio
async def test_authenticate_user(user_service):
    res = await user_service.authenticate_user("a@a.com", "pass")
    assert res is not None


@pytest.mark.asyncio
async def test_update_user_profile(user_service):
    res = await user_service.update_user_profile("1", {"name": "B"})
    assert res["id"] == "1"
    assert res["updated"] is True
