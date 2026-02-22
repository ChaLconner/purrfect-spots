import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.auth_service import AuthService
from user_models.user import User
from datetime import datetime

@pytest.fixture
def auth_service():
    mock_supabase = MagicMock()
    mock_admin = MagicMock()
    service = AuthService(supabase_client=mock_supabase, supabase_admin=mock_admin)
    service.user_service = MagicMock()
    service.user_service.create_or_get_user = AsyncMock(return_value=User(id="1", email="a@a.com", name="A", created_at=datetime.utcnow()))
    service.user_service.get_user_by_id = AsyncMock(return_value=User(id="1", email="a@a.com", name="A", created_at=datetime.utcnow()))
    service.user_service.authenticate_user = AsyncMock(return_value=True)
    return service

@pytest.mark.asyncio
async def test_find_or_create_google_user(auth_service):
    mock_admin = AsyncMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": "1"}]))
    
    with patch.object(auth_service, "_get_admin_client", return_value=mock_admin):
        res = await auth_service._find_or_create_google_user({"email": "a@a.com", "name": "A", "picture": "P"}, "g1")
        assert res is not None

@pytest.mark.asyncio
async def test_is_token_revoked(auth_service):
    mock_ts = MagicMock()
    mock_ts.is_blacklisted = AsyncMock(return_value=True)
    with patch("services.auth_service.get_token_service", new_callable=AsyncMock, return_value=mock_ts):
        res = await auth_service.is_token_revoked("jti1")
        assert res is True
        
    res2 = await auth_service.is_token_revoked("")
    assert res2 is False

@pytest.mark.asyncio
async def test_revoke_token(auth_service):
    mock_ts = MagicMock()
    mock_ts.blacklist_token = AsyncMock(return_value=True)
    with patch("services.auth_service.get_token_service", new_callable=AsyncMock, return_value=mock_ts):
        res = await auth_service.revoke_token("jti1", "u1", datetime.utcnow())
        assert res is True

def test_verify_google_token(auth_service):
    with patch("services.auth_service.google_auth_service.verify_google_token", return_value={"id": "1"}):
        res = auth_service.verify_google_token("tok")
        assert res["id"] == "1"

@pytest.mark.asyncio
async def test_confirm_user_email(auth_service):
    mock_admin = AsyncMock()
    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": "1"}]))
    mock_admin.auth.admin.update_user_by_id = AsyncMock()
    with patch.object(auth_service, "_get_admin_client", return_value=mock_admin):
        res = await auth_service.confirm_user_email("a@a.com")
        assert res is not None
        
    mock_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))
    with patch.object(auth_service, "_get_admin_client", return_value=mock_admin):
        res = await auth_service.confirm_user_email("a@a.com")
        assert res is False

@pytest.mark.asyncio
async def test_exchange_google_code(auth_service):
    mock_gas = MagicMock()
    mock_gas.exchange_google_code = AsyncMock(return_value={"user_info": {"google_id": "g1", "email": "a@a.com"}})
    with patch("services.auth_service.google_auth_service", mock_gas):
        res = await auth_service.exchange_google_code("code", "cv", "ru")
        assert res.access_token is not None
        assert res.refresh_token is not None

@pytest.mark.asyncio
async def test_verify_refresh_token(auth_service):
    token = auth_service.create_refresh_token("u1", "127.0.0.1", "agent")
    with patch.object(auth_service, "is_token_revoked", return_value=False):
        res = await auth_service.verify_refresh_token(token, "127.0.0.1", "agent")
        assert res is not None
        assert res["type"] == "refresh"

@pytest.mark.asyncio
async def test_create_password_reset_token(auth_service):
    mock_admin = AsyncMock()
    mock_res = MagicMock()
    mock_res.properties.action_link = "http://link"
    mock_admin.auth.admin.generate_link = AsyncMock(return_value=mock_res)
    with patch.object(auth_service, "_get_admin_client", return_value=mock_admin), \
         patch("services.auth_service.email_service.send_reset_email", return_value=True):
        res = await auth_service.create_password_reset_token("a@a.com")
        assert res is True

@pytest.mark.asyncio
async def test_change_password(auth_service):
    mock_admin = AsyncMock()
    mock_admin.auth.admin.update_user_by_id = AsyncMock()
    mock_ts = MagicMock()
    mock_ts.blacklist_all_user_tokens = AsyncMock()
    
    with patch.object(auth_service, "_get_admin_client", return_value=mock_admin), \
         patch("services.auth_service.password_service.validate_new_password", new_callable=AsyncMock, return_value=(True, None)), \
         patch("services.auth_service.get_token_service", new_callable=AsyncMock, return_value=mock_ts), \
         patch("services.auth_service.email_service.send_password_changed_email") as mock_email:
        res = await auth_service.change_password("u1", "old", "new")
        assert res is True
        mock_email.assert_called_once()
