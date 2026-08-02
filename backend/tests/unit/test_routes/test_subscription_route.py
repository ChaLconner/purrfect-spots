from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from stripe import SignatureVerificationError

from app.config import config
from app.dependencies import get_subscription_service
from app.main import app
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.services.subscription_service import SubscriptionPersistenceError


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client using AsyncClient."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:  # NOSONAR python:S5332 - test base URL
        yield ac


class TestSubscriptionRoute:
    @pytest.fixture
    def mock_subscription_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_plans_returns_stripe_backed_prices(self, client, mock_subscription_service):
        mock_subscription_service.get_plan_prices = AsyncMock(
            return_value={
                "monthly": {
                    "plan": "monthly",
                    "unit_amount": 17500,
                    "currency": "thb",
                    "interval": "month",
                    "interval_count": 1,
                },
                "annual": {
                    "plan": "annual",
                    "unit_amount": 175000,
                    "currency": "thb",
                    "interval": "year",
                    "interval_count": 1,
                },
            }
        )
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        response = await client.get("/api/v1/subscription/plans")

        app.dependency_overrides = {}

        assert response.status_code == 200
        assert response.json()["monthly"]["unit_amount"] == 17500

    @pytest.mark.asyncio
    async def test_checkout_unconfigured_price(self, client, mock_user, mock_subscription_service):
        """Checkout should return 503 if price ID is missing."""
        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        with patch.object(config, "STRIPE_PRO_PRICE_ID", None):
            response = await client.post("/api/v1/subscription/checkout", json={"plan": "monthly"})

        app.dependency_overrides = {}

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_checkout_success(self, client, mock_user, mock_subscription_service):
        """Checkout should return 200 with checkout_url on success."""
        mock_subscription_service.create_checkout_session = AsyncMock(
            return_value={"checkout_url": "https://checkout.stripe.com/test", "session_id": "sess_123"}
        )

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        with patch.object(config, "STRIPE_PRO_PRICE_ID", "price_pro_monthly"):
            response = await client.post("/api/v1/subscription/checkout", json={"plan": "monthly"})

        app.dependency_overrides = {}

        assert response.status_code == 200
        assert response.json()["checkout_url"] == "https://checkout.stripe.com/test"

    @pytest.mark.asyncio
    async def test_checkout_preserves_http_exception(self, client, mock_user, mock_subscription_service):
        """Checkout route should preserve HTTPException status and detail from service."""
        mock_subscription_service.create_checkout_session = AsyncMock(
            side_effect=HTTPException(status_code=400, detail="Stripe error: Invalid API Key")
        )

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        with patch.object(config, "STRIPE_PRO_PRICE_ID", "price_pro_monthly"):
            response = await client.post("/api/v1/subscription/checkout", json={"plan": "monthly"})

        app.dependency_overrides = {}

        assert response.status_code == 400
        assert "Invalid API Key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_persistence_failure_returns_retryable_status(self, client, mock_subscription_service):
        mock_subscription_service.handle_webhook = AsyncMock(side_effect=SubscriptionPersistenceError("db down"))
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        response = await client.post(
            "/api/v1/subscription/webhook",
            content=b"{}",
            headers={"stripe-signature": "sig"},
        )

        app.dependency_overrides = {}

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_returns_bad_request(self, client, mock_subscription_service):
        mock_subscription_service.handle_webhook = AsyncMock(
            side_effect=SignatureVerificationError("bad signature", "sig_header")
        )
        app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service

        response = await client.post(
            "/api/v1/subscription/webhook",
            content=b"{}",
            headers={"stripe-signature": "sig"},
        )

        app.dependency_overrides = {}

        assert response.status_code == 400
