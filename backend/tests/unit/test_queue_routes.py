import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.config import config
from app.dependencies import get_cat_detection_service, get_subscription_service
from app.main import app
from app.middleware.auth_middleware import get_current_user
from app.services.queue_service import QueueUnavailable


def valid_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="white").save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_stripe_webhook_is_accepted_only_after_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    subscription_service = MagicMock()
    subscription_service.construct_webhook_event.return_value = {
        "id": "evt_test_1",
        "type": "invoice.paid",
        "created": 1,
        "data": {"object": {}},
    }
    monkeypatch.setitem(app.dependency_overrides, get_subscription_service, lambda: subscription_service)
    with (
        patch.object(config, "ENABLE_STRIPE_WEBHOOK_QUEUE", True),
        patch("app.routes.subscription.queue_service.enqueue_stripe_webhook", new=AsyncMock(return_value="1-0")),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/subscription/webhook",
                content=b"signed-payload",
                headers={"stripe-signature": "sig"},
            )

    assert response.status_code == 200
    assert response.json() == {"message": "accepted", "status": None}
    subscription_service.handle_webhook.assert_not_called()


@pytest.mark.asyncio
async def test_stripe_webhook_returns_retryable_status_when_queue_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subscription_service = MagicMock()
    subscription_service.construct_webhook_event.return_value = {
        "id": "evt_test_2",
        "type": "invoice.paid",
        "created": 1,
        "data": {"object": {}},
    }
    monkeypatch.setitem(app.dependency_overrides, get_subscription_service, lambda: subscription_service)
    with (
        patch.object(config, "ENABLE_STRIPE_WEBHOOK_QUEUE", True),
        patch(
            "app.routes.subscription.queue_service.enqueue_stripe_webhook",
            new=AsyncMock(side_effect=QueueUnavailable("redis down")),
        ),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/subscription/webhook",
                content=b"signed-payload",
                headers={"stripe-signature": "sig"},
            )

    assert response.status_code == 503
    subscription_service.handle_webhook.assert_not_called()


@pytest.mark.asyncio
async def test_vision_analysis_returns_accepted_job_without_calling_vision(monkeypatch: pytest.MonkeyPatch) -> None:
    user = MagicMock(id="user-1", email="user@example.com")
    detection_service = MagicMock()
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: user)
    monkeypatch.setitem(app.dependency_overrides, get_cat_detection_service, lambda: detection_service)
    with (
        patch.object(config, "ENABLE_VISION_ANALYSIS_QUEUE", True),
        patch(
            "app.routes.cat_detection.queue_service.enqueue_vision_job",
            new=AsyncMock(
                return_value={
                    "job_id": "job-1",
                    "operation": "spot-analysis",
                    "created_at": "2026-08-04T00:00:00+00:00",
                }
            ),
        ),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/detect/spot-analysis",
                files={"file": ("spot.jpg", valid_jpeg(), "image/jpeg")},
            )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-1"
    detection_service.analyze_cat_spot_suitability.assert_not_called()
