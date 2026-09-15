import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.schemas.user import User
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    mock_supabase = MagicMock()
    mock_admin = MagicMock()
    service = AuthService(supabase_client=mock_supabase, supabase_admin=mock_admin)
    service.user_service = MagicMock()
    service.user_service.create_or_get_user = AsyncMock(
        return_value=User(id="1", email="a@a.com", name="A", created_at=datetime.now(UTC))
    )
    service.user_service.get_user_by_id = AsyncMock(
        return_value=User(id="1", email="a@a.com", name="A", created_at=datetime.now(UTC))
    )
    service.user_service.authenticate_user = AsyncMock(return_value=True)
    return service


@pytest.mark.asyncio
async def test_find_or_create_google_user(auth_service):
    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"id": "1"}])
    )

    with patch.object(auth_service, "_get_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_admin
        res = await auth_service._find_or_create_google_user({"email": "a@a.com", "name": "A", "picture": "P"}, "g1")
        assert res is not None


@pytest.mark.asyncio
async def test_exchange_google_code_normalizes_existing_sql_user_uuid(auth_service):
    existing_user_id = UUID("00000000-0000-4000-a000-000000000123")
    db_result = MagicMock()
    db_result.fetchone.return_value = (existing_user_id,)
    auth_service._db = MagicMock()
    auth_service._db.execute = AsyncMock(return_value=db_result)

    async def create_or_get_user(user_data):
        json.dumps(user_data)
        return User(
            id=str(existing_user_id),
            email="a@a.com",
            name="A",
            google_id="g1",
            created_at=datetime.now(UTC),
        )

    auth_service.user_service.create_or_get_user.side_effect = create_or_get_user
    mock_google_auth = MagicMock()
    mock_google_auth.exchange_google_code = AsyncMock(
        return_value={"user_info": {"google_id": "g1", "email": "a@a.com", "name": "A"}}
    )

    with patch("app.services.auth.oauth_mixin.google_auth_service", mock_google_auth):
        response = await auth_service.exchange_google_code("code", "verifier", "https://example.com/auth/callback")

    assert response.user.id == str(existing_user_id)


@pytest.mark.asyncio
async def test_find_user_sql_normalizes_email_link_uuid(auth_service):
    existing_user_id = UUID("00000000-0000-4000-a000-000000000124")
    google_result = MagicMock()
    google_result.fetchone.return_value = None
    email_result = MagicMock()
    email_result.fetchone.return_value = (existing_user_id,)
    auth_service._db = MagicMock()
    auth_service._db.execute = AsyncMock(side_effect=[google_result, email_result, MagicMock()])
    auth_service._db.commit = AsyncMock()

    user_id = await auth_service._find_user_sql("g1", "a@a.com")

    assert user_id == str(existing_user_id)
    assert isinstance(user_id, str)


@pytest.mark.asyncio
async def test_is_token_revoked(auth_service):
    mock_ts = MagicMock()
    mock_ts.is_blacklisted = AsyncMock(return_value=True)
    with patch("app.services.auth.token_mixin.get_token_service", new_callable=AsyncMock, return_value=mock_ts):
        res = await auth_service.is_token_revoked("jti1")
        assert res is True

    res2 = await auth_service.is_token_revoked("")
    assert res2 is False


@pytest.mark.asyncio
async def test_revoke_token(auth_service):
    mock_ts = MagicMock()
    mock_ts.blacklist_token = AsyncMock(return_value=True)
    with patch(
        "app.services.auth.token_mixin.get_token_service", new_callable=AsyncMock, return_value=mock_ts
    ) as mock_get:
        res = await auth_service.revoke_token("jti1", "u1", datetime.now(UTC))
        assert res is True
        mock_get.assert_awaited_once_with(auth_service.db)


def test_verify_google_token(auth_service) -> None:
    with patch("app.services.auth.oauth_mixin.google_auth_service.verify_google_token", return_value={"id": "1"}):
        res = auth_service.verify_google_token("tok")
        assert res["id"] == "1"


@pytest.mark.asyncio
async def test_confirm_user_email(auth_service):
    mock_admin = MagicMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"id": "1"}])
    )
    mock_admin.auth.admin.update_user_by_id = AsyncMock()
    with patch.object(auth_service, "_get_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_admin
        res = await auth_service.confirm_user_email("a@a.com")
        assert res is not None

    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    with patch.object(auth_service, "_get_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_admin
        res = await auth_service.confirm_user_email("a@a.com")
        assert res is False


@pytest.mark.asyncio
async def test_exchange_google_code(auth_service):
    mock_gas = MagicMock()
    mock_gas.exchange_google_code = AsyncMock(return_value={"user_info": {"google_id": "g1", "email": "a@a.com"}})
    with (
        patch("app.services.auth.oauth_mixin.google_auth_service", mock_gas),
        patch.object(auth_service, "_find_user_supabase", new=AsyncMock(return_value="u1")),
    ):
        res = await auth_service.exchange_google_code("code", "cv", "ru")
        assert res.access_token is not None
        assert not hasattr(res, "refresh_token") or res.refresh_token is None


@pytest.mark.asyncio
async def test_verify_refresh_token(auth_service):
    token = auth_service.create_refresh_token("u1", "127.0.0.1", "agent")
    token_service = AsyncMock()
    token_service.is_user_invalidated.return_value = False
    with (
        patch.object(auth_service, "is_token_revoked", return_value=False),
        patch("app.services.auth.token_mixin.get_token_service", new=AsyncMock(return_value=token_service)),
    ):
        res = await auth_service.verify_refresh_token(token, "127.0.0.1", "agent")
        assert res is not None
        assert res["type"] == "refresh"


@pytest.mark.asyncio
async def test_create_password_reset_token(auth_service):
    mock_admin = MagicMock()
    mock_res = MagicMock()
    mock_res.properties.action_link = "http://link"  # NOSONAR python:S5332 - test fixture URL
    mock_admin.auth.admin.generate_link = AsyncMock(return_value=mock_res)
    with (
        patch.object(auth_service, "_get_admin_client", new_callable=AsyncMock) as mock_get_admin,
        patch("app.services.auth.password_mixin.email_service.send_reset_email", return_value=True),
    ):
        mock_get_admin.return_value = mock_admin
        res = await auth_service.create_password_reset_token("a@a.com")
        assert res is True


@pytest.mark.asyncio
async def test_change_password(auth_service):
    mock_admin = MagicMock()
    mock_admin.auth.admin.update_user_by_id = AsyncMock()
    mock_ts = MagicMock()
    mock_ts.blacklist_all_user_tokens = AsyncMock()

    with (
        patch.object(auth_service, "_get_admin_client", new_callable=AsyncMock) as mock_get_admin,
        patch(
            "app.services.auth.password_mixin.password_service.validate_new_password",
            new_callable=AsyncMock,
            return_value=(True, None),
        ),
        patch("app.services.auth.password_mixin.get_token_service", new_callable=AsyncMock, return_value=mock_ts),
        patch("app.services.auth.password_mixin.email_service.send_password_changed_email") as mock_email,
    ):
        mock_get_admin.return_value = mock_admin
        res = await auth_service.change_password("u1", "old", "new")
        assert res is True
        mock_email.assert_called_once()
