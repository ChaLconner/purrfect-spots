import asyncio

import pytest

from app.services.redis_service import RedisService


@pytest.mark.asyncio
async def test_lock_serializes_same_quota_key() -> None:
    """Per-user quota locks must prevent overlapping critical sections."""
    service = RedisService()
    entered: list[str] = []
    release_first = asyncio.Event()

    async def first_request() -> None:
        async with service.lock("quota:upload:user-1", ttl=30, wait_timeout=1):
            entered.append("first")
            await release_first.wait()

    async def second_request() -> None:
        async with service.lock("quota:upload:user-1", ttl=30, wait_timeout=1):
            entered.append("second")

    first = asyncio.create_task(first_request())
    await asyncio.sleep(0)
    second = asyncio.create_task(second_request())
    await asyncio.sleep(0)

    assert entered == ["first"]
    release_first.set()
    await asyncio.gather(first, second)
    assert entered == ["first", "second"]
