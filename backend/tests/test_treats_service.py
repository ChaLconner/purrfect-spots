from unittest.mock import AsyncMock, MagicMock

import pytest

from services.treats_service import TreatsService


@pytest.fixture
def treats_service():
    mock_supabase = MagicMock()
    service = TreatsService(mock_supabase)
    service.notification_service = MagicMock()
    service.notification_service.create_notification = AsyncMock()
    return service


async def test_give_treat_success_with_to_user_id(treats_service):
    """Test give_treat when RPC returns to_user_id (optimized path)."""
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = {"success": True, "new_balance": 90, "to_user_id": "owner123"}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc_result

    # Mock actor name query for notification
    mock_user_query = MagicMock()
    mock_user_query.data = {"name": "Test User"}
    treats_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query

    res = await treats_service.give_treat("giver123", "photo123", 10)

    assert res["success"] is True
    assert "10 treats" in res["message"]
    assert res["new_balance"] == 90

    # Verify RPC call
    treats_service.supabase.rpc.assert_called_with(
        "give_treat_atomic",
        {"p_from_user_id": "giver123", "p_photo_id": "photo123", "p_amount": 10},
    )


async def test_give_treat_success_fallback_notification(treats_service):
    """Test give_treat when RPC doesn't return to_user_id (fallback path)."""
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = {"success": True, "new_balance": 90}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc_result

    # Mock photo owner query (fallback path)
    mock_photo_query = MagicMock()
    mock_photo_query.data = {"user_id": "owner123"}

    mock_user_query = MagicMock()
    mock_user_query.data = {"name": "Test User"}

    def side_effect(table_name):
        mock_chain = MagicMock()
        if table_name == "cat_photos":
            mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_photo_query
        elif table_name == "users":
            mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query
        return mock_chain

    treats_service.supabase.table.side_effect = side_effect

    res = await treats_service.give_treat("giver123", "photo123", 10)

    assert res["success"] is True
    assert res["new_balance"] == 90


async def test_give_treat_failure(treats_service):
    """Test give_treat with insufficient balance."""
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = {"success": False, "error": "Insufficient treats"}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc_result

    with pytest.raises(ValueError, match="Insufficient treats"):
        await treats_service.give_treat("giver123", "photo123", 10)


async def test_get_balance(treats_service):
    """Test get_balance returns correct structure."""
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


async def test_fulfill_treat_purchase_idempotent(treats_service):
    """Test that duplicate purchase fulfillment is handled gracefully."""
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
