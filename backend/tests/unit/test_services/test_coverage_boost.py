import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import config
from middleware.csrf_middleware import CSRFMiddleware
from services.otp_service import OTPService
from services.subscription_service import SubscriptionService
from services.treats_service import TreatsService
from services.user_service import UserService


@pytest.fixture
def mock_supabase():
    builder = MagicMock()
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.maybe_single.return_value = builder
    builder.single.return_value = builder
    builder.order.return_value = builder
    builder.limit.return_value = builder
    builder.update.return_value = builder
    builder.insert.return_value = builder
    builder.delete.return_value = builder
    builder.rpc.return_value = builder
    builder.execute = AsyncMock()

    mock = MagicMock()
    mock.table.return_value = builder
    mock.rpc.return_value = builder
    return mock


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# --- SubscriptionService Tests ---


@pytest.mark.asyncio
async def test_subscription_get_status_fallback(mock_supabase):
    service = SubscriptionService(mock_supabase)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )

    status = await service.get_subscription_status("user_123")
    assert status["is_pro"] is False
    assert status["treat_balance"] == 0


@pytest.mark.asyncio
@patch("services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_invoice_paid_success(mock_retrieve, mock_supabase):
    service = SubscriptionService(mock_supabase)

    invoice = {"customer": "cus_123", "subscription": "sub_123"}

    mock_sub = MagicMock()
    mock_sub.status = "active"
    mock_sub.current_period_end = 1700000000
    mock_sub.cancel_at_period_end = False
    mock_sub.items = {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]}
    mock_retrieve.return_value = mock_sub

    await service._handle_invoice_paid(invoice)

    # Verify update to DB happened
    mock_supabase.table.return_value.update.assert_called()


@pytest.mark.asyncio
@pytest.mark.asyncio
@patch("services.subscription_service.stripe.Subscription.list")
@patch("services.subscription_service.stripe.Subscription.modify")
async def test_cancel_subscription_success(mock_modify, mock_list, mock_supabase):
    service = SubscriptionService(mock_supabase)

    # Mock user data via _get_user_data
    # Note: SubscriptionService._get_user_data uses .limit(1)
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        MagicMock(data=[{"stripe_customer_id": "cus_123"}])
    )

    # Mock active subscriptions
    mock_sub = MagicMock()
    mock_sub.id = "sub_123"
    mock_list.return_value = MagicMock(data=[mock_sub])

    await service.cancel_subscription("user_123")

    mock_modify.assert_called_once()


# --- TreatsService Tests ---


@pytest.mark.asyncio
async def test_treats_get_balance_sql(mock_supabase, mock_db):
    service = TreatsService(mock_supabase, db=mock_db)

    # Mock balance query result
    balance_mock = MagicMock()
    balance_mock.fetchone.return_value = [100]

    # Mock transactions query result
    trans_mock = MagicMock()
    trans_mock.__iter__.return_value = [MagicMock(_mapping={"id": "t1", "amount": 10})]

    mock_db.execute.side_effect = [balance_mock, trans_mock]

    res = await service.get_balance("user_123")
    assert res["balance"] == 100
    assert len(res["recent_transactions"]) == 1


@pytest.mark.asyncio
async def test_treats_give_treat_sql_success(mock_supabase, mock_db):
    service = TreatsService(mock_supabase, db=mock_db)

    # Mock RPC result
    rpc_res = MagicMock()
    rpc_res.fetchone.return_value = [True, None, "receiver_123", 50]
    mock_db.execute.return_value = rpc_res

    # Mock user name fetch for notification
    user_res = MagicMock()
    user_res.fetchone.return_value = ["SenderName"]

    # notification_service mock
    service.notification_service.create_notification = AsyncMock()

    # We need to handle multiple calls to execute
    mock_db.execute.side_effect = [rpc_res, user_res]

    res = await service.give_treat("sender_123", "photo_123", 10)

    assert res["success"] is True
    assert res["new_balance"] == 50
    mock_db.commit.assert_called()


# --- OTPService Tests ---


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_otp_lockout_redis(mock_redis_from_url, mock_supabase):
    import os

    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost"}):
        service = OTPService(mock_supabase)

        # Mock redis client
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        # Mock context manager
        mock_redis_from_url.return_value.__aenter__.return_value = mock_redis

        locked = await service._is_email_locked_out("test@example.com")
        assert locked is True
        mock_redis.exists.assert_called_with("otp_lockout:test@example.com")


@pytest.mark.asyncio
async def test_otp_verify_expired(mock_supabase, mock_db):
    service = OTPService(mock_supabase, db=mock_db)

    # Mock record
    record = {"id": 1, "otp_hash": "hash", "attempts": 0, "max_attempts": 5, "expires_at": "2020-01-01T00:00:00Z"}
    mock_res = MagicMock()
    mock_res.fetchone.return_value = MagicMock(_mapping=record)
    mock_db.execute.return_value = mock_res

    res = await service.verify_otp("test@example.com", "123456")
    assert res["success"] is False
    assert "expired" in res["error"]


@pytest.mark.asyncio
async def test_otp_verify_wrong_code(mock_supabase, mock_db):
    service = OTPService(mock_supabase, db=mock_db)

    # Mock record
    record = {
        "id": 1,
        "otp_hash": "different_hash",
        "attempts": 0,
        "max_attempts": 5,
        "expires_at": "2099-01-01T00:00:00Z",
    }
    mock_res = MagicMock()
    mock_res.fetchone.return_value = MagicMock(_mapping=record)
    mock_db.execute.return_value = mock_res

    # Mock update attempts
    mock_db.execute.side_effect = [mock_res, MagicMock()]

    res = await service.verify_otp("test@example.com", "123456")
    assert res["success"] is False
    assert res["attempts_remaining"] == 4
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_otp_can_resend_sql(mock_supabase, mock_db):
    service = OTPService(mock_supabase, db=mock_db)

    # Mock latest record
    mock_res = MagicMock()
    mock_res.fetchone.return_value = ["2020-01-01T00:00:00Z"]
    mock_db.execute.return_value = mock_res

    can_resend, remaining = await service.can_resend_otp("test@example.com")
    assert can_resend is True
    assert remaining == 0


