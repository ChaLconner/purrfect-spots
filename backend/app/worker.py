"""Long-lived worker for Redis-backed Stripe and Google Vision jobs."""

from __future__ import annotations

import asyncio
import json
import os
import socket
from typing import Any
from uuid import uuid4

from app.config import config
from app.logger import logger
from app.services.cat_detection_service import cat_detection_service
from app.services.queue_service import QueueMessage, QueuePayloadMissing, queue_service
from app.services.subscription_service import SubscriptionService
from app.utils.supabase_client import get_async_supabase_admin_client


class PermanentJobError(RuntimeError):
    """Raised when retrying cannot recover a queue entry."""


class QueueWorker:
    """Process each stream with consumer-group delivery and stale-claim recovery."""

    def __init__(self) -> None:
        hostname = socket.gethostname().replace(" ", "-")[:40]
        self.consumer = os.getenv("QUEUE_CONSUMER_NAME", f"{hostname}-{uuid4().hex[:10]}")

    async def run_forever(self) -> None:
        if not queue_service.available:
            raise RuntimeError("QUEUE_REDIS_URL or REDIS_URL is required for the worker")

        await queue_service.ensure_groups()
        await asyncio.gather(
            self._run_stream(queue_service.STRIPE_STREAM, queue_service.STRIPE_GROUP),
            self._run_stream(queue_service.VISION_STREAM, queue_service.VISION_GROUP),
        )

    async def _run_stream(self, stream: str, group: str) -> None:
        while True:
            try:
                stale_messages = await queue_service.claim_stale(
                    stream=stream,
                    group=group,
                    consumer=self.consumer,
                )
                for message in stale_messages:
                    await self._process_with_retry(message, group)

                messages = await queue_service.read_group(
                    stream=stream,
                    group=group,
                    consumer=self.consumer,
                )
                for message in messages:
                    await self._process_with_retry(message, group)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("Queue Redis temporarily unavailable for %s", stream, exc_info=True)
                await asyncio.sleep(5)

    async def _process_with_retry(self, message: QueueMessage, group: str) -> None:
        try:
            await self._dispatch_message(message)
        except Exception as exc:
            await self._handle_processing_failure(message, group, exc)
            return

        await queue_service.clear_attempt(message)
        await queue_service.acknowledge(message, group)

    async def _dispatch_message(self, message: QueueMessage) -> None:
        if message.stream == queue_service.STRIPE_STREAM:
            await self._process_stripe(message)
        elif message.stream == queue_service.VISION_STREAM:
            await self._process_vision(message)
        else:
            raise PermanentJobError(f"Unsupported queue stream {message.stream}")

    async def _handle_processing_failure(self, message: QueueMessage, group: str, error: Exception) -> None:
        try:
            attempts = await queue_service.increment_attempt(message)
        except Exception:
            logger.error("Queue acknowledgement state is temporarily unavailable", exc_info=True)
            return

        if self._should_dead_letter(error, attempts):
            await self._mark_vision_job_failed(message, error, attempts)
            await self._move_to_dead_letter(message, group, error)
            return

        await self._mark_vision_job_for_retry(message, attempts)
        logger.warning(
            "Queue job failed; leaving it pending for stale-claim retry (%s/%s): %s",
            attempts,
            config.QUEUE_MAX_ATTEMPTS,
            message.message_id,
            exc_info=True,
        )

    @staticmethod
    def _should_dead_letter(error: Exception, attempts: int) -> bool:
        return isinstance(error, (PermanentJobError, QueuePayloadMissing)) or attempts >= config.QUEUE_MAX_ATTEMPTS

    async def _mark_vision_job_failed(self, message: QueueMessage, error: Exception, attempts: int) -> None:
        job_id = self._vision_job_id(message)
        if not job_id:
            return
        await queue_service.update_vision_job(
            job_id,
            status="failed",
            error=self._safe_error(error),
            attempts=attempts,
        )
        await queue_service.delete_vision_payload(job_id)

    async def _mark_vision_job_for_retry(self, message: QueueMessage, attempts: int) -> None:
        job_id = self._vision_job_id(message)
        if job_id:
            await queue_service.update_vision_job(job_id, status="queued", attempts=attempts)

    @staticmethod
    def _vision_job_id(message: QueueMessage) -> str:
        if message.stream != queue_service.VISION_STREAM:
            return ""
        return message.fields.get("job_id", "")

    async def _move_to_dead_letter(self, message: QueueMessage, group: str, error: Exception) -> None:
        try:
            await queue_service.dead_letter(message, group, self._safe_error(error))
            await queue_service.clear_attempt(message)
            logger.error("Queue job moved to dead-letter stream: %s", message.message_id, exc_info=True)
        except Exception:
            # Keep the source entry pending if the dead-letter write is
            # unavailable; the worker must not acknowledge data it could not preserve.
            logger.error("Could not persist queue dead-letter entry: %s", message.message_id, exc_info=True)

    async def _process_stripe(self, message: QueueMessage) -> None:
        raw_event = message.fields.get("event")
        if not raw_event:
            raise PermanentJobError("Stripe queue entry has no event payload")
        try:
            event = json.loads(raw_event)
        except json.JSONDecodeError as exc:
            raise PermanentJobError("Stripe queue entry has invalid JSON") from exc
        if not isinstance(event, dict):
            raise PermanentJobError("Stripe queue entry is not an object")

        admin_client = await get_async_supabase_admin_client()
        await SubscriptionService(admin_client).handle_verified_webhook(event)

    async def _process_vision(self, message: QueueMessage) -> None:
        job_id = message.fields.get("job_id", "")
        user_id = message.fields.get("user_id", "")
        operation = message.fields.get("operation", "")
        if not job_id or not user_id or operation not in {"spot-analysis", "combined"}:
            raise PermanentJobError("Vision queue entry is incomplete")

        job = await queue_service.get_vision_job(job_id, user_id)
        if not job:
            raise QueuePayloadMissing(f"Vision job {job_id} is missing")
        if job.get("status") == "completed":
            return

        attempts = int(job.get("attempts") or 0) + 1
        await queue_service.update_vision_job(job_id, status="processing", attempts=attempts, error=None)
        contents = await queue_service.get_vision_payload(job_id)
        filename = str(job.get("filename") or "uploaded-image")
        analyzed_by = str(job.get("analyzed_by") or "")

        if operation == "spot-analysis":
            result: dict[str, Any] = await cat_detection_service.analyze_cat_spot_suitability(contents)
            result.update({"filename": filename, "analyzed_by": analyzed_by})
        else:
            cat_detection = await cat_detection_service.detect_cats(contents)
            spot_analysis = await cat_detection_service.analyze_cat_spot_suitability(contents)
            result = {
                "cat_detection": cat_detection,
                "spot_analysis": spot_analysis,
                "overall_recommendation": {
                    "suitable_for_cat_spot": cat_detection.get("suitable_for_cat_spot", False),
                    "confidence": (cat_detection.get("confidence", 0) + spot_analysis.get("suitability_score", 0)) / 2,
                    "summary": (
                        f"Found cats: {cat_detection.get('cat_count', 0)}, "
                        f"Suitability score: {spot_analysis.get('suitability_score', 0)}/100"
                    ),
                },
                "metadata": {
                    "filename": filename,
                    "file_size": len(contents),
                    "analyzed_by": analyzed_by,
                },
            }

        await queue_service.update_vision_job(job_id, status="completed", result=result, error=None, attempts=attempts)
        await queue_service.delete_vision_payload(job_id)

    @staticmethod
    def _safe_error(error: Exception) -> str:
        return str(error).replace("\r", " ").replace("\n", " ")[:500] or error.__class__.__name__


async def _run() -> None:
    worker = QueueWorker()
    try:
        await worker.run_forever()
    finally:
        await queue_service.close()


if __name__ == "__main__":
    asyncio.run(_run())
