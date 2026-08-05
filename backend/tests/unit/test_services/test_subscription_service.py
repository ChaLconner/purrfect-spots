from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.config import config
from app.services.subscription_service import (
    SubscriptionPersistenceError,
    SubscriptionService,
    cancel_customer_subscriptions,
)


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


@patch("app.services.subscription_service.stripe.Subscription.list")
@patch("app.services.subscription_service.stripe.checkout.Session.create")
@patch("app.services.subscription_service.stripe.Customer.create")
async def test_create_checkout_session(
    mock_customer_create, mock_session_create, mock_subscription_list, subscription_service
):
    """Test checkout session creation with new customer."""
    # Mock user query (no existing customer id)
    subscription_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=None
    )

    mock_customer_create.return_value.id = "cus_test123"
    mock_subscription_list.return_value = MagicMock(data=[])
    mock_session_create.return_value.url = "http://test.url"  # NOSONAR python:S5332 - test fixture URL
    mock_session_create.return_value.id = "sess_123"
    subscription_service._update_user_data = AsyncMock(return_value={"id": "00000000-0000-4000-a000-000000000123"})

    res = await subscription_service.create_checkout_session(
        "00000000-0000-4000-a000-000000000123", "test@test.com", "price_123", "success", "cancel"
    )

    assert res["checkout_url"] == "http://test.url"  # NOSONAR python:S5332 - test fixture URL assertion
    assert res["session_id"] == "sess_123"


@patch("app.services.subscription_service.stripe.Subscription.list")
@patch("app.services.subscription_service.stripe.checkout.Session.create")
async def test_create_checkout_session_with_existing_customer(
    mock_session_create, mock_subscription_list, subscription_service
):
    """Test checkout when user already has a Stripe customer ID."""
    mock_session_create.return_value.url = "http://test.url"  # NOSONAR python:S5332 - test fixture URL
    mock_session_create.return_value.id = "sess_456"
    mock_subscription_list.return_value = MagicMock(data=[])

    res = await subscription_service.create_checkout_session(
        "00000000-0000-4000-a000-000000000123",
        "test@test.com",
        "price_123",
        "success",
        "cancel",
        stripe_customer_id="cus_existing",
    )

    assert res["checkout_url"] == "http://test.url"  # NOSONAR python:S5332 - test fixture URL assertion
    assert res["session_id"] == "sess_456"


@patch("app.services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_webhook_checkout_completed(mock_retrieve, subscription_service):
    """Test subscription activation via webhook."""
    session = {"metadata": {"user_id": "00000000-0000-4000-a000-000000000123"}, "subscription": "sub_123"}

    mock_sub = MagicMock()
    mock_sub.status = "active"
    mock_sub.current_period_end = 1700000000
    mock_sub.cancel_at_period_end = False
    mock_sub.items = {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]}
    mock_retrieve.return_value = mock_sub

    await subscription_service._handle_checkout_session_completed(session)

    # Verify update was called
    subscription_service.supabase.table.return_value.update.assert_called()


@patch("app.services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_webhook_checkout_completed_ignores_unexpected_price(mock_retrieve, subscription_service):
    """Test subscription activation is rejected for unknown Stripe prices."""
    session = {"metadata": {"user_id": "00000000-0000-4000-a000-000000000123"}, "subscription": "sub_123"}

    mock_sub = MagicMock()
    mock_sub.status = "active"
    mock_sub.current_period_end = 1700000000
    mock_sub.cancel_at_period_end = False
    mock_sub.items = {"data": [{"price": {"id": "price_unexpected"}}]}
    mock_retrieve.return_value = mock_sub

    await subscription_service._handle_checkout_session_completed(session)

    subscription_service.supabase.table.return_value.update.assert_not_called()


@patch("app.services.subscription_service.stripe.Subscription.retrieve")
async def test_handle_subscription_updated(mock_retrieve, subscription_service):
    """Test subscription update sync."""
    subscription = {
        "id": "sub_123",
        "customer": "cus_123",
        "status": "active",
        "cancel_at_period_end": True,
        "current_period_end": 1700000000,
        "items": {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]},
    }

    await subscription_service._handle_subscription_updated(subscription)

    subscription_service.supabase.table.return_value.update.assert_called()


