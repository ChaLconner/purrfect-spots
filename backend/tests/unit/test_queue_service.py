from __future__ import annotations

import json
from typing import Any

import pytest

from app.services.queue_service import QueueService, QueueUnavailable


class FakeRedis:
    def __init__(self) -> None:
        self.streams: dict[str, list[tuple[str, dict[str, str]]]] = {}
        self.values: dict[str, str] = {}
        self.groups: set[tuple[str, str]] = set()
        self.sequence = 0

    async def ping(self) -> bool:
        return True

    async def xgroup_create(self, stream: str, group: str, *, id: str, mkstream: bool) -> None:
        self.groups.add((stream, group))
        self.streams.setdefault(stream, [])

    async def xlen(self, stream: str) -> int:
        return len(self.streams.get(stream, []))

    async def xadd(self, stream: str, fields: dict[str, str], **_: Any) -> str:
        self.sequence += 1
        message_id = f"{self.sequence}-0"
        self.streams.setdefault(stream, []).append((message_id, fields))
        return message_id

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        self.values[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            deleted += int(self.values.pop(key, None) is not None)
        return deleted

    async def xreadgroup(self, *_: Any, **__: Any) -> list[Any]:
        return []

    async def xautoclaim(self, *_: Any, **__: Any) -> list[Any]:
        return ["0-0", [], []]

    async def xack(self, *_: Any, **__: Any) -> int:
        return 1

    async def xdel(self, stream: str, message_id: str) -> int:
        self.streams[stream] = [entry for entry in self.streams.get(stream, []) if entry[0] != message_id]
        return 1

    async def incr(self, key: str) -> int:
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def expire(self, *_: Any, **__: Any) -> bool:
        return True


class FailingVisionRedis(FakeRedis):
    async def xadd(self, stream: str, fields: dict[str, str], **kwargs: Any) -> str:
        if stream == QueueService.VISION_STREAM:
            raise ConnectionError("redis connection lost")
        return await super().xadd(stream, fields, **kwargs)

    async def delete(self, *_: str) -> int:
        raise ConnectionError("redis connection lost")


@pytest.mark.asyncio
async def test_enqueue_stripe_event_and_vision_payload_round_trip() -> None:
    service = QueueService()
    fake = FakeRedis()
    service.client = fake  # type: ignore[assignment]

    stripe_message_id = await service.enqueue_stripe_webhook(
        {
            "id": "evt_test_1",
            "type": "invoice.paid",
            "created": 1,
            "data": {"object": {"id": "in_test_1"}},
        }
    )
    job = await service.enqueue_vision_job(
        operation="spot-analysis",
        user_id="user-1",
        analyzed_by="user@example.com",
        filename="spot.jpg",
        contents=b"image-bytes",
    )

    assert stripe_message_id == "1-0"
    assert json.loads(fake.streams[service.STRIPE_STREAM][0][1]["event"])["id"] == "evt_test_1"
    assert await service.get_vision_payload(job["job_id"]) == b"image-bytes"
    stored_job = await service.get_vision_job(job["job_id"], "user-1")
    assert stored_job is not None
    assert stored_job["status"] == "queued"
    assert await service.get_vision_job(job["job_id"], "other-user") is None

    await service.close()


@pytest.mark.asyncio
async def test_vision_enqueue_preserves_queue_error_when_cleanup_also_fails() -> None:
    service = QueueService()
    service.client = FailingVisionRedis()  # type: ignore[assignment]

    with pytest.raises(QueueUnavailable):
        await service.enqueue_vision_job(
            operation="spot-analysis",
            user_id="user-1",
            analyzed_by="user@example.com",
            filename="spot.jpg",
            contents=b"image-bytes",
        )
