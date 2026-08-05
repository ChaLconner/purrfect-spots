import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.queue_service import QueueMessage, queue_service
from app.worker import QueueWorker


@pytest.mark.asyncio
async def test_worker_processes_verified_stripe_event() -> None:
    worker = QueueWorker()
    event = {
        "id": "evt_test_worker",
        "type": "invoice.paid",
        "created": 1,
        "data": {"object": {"id": "in_test_worker"}},
    }
    message = QueueMessage(
        stream=queue_service.STRIPE_STREAM,
        message_id="1-0",
        fields={"event": json.dumps(event)},
    )
    admin_client = object()

    with (
        patch("app.worker.get_async_supabase_admin_client", new=AsyncMock(return_value=admin_client)),
        patch("app.worker.SubscriptionService") as service_class,
    ):
        service = service_class.return_value
        service.handle_verified_webhook = AsyncMock()
        await worker._process_stripe(message)

    service_class.assert_called_once_with(admin_client)
    service.handle_verified_webhook.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_worker_processes_vision_job_and_removes_payload() -> None:
    worker = QueueWorker()
    message = QueueMessage(
        stream=queue_service.VISION_STREAM,
        message_id="2-0",
        fields={"job_id": "job-worker", "user_id": "user-worker", "operation": "spot-analysis"},
    )
    job = {
        "job_id": "job-worker",
        "user_id": "user-worker",
        "status": "queued",
        "attempts": 0,
        "filename": "spot.jpg",
        "analyzed_by": "user@example.com",
    }
    update_job = AsyncMock()

    with (
        patch.object(queue_service, "get_vision_job", new=AsyncMock(return_value=job)),
        patch.object(queue_service, "update_vision_job", new=update_job),
        patch.object(queue_service, "get_vision_payload", new=AsyncMock(return_value=b"image-bytes")),
        patch.object(queue_service, "delete_vision_payload", new=AsyncMock()) as delete_payload,
        patch("app.worker.cat_detection_service") as detection_service,
    ):
        detection_service.analyze_cat_spot_suitability = AsyncMock(
            return_value={"suitability_score": 90, "suitable_for_cat_spot": True}
        )
        await worker._process_vision(message)

    assert update_job.await_count == 2
    assert update_job.await_args_list[0].kwargs == {"status": "processing", "attempts": 1, "error": None}
    completed = update_job.await_args_list[1].kwargs
    assert completed["status"] == "completed"
    assert completed["attempts"] == 1
    assert completed["result"]["filename"] == "spot.jpg"
    delete_payload.assert_awaited_once_with("job-worker")


@pytest.mark.asyncio
async def test_worker_keeps_failed_job_pending_for_retry() -> None:
    worker = QueueWorker()
    message = QueueMessage(
        stream=queue_service.VISION_STREAM,
        message_id="3-0",
        fields={"job_id": "job-retry", "user_id": "user-worker", "operation": "spot-analysis"},
    )
    update_job = AsyncMock()
    acknowledge = AsyncMock()

    with (
        patch.object(worker, "_process_vision", new=AsyncMock(side_effect=RuntimeError("Vision unavailable"))),
        patch.object(queue_service, "increment_attempt", new=AsyncMock(return_value=1)),
        patch.object(queue_service, "update_vision_job", new=update_job),
        patch.object(queue_service, "acknowledge", new=acknowledge),
    ):
        await worker._process_with_retry(message, queue_service.VISION_GROUP)

    update_job.assert_awaited_once_with("job-retry", status="queued", attempts=1)
    acknowledge.assert_not_awaited()