async def test_handle_subscription_updated_missing_period_end(subscription_service):
    """Test that missing current_period_end is handled gracefully."""
    subscription = {
        "id": "sub_123",
        "customer": "cus_123",
        "status": "active",
        "cancel_at_period_end": False,
        "items": {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]},
    }

    # Should not raise
    await subscription_service._handle_subscription_updated(subscription)


async def test_ordered_snapshot_rejects_active_subscription_without_period_end(subscription_service):
    subscription_service.supabase.rpc.return_value.execute = AsyncMock()

    applied = await subscription_service._apply_subscription_snapshot(
        {
            "id": "sub_missing_period",
            "customer": "cus_123",
            "status": "active",
            "items": {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]},
        },
        user_id="user_123",
        event_id="evt_missing_period",
        event_created_at=datetime.now(UTC),
    )

    assert applied is False
    subscription_service.supabase.rpc.assert_not_called()


async def test_webhook_requires_configured_secret(subscription_service):
    import os

    with (
        patch.object(config, "STRIPE_WEBHOOK_SECRET", None),
        patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": ""}),
        pytest.raises(SubscriptionPersistenceError, match="webhook secret"),
    ):
        await subscription_service.handle_webhook(b"{}", "sig")


async def test_handle_subscription_deleted(subscription_service):
    """Test subscription deletion clears pro status."""
    subscription = {
        "id": "sub_456",
        "customer": "cus_456",
        "status": "canceled",
        "items": {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]},
    }

    await subscription_service._handle_subscription_deleted(subscription)

    subscription_service.supabase.table.return_value.update.assert_called_with(
        {"is_pro": False, "subscription_end_date": None, "cancel_at_period_end": False}
    )


async def test_dispatch_checkout_completed_payment(subscription_service):
    """Test that payment mode dispatches to treats fulfillment."""
    session = {
        "mode": "payment",
        "payment_status": "paid",
        "metadata": {"user_id": "00000000-0000-4000-a000-000000000123", "type": "treat_purchase", "package": "small"},
        "id": "sess_pay_1",
    }

    # Mock treats service fulfill
    subscription_service.treats_service.fulfill_treat_purchase = AsyncMock()

    await subscription_service._dispatch_checkout_completed(session)

    subscription_service.treats_service.fulfill_treat_purchase.assert_called_once_with(session)


async def test_dispatch_checkout_completed_payment_requires_paid_status(subscription_service):
    session = {
        "mode": "payment",
        "payment_status": "unpaid",
        "metadata": {"type": "treat_purchase", "package": "small"},
        "id": "sess_unpaid",
    }
    subscription_service.treats_service.fulfill_treat_purchase = AsyncMock()

    await subscription_service._dispatch_checkout_completed(session)

    subscription_service.treats_service.fulfill_treat_purchase.assert_not_awaited()


@patch("app.services.subscription_service.stripe.billing_portal.Session.create")
async def test_create_portal_session_sanitizes_external_return_url(mock_portal_create, subscription_service):
    """Test portal sessions always return to the configured frontend."""
    subscription_service._get_user_data = AsyncMock(return_value={"stripe_customer_id": "cus_123"})
    mock_portal_create.return_value.url = "https://stripe.com/portal"

    await subscription_service.create_portal_session(
        "00000000-0000-4000-a000-000000000123",
        "https://evil.example/phish",
    )

    mock_portal_create.assert_called_once()
    assert mock_portal_create.call_args.kwargs["return_url"] == config.resolve_frontend_url(
        default_path="/subscription"
    )


