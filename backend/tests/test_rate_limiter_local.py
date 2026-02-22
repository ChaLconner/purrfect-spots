import asyncio

import pytest

from utils.rate_limiter import RateLimiter, like_rate_limiter


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    limiter = RateLimiter(max_requests=2, window_seconds=1.0)

    # 1st request allowed
    assert await limiter.is_allowed("test_key") is True
    # 2nd request allowed
    assert await limiter.is_allowed("test_key") is True
    # 3rd request blocked
    assert await limiter.is_allowed("test_key") is False


@pytest.mark.asyncio
async def test_rate_limiter_window_reset():
    limiter = RateLimiter(max_requests=1, window_seconds=0.1)

    # 1st request allowed
    assert await limiter.is_allowed("test_key_2") is True
    # 2nd request blocked
    assert await limiter.is_allowed("test_key_2") is False

    # Wait for window to reset
    await asyncio.sleep(0.15)

    # 1st request allowed again
    assert await limiter.is_allowed("test_key_2") is True


@pytest.mark.asyncio
async def test_rate_limiter_cleanup():
    limiter = RateLimiter(max_requests=1, window_seconds=0.1)

    await limiter.is_allowed("test_key_3")

    # Wait to ensure it expires
    await asyncio.sleep(0.3)

    await limiter.cleanup()

    assert "test_key_3" not in limiter._windows


@pytest.mark.asyncio
async def test_shared_like_limiter():
    assert like_rate_limiter.max_requests == 10
    assert like_rate_limiter.window_seconds == 10.0
