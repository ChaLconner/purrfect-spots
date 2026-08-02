from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.treats_service import TreatsService


@pytest.fixture
def treats_service():
    from unittest.mock import AsyncMock

    mock_supabase = MagicMock()
    # Mock chain: .table().select().eq().single().execute()
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock()
    mock_supabase.table.return_value.select.return_value.or_.return_value.order.return_value.limit.return_value.execute = AsyncMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute = AsyncMock()
    mock_supabase.rpc.return_value.execute = AsyncMock()

    service = TreatsService(mock_supabase)
    service.notification_service = MagicMock()
    service.notification_service.create_notification = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_give_treat_success_with_to_user_id(treats_service):
    """Test give_treat when RPC returns to_user_id (optimized path)."""
    admin_mock = MagicMock()
    # Configure RPC return
    admin_mock.rpc.return_value.execute = AsyncMock(
        return_value=MagicMock(
            data=[{"success": True, "new_balance": 90, "to_user_id": "22222222-2222-4222-a222-222222222222"}]
        )
    )
    with patch("app.utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = admin_mock

        # Mock actor name query
        mock_user_query = MagicMock()
        mock_user_query.data = {"name": "Test User"}
        treats_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query

        res = await treats_service.give_treat(
            "11111111-1111-4111-a111-111111111111", "00000000-0000-4000-b000-000000000123", 10, jwt_token="token"
        )

        assert res["success"] is True
        assert res["new_balance"] == 90

        admin_mock.rpc.assert_called_with(
            "give_treat_atomic",
            {
                "p_from_user_id": "11111111-1111-4111-a111-111111111111",
                "p_photo_id": "00000000-0000-4000-b000-000000000123",
                "p_amount": 10,
            },
        )


@pytest.mark.asyncio
async def test_give_treat_supabase_accepts_scalar_json_object(treats_service):
    """PostgREST may return a scalar JSON RPC result as an object, not a row list."""
    admin_mock = MagicMock()
    admin_mock.rpc.return_value.execute = AsyncMock(
        return_value=MagicMock(
            data={"success": True, "new_balance": 90, "to_user_id": "22222222-2222-4222-a222-222222222222"}
        )
    )

    with patch("app.utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = admin_mock
        result = await treats_service._give_treat_supabase(
            "11111111-1111-4111-a111-111111111111",
            "00000000-0000-4000-b000-000000000123",
            10,
        )

    assert result["success"] is True
    assert result["new_balance"] == 90


@pytest.mark.asyncio
async def test_treat_sql_rpcs_decode_json_results():
    """Direct SQL paths must decode the JSON returned by both atomic RPCs."""
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchone=MagicMock(return_value=(True, None, "22222222-2222-4222-a222-222222222222", 90))),
            MagicMock(fetchone=MagicMock(return_value=(None, False, 120))),
        ]
    )
    db.commit = AsyncMock()
    service = TreatsService(MagicMock(), db=db)

    result = await service._give_treat_sql(
        "11111111-1111-4111-a111-111111111111",
        "00000000-0000-4000-b000-000000000123",
        10,
    )
    await service._fulfill_purchase_sql(
        "11111111-1111-4111-a111-111111111111",
        30,
        "Purchased test pack",
        "cs_test_123",
    )

    assert result == {
        "to_user_id": "22222222-2222-4222-a222-222222222222",
        "new_balance": 90,
    }
    assert all("json_to_record" in str(call.args[0]) for call in db.execute.await_args_list)
    assert db.commit.await_count == 2


@pytest.mark.asyncio
async def test_give_treat_success_fallback_notification(treats_service):
    """Test give_treat when RPC doesn't return to_user_id (fallback path)."""
    admin_mock = MagicMock()
    admin_mock.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"success": True, "new_balance": 90}]))

    with patch("app.utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = admin_mock

        # Mock chain for fallback queries
        mock_photo_query = MagicMock()
        mock_photo_query.data = {"user_id": "22222222-2222-4222-a222-222222222222"}

        mock_user_query = MagicMock()
        mock_user_query.data = {"name": "Test User"}

        def table_side_effect(table_name):
            mock_chain = MagicMock()
            mock_chain.select.return_value.eq.return_value.single.return_value.execute = AsyncMock()
            if table_name == "cat_photos":
                mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    mock_photo_query
                )
            elif table_name == "users":
                mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    mock_user_query
                )
            return mock_chain

        treats_service.supabase.table.side_effect = table_side_effect

        res = await treats_service.give_treat(
            "11111111-1111-4111-a111-111111111111", "00000000-0000-4000-b000-000000000123", 10, jwt_token="token"
        )

        assert res["success"] is True