@patch("app.services.subscription_service.stripe.Subscription.list")
@patch("app.services.subscription_service.stripe.checkout.Session.create")
@patch("app.services.subscription_service.stripe.Customer.create")
async def test_create_checkout_session_recreates_customer_on_invalid_customer_error(
    mock_customer_create, mock_session_create, mock_subscription_list, subscription_service
):
    """Test that checkout session creation retries with a new customer if customer ID is invalid."""
    import stripe

    invalid_err = stripe.error.InvalidRequestError("No such customer: 'cus_invalid'", param="customer")
    mock_session_create.side_effect = [
        invalid_err,
        MagicMock(url="http://test.url/success", id="sess_retry"),
    ]
    mock_customer_create.return_value.id = "cus_new_123"
    mock_subscription_list.return_value = MagicMock(data=[])
    subscription_service._update_user_data = AsyncMock(return_value={"id": "00000000-0000-4000-a000-000000000123"})

    res = await subscription_service.create_checkout_session(
        "00000000-0000-4000-a000-000000000123",
        "test@test.com",
        "price_123",
        "success",
        "cancel",
        stripe_customer_id="cus_invalid",
    )

    assert res["checkout_url"] == "http://test.url/success"
    assert res["session_id"] == "sess_retry"
    mock_customer_create.assert_called_once()


async def test_subscription_updated_rejects_unexpected_price(subscription_service):
    subscription_service._update_user_data = AsyncMock()

    await subscription_service._handle_subscription_updated(
        {
            "id": "sub_unexpected",
            "customer": "cus_123",
            "status": "active",
            "current_period_end": 1700000000,
            "items": {"data": [{"price": {"id": "price_unexpected"}}]},
        }
    )

    subscription_service._update_user_data.assert_not_called()


async def test_billing_write_failure_is_not_acknowledged(subscription_service):
    subscription_service.user_repo.get_user_strict = AsyncMock(return_value={"id": "user_123"})
    subscription_service.user_repo.update_user_strict = AsyncMock(return_value=False)

    with pytest.raises(SubscriptionPersistenceError):
        await subscription_service._update_user_data({"is_pro": True}, {"id": "user_123"})


@patch("app.services.subscription_service.stripe.Subscription.list")
@patch("app.services.subscription_service.stripe.checkout.Session.create")
async def test_checkout_rejects_existing_live_subscription(
    mock_session_create, mock_subscription_list, subscription_service
):
    mock_subscription_list.return_value = MagicMock(data=[MagicMock(status="trialing", id="sub_trial")])

    with pytest.raises(HTTPException) as exc_info:
        await subscription_service.create_checkout_session(
            "user_123", "test@test.com", "price_123", "success", "cancel", stripe_customer_id="cus_existing"
        )

    assert exc_info.value.status_code == 409
    mock_session_create.assert_not_called()


@patch("app.services.subscription_service.stripe.Subscription.list")
@patch("app.services.subscription_service.stripe.Subscription.modify")
async def test_cancel_subscription_includes_trialing(mock_modify, mock_list, subscription_service):
    subscription_service._get_user_data = AsyncMock(return_value={"stripe_customer_id": "cus_existing"})
    mock_list.return_value = MagicMock(data=[MagicMock(status="trialing", id="sub_trial")])

    await subscription_service.cancel_subscription("user_123")

    mock_modify.assert_called_once_with("sub_trial", cancel_at_period_end=True)


@patch("app.services.subscription_service.stripe.Subscription.modify")
@patch("app.services.subscription_service.stripe.Subscription.list")
async def test_cancel_customer_subscriptions_paginates_all_results(mock_list, mock_modify):
    page_one = [MagicMock(status="active", id="sub_1")]
    page_two = [MagicMock(status="trialing", id="sub_101")]
    collection = MagicMock(data=page_one)
    collection.auto_paging_iter.return_value = iter(page_one + page_two)
    mock_list.return_value = collection

    canceled = await cancel_customer_subscriptions("cus_existing")

    assert canceled == 2
    assert [call.args[0] for call in mock_modify.call_args_list] == ["sub_1", "sub_101"]


@patch("app.services.subscription_service.stripe.Price.retrieve")
async def test_get_plan_prices_reads_current_stripe_amounts(mock_retrieve, subscription_service):
    SubscriptionService._plan_price_cache = None
    with (
        patch.object(config, "STRIPE_PRO_PRICE_ID", "price_monthly"),
        patch.object(config, "STRIPE_PRO_ANNUAL_PRICE_ID", "price_annual"),
    ):

        def retrieve_price(price_id: str) -> dict[str, object]:
            if price_id == "price_monthly":
                return {
                    "active": True,
                    "currency": "thb",
                    "unit_amount": 17500,
                    "recurring": {"interval": "month", "interval_count": 1},
                }
            return {
                "active": True,
                "currency": "thb",
                "unit_amount": 175000,
                "recurring": {"interval": "year", "interval_count": 1},
            }

        mock_retrieve.side_effect = retrieve_price

        plans = await subscription_service.get_plan_prices()

    assert plans["monthly"]["unit_amount"] == 17500
    assert plans["annual"]["unit_amount"] == 175000
    assert mock_retrieve.call_count == 2