# --- Middleware Tests ---


@pytest.mark.asyncio
async def test_csrf_middleware_exempt():
    app = AsyncMock()
    middleware = CSRFMiddleware(app)

    request = MagicMock()
    request.method = "POST"
    request.url.path = "/health"

    call_next = AsyncMock()
    await middleware.dispatch(request, call_next)

    call_next.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_csrf_middleware_production_missing_token():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = AsyncMock()
        middleware = CSRFMiddleware(app)

        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/v1/something"
        request.cookies = {}
        request.headers = {}

        response = await middleware.dispatch(request, AsyncMock())
        assert response.status_code == 403
        assert b"CSRF_TOKEN_MISSING" in response.body


@pytest.mark.asyncio
async def test_csrf_middleware_safe_method():
    app = AsyncMock()
    middleware = CSRFMiddleware(app)

    request = MagicMock()
    request.method = "GET"
    request.url.path = "/api/v1/gallery"
    request.cookies = {}

    call_next = AsyncMock(return_value=MagicMock())
    await middleware.dispatch(request, call_next)

    # Response from call_next should be returned
    call_next.assert_called_once_with(request)


# --- UserService Tests ---


@pytest.mark.asyncio
async def test_user_read_mixin_sql(mock_supabase, mock_db):
    service = UserService(mock_supabase, db=mock_db)

    # Needs to mock prefixed columns helper or ensure it works
    service._prefixed_user_columns = MagicMock(return_value="id, username")

    # Mock user query
    user_row = MagicMock()
    user_row._mapping = {
        "id": "u1",
        "username": "testuser",
        "role_name": "admin",
        "email": "test@test.com",
        "name": "Test User",
        "is_active": True,
        "is_pro": False,
    }

    # We need a separate MagicMock for each execute call's result
    res1 = MagicMock()
    res1.fetchone.return_value = user_row

    res2 = MagicMock()
    res2.__iter__.return_value = ["can_read"]

    mock_db.execute.side_effect = [res1, res2]

    user = await service.get_user_by_id("u1")
    assert user is not None
    assert user.id == "u1"
    assert user.role == "admin"


@pytest.mark.asyncio
async def test_user_get_by_email_sql(mock_supabase, mock_db):
    service = UserService(mock_supabase, db=mock_db)

    mock_row = MagicMock()
    mock_row._mapping = {"id": "u1", "email": "test@test.com"}
    res = MagicMock()
    res.fetchone.return_value = mock_row
    mock_db.execute.return_value = res

    res_data = await service.get_user_by_email("test@test.com")
    assert res_data["id"] == "u1"


@pytest.mark.asyncio
async def test_user_deletion_mixin_sql(mock_supabase, mock_db):
    service = UserService(mock_supabase, db=mock_db)

    # Mock get_user_by_id (inherited)
    service.get_user_by_id = AsyncMock(return_value=MagicMock(id="u1"))

    # Mock update call in mixin
    update_res = MagicMock()
    update_res.rowcount = 1

    # Mock three execute calls in request_account_deletion
    mock_db.execute.side_effect = [update_res, MagicMock(), MagicMock()]

    await service.request_account_deletion("u1", "127.0.0.1")
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_user_profile_mixin_create_sql(mock_supabase, mock_db):
    service = UserService(mock_supabase, db=mock_db)
    service._get_user_role_id = AsyncMock(return_value=1)
    service._prefixed_user_columns = MagicMock(return_value="id")

    user_data = {"id": "u1", "email": "new@test.com", "name": "NewUser"}

    # Mock check_row, upsert, get_user_by_id (two calls: user select and perm select)
    r1 = MagicMock()
    r1.fetchone.return_value = [1]

    r2 = MagicMock()  # upsert

    r3 = MagicMock()  # get_user select
    u_row = MagicMock()
    u_row._mapping = {"id": "u1", "role_name": "user", "email": "new@test.com", "name": "NewUser"}
    r3.fetchone.return_value = u_row

    r4 = MagicMock()  # get_perms select
    r4.__iter__.return_value = []

    # We need to reach the return user in create_or_get_user
    # Note: get_user_by_id is called inside.
    # We'll use side_effect for the sequence of db.execute calls.
    mock_db.execute.side_effect = [r1, r2, r3, r4]

    user = await service.create_or_get_user(user_data)
    assert user.id == "u1"


@pytest.mark.asyncio
async def test_user_auth_mixin_sql(mock_supabase, mock_db):
    service = UserService(mock_supabase, db=mock_db)

    # Mock sign_in_with_password
    mock_res = MagicMock()
    mock_res.user.id = "u1"
    mock_res.user.email = "test@test.com"
    mock_res.user.user_metadata = {"name": "Test"}
    mock_res.session.access_token = "atk"
    mock_res.session.refresh_token = "rtk"

    mock_supabase.auth.sign_in_with_password = AsyncMock(return_value=mock_res)
    service.get_user_by_id = AsyncMock(return_value=None)

    user_data = await service.authenticate_user("test@test.com", "password")
    assert user_data["id"] == "u1"
    assert user_data["access_token"] == "atk"