@pytest.mark.asyncio
async def test_give_treat_failure(treats_service):
    """Test give_treat with insufficient balance."""
    admin_mock = MagicMock()
    admin_mock.rpc.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"success": False, "error": "Insufficient treats"}])
    )
    with patch("app.utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = admin_mock

        with pytest.raises(ValueError, match="Insufficient treats"):
            await treats_service.give_treat(
                "11111111-1111-4111-a111-111111111111", "00000000-0000-4000-b000-000000000123", 10
            )


# Tests for other methods that still use sync client don't need async_supabase patching
# But they DO need run_in_threadpool patching if logic imports it?
# The service imports `run_in_threadpool` from `starlette.concurrency`.
# Since we are not running in a real Starlette app, we might need to verify behavior or just let it run if calling direct?
# The original tests didn't patch `run_in_threadpool`, implying `treats_service.py` calls were awaited directly?
# Ah, `await run_in_threadpool(lambda: ...)` works in tests if `anyio` or `asyncio` loop is running?
# Actually, `run_in_threadpool` uses `anyio.to_thread.run_sync`.
# If `mock_supabase` is MagicMock, calling it in threadpool is fine.


@pytest.mark.asyncio
async def test_get_balance(treats_service):
    """Test get_balance returns correct structure."""
    # This method uses run_in_threadpool + sync client
    mock_user = MagicMock()
    mock_user.data = {"treat_balance": 42}

    mock_trans = MagicMock()
    mock_trans.data = [{"id": "t1", "amount": 5, "transaction_type": "give"}]

    def side_effect(table_name):
        mock_chain = MagicMock()
        mock_chain.select.return_value.eq.return_value.maybe_single.return_value.execute = AsyncMock()
        mock_chain.select.return_value.or_.return_value.order.return_value.limit.return_value.execute = AsyncMock()

        if table_name == "users":
            mock_chain.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_user
        elif table_name == "treats_transactions":
            mock_chain.select.return_value.or_.return_value.order.return_value.limit.return_value.execute.return_value = mock_trans
        return mock_chain

    treats_service.supabase.table.side_effect = side_effect

    res = await treats_service.get_balance("00000000-0000-4000-a000-000000000123")
    assert res["balance"] == 42
    assert len(res["recent_transactions"]) == 1


@pytest.mark.asyncio
async def test_fulfill_treat_purchase_idempotent(treats_service):
    """Test that duplicate purchase fulfillment is handled gracefully."""
    # This also uses run_in_threadpool + sync client
    session = {
        "metadata": {"user_id": "00000000-0000-4000-a000-000000000123", "package": "small"},
        "id": "sess_dup_1",
    }

    # Mock package lookup
    mock_pkg = MagicMock()
    mock_pkg.data = [
        {
            "id": "small",
            "amount": 5,
            "price": "1.99",
            "name": "Snack Pack",
            "bonus": 0,
            "price_per_treat": "0.40",
            "price_id": "price_small",
            "is_active": True,
        }
    ]
    treats_service.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_pkg

    # Mock RPC returning duplicate
    mock_rpc = MagicMock()
    mock_rpc.data = {"success": True, "duplicate": True, "new_balance": 42}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc

    # Should not raise
    await treats_service.fulfill_treat_purchase(session)


@pytest.mark.asyncio
@patch("app.services.treats_service.stripe.checkout.Session.create")
async def test_purchase_treats_checkout_invalid_customer_fallback(mock_session_create, treats_service):
    """Test that treat checkout retries without customer ID if Stripe customer is invalid."""
    import stripe

    invalid_err = stripe.error.InvalidRequestError("No such customer: 'cus_invalid'", param="customer")
    mock_session_create.side_effect = [
        invalid_err,
        MagicMock(url="http://test.url/treats", id="sess_treats_1"),
    ]
    treats_service.user_repo.update_user = AsyncMock(return_value=True)

    res = await treats_service.purchase_treats_checkout(
        user_id="00000000-0000-4000-a000-000000000123",
        package="small",
        price_id="price_small",
        success_url="http://success",
        cancel_url="http://cancel",
        stripe_customer_id="cus_invalid",
    )

    assert res["checkout_url"] == "http://test.url/treats"
    assert res["session_id"] == "sess_treats_1"
    treats_service.user_repo.update_user.assert_called_once_with(
        "00000000-0000-4000-a000-000000000123", {"stripe_customer_id": None}
    )