async def test_reconcile_all_subscriptions_scans_users_and_is_idempotent(subscription_service):
    subscription_service._list_billing_users = AsyncMock(return_value=[{"id": "user_1", "stripe_customer_id": "cus_1"}])
    subscription_service._reconcile_customer = AsyncMock(return_value=1)

    summary = await subscription_service.reconcile_all_subscriptions()

    assert summary == {
        "customers_scanned": 1,
        "subscriptions_reconciled": 1,
        "failed_customers": 0,
        "skipped": 0,
    }
    subscription_service._reconcile_customer.assert_awaited_once()


@patch("app.services.subscription_service.stripe.Subscription.retrieve")
async def test_invoice_paid_retrieval_failure_is_retryable(mock_retrieve, subscription_service):
    mock_retrieve.side_effect = RuntimeError("Stripe unavailable")

    with pytest.raises(SubscriptionPersistenceError):
        await subscription_service._handle_invoice_paid({"customer": "cus_123", "subscription": "sub_123"})


@patch("app.services.subscription_service.stripe.Webhook.construct_event")
async def test_webhook_duplicate_is_skipped(mock_construct_event, subscription_service):
    mock_construct_event.return_value = {
        "id": "evt_duplicate",
        "type": "customer.subscription.updated",
        "created": 1700000000,
        "data": {"object": {"id": "sub_123", "customer": "cus_123"}},
    }
    rpc_execute = AsyncMock(return_value=MagicMock(data={"claimed": False}))
    subscription_service.supabase.rpc.return_value.execute = rpc_execute
    subscription_service._handle_subscription_updated = AsyncMock()

    await subscription_service.handle_webhook(b"{}", "sig")

    subscription_service._handle_subscription_updated.assert_not_called()
    rpc_execute.assert_awaited_once()


@patch("app.services.subscription_service.stripe.Webhook.construct_event")
async def test_webhook_failure_is_recorded_and_raised_for_retry(mock_construct_event, subscription_service):
    mock_construct_event.return_value = {
        "id": "evt_failed",
        "type": "customer.subscription.updated",
        "created": 1700000000,
        "data": {"object": {"id": "sub_123", "customer": "cus_123"}},
    }
    rpc_execute = AsyncMock(
        side_effect=[
            MagicMock(data={"claimed": True}),
            MagicMock(data={"failed": True}),
        ]
    )
    subscription_service.supabase.rpc.return_value.execute = rpc_execute
    subscription_service._handle_subscription_updated = AsyncMock(side_effect=SubscriptionPersistenceError("db down"))

    with pytest.raises(SubscriptionPersistenceError):
        await subscription_service.handle_webhook(b"{}", "sig")

    assert rpc_execute.await_count == 2
    assert subscription_service.supabase.rpc.call_args_list[1].args[0] == "fail_stripe_webhook_event"


async def test_ordered_snapshot_ignores_stale_event(subscription_service):
    rpc_execute = AsyncMock(
        side_effect=[
            MagicMock(data={"applied": True, "user_found": True}),
            MagicMock(data={"applied": False, "user_found": True}),
        ]
    )
    subscription_service.supabase.rpc.return_value.execute = rpc_execute
    subscription = {
        "id": "sub_123",
        "customer": "cus_123",
        "status": "active",
        "current_period_end": 1700000000,
        "items": {"data": [{"price": {"id": config.STRIPE_PRO_PRICE_ID}}]},
    }

    assert (
        await subscription_service._handle_subscription_updated(
            subscription, "evt_new", datetime.fromtimestamp(1700000002, UTC)
        )
        is None
    )
    assert (
        await subscription_service._handle_subscription_updated(
            {**subscription, "status": "canceled"}, "evt_old", datetime.fromtimestamp(1700000001, UTC)
        )
        is None
    )
    assert rpc_execute.await_count == 2
