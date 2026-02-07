from unittest.mock import MagicMock
import pytest
from services.treats_service import TreatsService

@pytest.fixture
def treats_service():
    mock_supabase = MagicMock()
    return TreatsService(mock_supabase)

async def test_give_treat_success(treats_service):
    # Setup mocks
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = {"success": True, "new_balance": 90}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc_result
    
    # Mock photo owner retrieval for notification
    mock_photo_query = MagicMock()
    mock_photo_query.data = {"user_id": "owner123"}
    
    # Mock user name query for notification
    mock_user_query = MagicMock()
    mock_user_query.data = {"name": "Test User"}

    def side_effect(table_name):
        mock_chain = MagicMock()
        if table_name == "cat_photos":
            mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_photo_query
        elif table_name == "users":
             mock_chain.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_query
        elif table_name == "notifications":
             mock_chain.insert.return_value.execute.return_value = MagicMock()
        return mock_chain

    treats_service.supabase.table.side_effect = side_effect

    # Execute
    res = await treats_service.give_treat("giver123", "photo123", 10)

    assert res["success"] is True
    assert "10 treats" in res["message"]
    
    # Verify RPC call
    treats_service.supabase.rpc.assert_called_with(
        "give_treat_atomic", 
        {"p_from_user_id": "giver123", "p_photo_id": "photo123", "p_amount": 10}
    )

async def test_give_treat_failure(treats_service):
    # Setup mock for failure
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = {"success": False, "error": "Insufficient treats"}
    treats_service.supabase.rpc.return_value.execute.return_value = mock_rpc_result

    with pytest.raises(ValueError, match="Insufficient treats"):
        await treats_service.give_treat("giver123", "photo123", 10)
