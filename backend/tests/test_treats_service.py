
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.treats_service import TreatsService

@pytest.fixture
def treats_service():
    mock_supabase = MagicMock()
    service = TreatsService(mock_supabase)
    service.notification_service = MagicMock()
    service.notification_service.create_notification = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_give_treat_success_with_to_user_id(treats_service):
    """Test give_treat when RPC returns to_user_id (optimized path)."""
    with patch("utils.async_client.async_supabase") as mock_async, \
         patch("services.treats_service.run_in_threadpool") as mock_run_in_threadpool: # Mock threadpool if used for other calls
        
        # Configure RPC return
        mock_async.rpc = AsyncMock(return_value=[{"success": True, "new_balance": 90, "to_user_id": "owner123"}])
        
        # Mock actor name query (still uses run_in_threadpool + sync client in _send_treat_notification)
        # We need to mock the sync client for the notification part
        mock_user_query = MagicMock()
        mock_user_query.data = {"name": "Test User"}
        treats_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query
        
        # Mock run_in_threadpool to execute the lambda passed to it
        # Note: _send_treat_notification calls run_in_threadpool(lambda: ...)
        async def side_effect(func):
            return func()
        mock_run_in_threadpool.side_effect = side_effect

        res = await treats_service.give_treat("giver123", "photo123", 10, jwt_token="token")

        assert res["success"] is True
        assert res["new_balance"] == 90
        
        mock_async.rpc.assert_called_with(
            "give_treat_atomic",
            {"p_from_user_id": "giver123", "p_photo_id": "photo123", "p_amount": 10},
            jwt_token="token"
        )

@pytest.mark.asyncio
async def test_give_treat_success_fallback_notification(treats_service):
    """Test give_treat when RPC doesn't return to_user_id (fallback path)."""
    with patch("utils.async_client.async_supabase") as mock_async, \
         patch("services.treats_service.run_in_threadpool") as mock_run_in_threadpool:
        
        mock_async.rpc = AsyncMock(return_value=[{"success": True, "new_balance": 90}])
        
        # Mock chain for fallback queries (sync client)
        mock_photo_query = MagicMock()
        mock_photo_query.data = {"user_id": "owner123"}
        
        mock_user_query = MagicMock()
        mock_user_query.data = {"name": "Test User"}
        
        def table_side_effect(table_name):
            mock_chain = MagicMock()
            if table_name == "cat_photos":
                mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_photo_query
            elif table_name == "users":
                mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query
            return mock_chain
            
        treats_service.supabase.table.side_effect = table_side_effect
        
        # Mock run_in_threadpool to execute
        async def side_effect(func):
            return func()
        mock_run_in_threadpool.side_effect = side_effect
        
        res = await treats_service.give_treat("giver123", "photo123", 10, jwt_token="token")
        
        assert res["success"] is True

@pytest.mark.asyncio
async def test_give_treat_failure(treats_service):
    """Test give_treat with insufficient balance."""
    with patch("utils.async_client.async_supabase") as mock_async:
        mock_async.rpc = AsyncMock(return_value=[{"success": False, "error": "Insufficient treats"}])
        
        with pytest.raises(ValueError, match="Insufficient treats"):
            await treats_service.give_treat("giver123", "photo123", 10)

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
        if table_name == "users":
            mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user
        elif table_name == "treats_transactions":
            mock_chain.select.return_value.or_.return_value.order.return_value.limit.return_value.execute.return_value = mock_trans
        return mock_chain

    treats_service.supabase.table.side_effect = side_effect

    res = await treats_service.get_balance("user123")
    assert res["balance"] == 42
    assert len(res["recent_transactions"]) == 1

@pytest.mark.asyncio
async def test_fulfill_treat_purchase_idempotent(treats_service):
    """Test that duplicate purchase fulfillment is handled gracefully."""
    # This also uses run_in_threadpool + sync client
    session = {
        "metadata": {"user_id": "user123", "package": "small"},
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
