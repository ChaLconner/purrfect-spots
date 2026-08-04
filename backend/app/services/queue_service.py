"""Durable Redis Streams used for external API work.

The API verifies and persists a small queue envelope, while a long-lived
worker owns the external Stripe/Vision calls. Image bytes are stored in Redis
with a short TTL instead of being placed in the stream entry itself.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import redis.asyncio as aioredis
from redis.exceptions import ResponseError

from app.config import config
from app.logger import logger


class QueueError(RuntimeError):
    """Base class for queue failures that should be retried by callers."""


class QueueUnavailable(QueueError):
    """Raised when the configured queue Redis cannot be reached."""


class QueueBackpressure(QueueError):
    """Raised when accepting another job would exceed the configured bound."""


class QueuePayloadMissing(QueueError):
    """Raised when a Vision job no longer has its temporary image payload."""


@dataclass(frozen=True)
class QueueMessage:
    stream: str
    message_id: str
    fields: dict[str, str]


class QueueService:
    """Small Redis Streams abstraction with explicit acknowledgement semantics."""

    STRIPE_STREAM = "purrfect:queue:stripe"
    VISION_STREAM = "purrfect:queue:vision"
    STRIPE_GROUP = "purrfect-workers"
    VISION_GROUP = "purrfect-workers"
    DEAD_LETTER_SUFFIX = ":dead-letter"
    VISION_JOB_PREFIX = "purrfect:vision:job:"
    VISION_PAYLOAD_PREFIX = "purrfect:vision:payload:"
    ATTEMPT_PREFIX = "purrfect:queue:attempts:"

    def __init__(self) -> None:
        self.client: aioredis.Redis | None = None
        if config.QUEUE_REDIS_URL:
            try:
                self.client = aioredis.from_url(config.QUEUE_REDIS_URL, decode_responses=True)
            except Exception as exc:
                logger.error("Failed to configure queue Redis: %s", exc)

    @property
    def available(self) -> bool:
        return self.client is not None

    async def close(self) -> None:
        if self.client:
            try:
                await cast(Any, self.client).aclose()
            except Exception:
                logger.warning("Failed to close queue Redis pool", exc_info=True)

    async def ping(self) -> bool:
        if not self.client:
            return False
        try:
            return bool(await self.client.ping())
        except Exception:
            return False

    def _require_client(self) -> aioredis.Redis:
        if not self.client:
            raise QueueUnavailable("Queue Redis is not configured")
        return self.client

    async def ensure_group(self, stream: str, group: str) -> None:
        client = self._require_client()
        try:
            await client.xgroup_create(stream, group, id="0-0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise QueueUnavailable("Unable to create Redis consumer group") from exc
        except Exception as exc:
            raise QueueUnavailable("Unable to create Redis consumer group") from exc

    async def ensure_groups(self) -> None:
        await self.ensure_group(self.STRIPE_STREAM, self.STRIPE_GROUP)
        await self.ensure_group(self.VISION_STREAM, self.VISION_GROUP)

    @staticmethod
    def _serialize(value: Any) -> str:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False, default=str)

    @staticmethod
    def _deserialize(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        try:
            parsed = json.loads(value.decode() if isinstance(value, bytes) else str(value))
        except (TypeError, ValueError, UnicodeDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    async def _ensure_capacity(self, stream: str) -> None:
        client = self._require_client()
        try:
            length = int(await client.xlen(stream))
        except Exception as exc:
            raise QueueUnavailable("Unable to inspect Redis queue capacity") from exc
        if length >= config.QUEUE_STREAM_MAXLEN:
            raise QueueBackpressure("Queue is full; retry after the worker drains pending jobs")

    async def enqueue_stripe_webhook(self, event: dict[str, Any]) -> str:
        """Enqueue an already signature-verified Stripe event."""
        client = self._require_client()
        event_id = str(event.get("id") or "")
        event_type = str(event.get("type") or "")
        if not event_id or not event_type:
            raise ValueError("Stripe event is missing id or type")

        await self.ensure_group(self.STRIPE_STREAM, self.STRIPE_GROUP)
        await self._ensure_capacity(self.STRIPE_STREAM)
        try:
            message_id = await client.xadd(
                self.STRIPE_STREAM,
                {"event_id": event_id, "event_type": event_type, "event": self._serialize(event)},
            )
        except Exception as exc:
            raise QueueUnavailable("Unable to enqueue Stripe webhook") from exc
        return str(message_id)

    async def enqueue_vision_job(
        self,
        *,
        operation: str,
        user_id: str,
        analyzed_by: str,
        filename: str | None,
        contents: bytes,
    ) -> dict[str, Any]:
        """Store a bounded temporary payload and enqueue a Vision job."""
        if len(contents) > config.VISION_QUEUE_MAX_IMAGE_BYTES:
            raise QueueBackpressure("Image is too large for the Vision queue")
        if operation not in {"spot-analysis", "combined"}:
            raise ValueError("Unsupported Vision queue operation")

        client = self._require_client()
        await self.ensure_group(self.VISION_STREAM, self.VISION_GROUP)
        await self._ensure_capacity(self.VISION_STREAM)

        job_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        job = {
            "job_id": job_id,
            "operation": operation,
            "user_id": user_id,
            "filename": filename or "uploaded-image",
            "analyzed_by": analyzed_by,
            "status": "queued",
            "result": None,
            "error": None,
            "attempts": 0,
            "created_at": now,
            "updated_at": now,
        }
        payload_key = f"{self.VISION_PAYLOAD_PREFIX}{job_id}"
        job_key = f"{self.VISION_JOB_PREFIX}{job_id}"
        encoded_contents = base64.b64encode(contents).decode("ascii")

        try:
            await client.set(payload_key, encoded_contents, ex=config.QUEUE_RESULT_TTL_SECONDS)
            await client.set(job_key, self._serialize(job), ex=config.QUEUE_RESULT_TTL_SECONDS)
            await client.xadd(
                self.VISION_STREAM,
                {"job_id": job_id, "operation": operation, "user_id": user_id},
            )
        except Exception as exc:
            try:
                await client.delete(payload_key, job_key)
            except Exception:
                logger.warning("Failed to clean up partially enqueued Vision job %s", job_id, exc_info=True)
            raise QueueUnavailable("Unable to enqueue Vision job") from exc
        return job

    async def get_vision_job(self, job_id: str, user_id: str) -> dict[str, Any] | None:
        client = self._require_client()
        try:
            raw = await client.get(f"{self.VISION_JOB_PREFIX}{job_id}")
        except Exception as exc:
            raise QueueUnavailable("Unable to read Vision job status") from exc
        job = self._deserialize(raw)
        if not job or str(job.get("user_id")) != user_id:
            return None
        return job

    async def update_vision_job(self, job_id: str, **updates: Any) -> dict[str, Any] | None:
        client = self._require_client()
        key = f"{self.VISION_JOB_PREFIX}{job_id}"
        try:
            current = self._deserialize(await client.get(key))
        except Exception as exc:
            raise QueueUnavailable("Unable to read Vision job state") from exc
        if not current:
            return None
        current.update(updates)
        current["updated_at"] = datetime.now(UTC).isoformat()
        try:
            await client.set(key, self._serialize(current), ex=config.QUEUE_RESULT_TTL_SECONDS)
        except Exception as exc:
            raise QueueUnavailable("Unable to update Vision job state") from exc
        return current

    async def get_vision_payload(self, job_id: str) -> bytes:
        client = self._require_client()
        try:
            raw = await client.get(f"{self.VISION_PAYLOAD_PREFIX}{job_id}")
        except Exception as exc:
            raise QueueUnavailable("Unable to read Vision payload") from exc
        if raw is None:
            raise QueuePayloadMissing(f"Vision payload expired for job {job_id}")
        try:
            return base64.b64decode(raw.decode() if isinstance(raw, bytes) else str(raw), validate=True)
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise QueuePayloadMissing(f"Vision payload is invalid for job {job_id}") from exc

    async def delete_vision_payload(self, job_id: str) -> None:
        client = self._require_client()
        try:
            await client.delete(f"{self.VISION_PAYLOAD_PREFIX}{job_id}")
        except Exception as exc:
            raise QueueUnavailable("Unable to delete Vision payload") from exc

    async def read_group(
        self,
        *,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 1000,
    ) -> list[QueueMessage]:
        client = self._require_client()
        try:
            raw = await client.xreadgroup(
                group,
                consumer,
                {stream: ">"},
                count=count,
                block=block_ms,
            )
        except Exception as exc:
            raise QueueUnavailable("Unable to read Redis queue") from exc
        return self._flatten_messages(stream, raw)

    async def claim_stale(
        self,
        *,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
    ) -> list[QueueMessage]:
        client = self._require_client()
        try:
            raw = await client.xautoclaim(
                stream,
                group,
                consumer,
                config.QUEUE_VISIBILITY_TIMEOUT_SECONDS * 1000,
                start_id="0-0",
                count=count,
            )
        except Exception as exc:
            raise QueueUnavailable("Unable to reclaim Redis queue entries") from exc
        entries = raw[1] if isinstance(raw, (list, tuple)) and len(raw) > 1 else []
        return [
            QueueMessage(stream=stream, message_id=str(message_id), fields={str(k): str(v) for k, v in fields.items()})
            for message_id, fields in entries
        ]

    @staticmethod
    def _flatten_messages(stream: str, raw: Any) -> list[QueueMessage]:
        messages: list[QueueMessage] = []
        for stream_name, entries in raw or []:
            actual_stream = str(stream_name or stream)
            for message_id, fields in entries:
                messages.append(
                    QueueMessage(
                        stream=actual_stream,
                        message_id=str(message_id),
                        fields={str(k): str(v) for k, v in fields.items()},
                    )
                )
        return messages

    async def acknowledge(self, message: QueueMessage, group: str) -> None:
        client = self._require_client()
        try:
            acknowledged = await client.xack(message.stream, group, message.message_id)
        except Exception as exc:
            raise QueueUnavailable("Unable to acknowledge Redis queue entry") from exc
        if acknowledged:
            # Explicit deletion keeps the stream bounded without trimming a
            # still-pending entry belonging to another consumer.
            try:
                await client.xdel(message.stream, message.message_id)
            except Exception as exc:
                raise QueueUnavailable("Unable to remove acknowledged queue entry") from exc

    async def dead_letter(self, message: QueueMessage, group: str, reason: str) -> None:
        client = self._require_client()
        dead_letter_stream = f"{message.stream}{self.DEAD_LETTER_SUFFIX}"
        payload = {
            "source_stream": message.stream,
            "source_message_id": message.message_id,
            "reason": reason[:500],
            "fields": message.fields,
            "failed_at": datetime.now(UTC).isoformat(),
        }
        try:
            await client.xadd(dead_letter_stream, {"message": self._serialize(payload)})
        except Exception as exc:
            raise QueueUnavailable("Unable to write queue dead-letter entry") from exc
        await self.acknowledge(message, group)

    async def increment_attempt(self, message: QueueMessage) -> int:
        client = self._require_client()
        key = f"{self.ATTEMPT_PREFIX}{message.stream}:{message.message_id}"
        try:
            attempts = int(await client.incr(key))
        except Exception as exc:
            raise QueueUnavailable("Unable to record queue attempt") from exc
        if attempts == 1:
            try:
                await client.expire(key, config.QUEUE_RESULT_TTL_SECONDS)
            except Exception as exc:
                raise QueueUnavailable("Unable to expire queue attempt state") from exc
        return attempts

    async def clear_attempt(self, message: QueueMessage) -> None:
        client = self._require_client()
        try:
            await client.delete(f"{self.ATTEMPT_PREFIX}{message.stream}:{message.message_id}")
        except Exception as exc:
            raise QueueUnavailable("Unable to clear queue attempt state") from exc


queue_service = QueueService()
