from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.subscription_service import SubscriptionService


@pytest.fixture
def subscription_service():
    from unittest.mock import AsyncMock

    mock_supabase = MagicMock()
    # Mock chain: .table().select().eq().maybe_single().execute()
    builder = MagicMock()
    mock_supabase.table.return_value = builder
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.single.return_value = builder
    builder.maybe_single.return_value = builder
    builder.update.return_value = builder
    builder.match.return_value = builder
    builder.execute = AsyncMock()

    return SubscriptionService(mock_supabase)


@patch("services.subscription_service.stripe.checkout.Session.create")
@patch("services.subscription_service.stripe.Customer.create")
async def test_create_checkout_session(mock_customer_create, mock_session_create, subscription_service):
    """Test checkout session creation with new customer."""
    # Mock user query (no existing customer id)
    subscription_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=None
    )

    mock_customer_create.return_value.id = "cus_test123"
    mock_session_create.return_value.url = "http://test.url"
    mock_session_create.return_value.id = "sess_123"

    res = await subscription_service.create_checkout_session(
        "00000000-0000-4000-a000-000000000123", "test@test.com", "price_123", "success", "cancel"
    )

    assert res["checkout_url"] == "http://test.url"
    assert res["session_id"] == "sess_123"


@patch("services.subscription_service.stripe.checkout.Session.create")
async def test_create_checkout_session_with_existing_customer(mock_session_create, subscription_service):
    """Test checkout when user already has a Stripe customer ID."""
    mock_session_create.return_value.url = "http://test.url"
    mock_session_create.return_value.id = "sess_456"

    res = await subscription_service.create_checkout_session(
        "00000000-0000-4000-a000-000000000123",
        "test@test.com",
        "price_123",
        "success",
        "cancel",
        stripe_customer_id="cus_existing",
    )

    assert res["checkout_url"] == "http://test.url"
    assert res["session_id"] == "sess_456"


@patch("services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_webhook_checkout_completed(mock_retrieve, subscription_service):
    """Test subscription activation via webhook."""
    session = {"metadata": {"user_id": "00000000-0000-4000-a000-000000000123"}, "subscription": "sub_123"}

    mock_sub = MagicMock()
    mock_sub.current_period_end = 1700000000
    mock_sub.cancel_at_period_end = False
    mock_retrieve.return_value = mock_sub

    await subscription_service._handle_checkout_session_completed(session)

    # Verify update was called
    subscription_service.supabase.table.return_value.update.assert_called()


@patch("services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_subscription_updated(mock_retrieve, subscription_service):
    """Test subscription update sync."""
    subscription = {
        "customer": "cus_123",
        "cancel_at_period_end": True,
        "current_period_end": 1700000000,
    }

    await subscription_service._handle_subscription_updated(subscription)

    subscription_service.supabase.table.return_value.update.assert_called()


async def test_handle_subscription_updated_missing_period_end(subscription_service):
    """Test that missing current_period_end is handled gracefully."""
    subscription = {"customer": "cus_123", "cancel_at_period_end": False}

    # Should not raise
    await subscription_service._handle_subscription_updated(subscription)


async def test_handle_subscription_deleted(subscription_service):
    """Test subscription deletion clears pro status."""
    subscription = {"customer": "cus_456"}

    await subscription_service._handle_subscription_deleted(subscription)

    subscription_service.supabase.table.return_value.update.assert_called_with(
        {"is_pro": False, "subscription_end_date": None, "cancel_at_period_end": False}
    )


async def test_dispatch_checkout_completed_payment(subscription_service):
    """Test that payment mode dispatches to treats fulfillment."""
    session = {
        "mode": "payment",
        "metadata": {"user_id": "00000000-0000-4000-a000-000000000123", "type": "treat_purchase", "package": "small"},
        "id": "sess_pay_1",
    }

    # Mock treats service fulfill
    subscription_service.treats_service.fulfill_treat_purchase = AsyncMock()

    await subscription_service._dispatch_checkout_completed(session)

    subscription_service.treats_service.fulfill_treat_purchase.assert_called_once_with(session)
