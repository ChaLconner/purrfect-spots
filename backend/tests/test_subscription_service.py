from unittest.mock import MagicMock, patch

import pytest

from services.subscription_service import SubscriptionService


@pytest.fixture
def subscription_service():
    mock_supabase = MagicMock()
    return SubscriptionService(mock_supabase)

@patch("services.subscription_service.stripe.checkout.Session.create")
@patch("services.subscription_service.stripe.Customer.create")
async def test_create_checkout_session(mock_customer_create, mock_session_create, subscription_service):
    # Mock user query (no existing customer id)
    subscription_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
    
    mock_customer_create.return_value.id = "cus_test123"
    mock_session_create.return_value.url = "http://test.url"
    mock_session_create.return_value.id = "sess_123"

    res = await subscription_service.create_checkout_session(
        "user123", "test@test.com", "price_123", "success", "cancel"
    )

    assert res["checkout_url"] == "http://test.url"
    assert res["session_id"] == "sess_123"
    
    # Verify we updated the user with new customer ID
    subscription_service.supabase.table.return_value.update.assert_called()

@patch("services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_webhook_checkout_completed(mock_retrieve, subscription_service):
    # Mock event data
    session = {
        "metadata": {"user_id": "user123"},
        "subscription": "sub_123"
    }
    
    # Mock subscription retrieval
    mock_sub = MagicMock()
    mock_sub.current_period_end = 1700000000
    mock_retrieve.return_value = mock_sub
    
    await subscription_service._handle_checkout_session_completed(session)
    
    # Verify update called
    subscription_service.supabase.table.return_value.update.assert_called_with({
        "is_pro": True,
        "subscription_end_date": "2023-11-14T22:13:20+00:00" # depending on timezone, but checking structure
    })
