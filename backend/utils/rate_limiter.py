"""
In-memory rate limiter for API endpoints.

Uses a sliding window counter per key (e.g., user_id + action)
to prevent abuse without requiring external infrastructure like Redis.

Thread-safe via asyncio lock.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Tuple

from logger import logger


class RateLimiter:
    """
    Simple in-memory sliding window rate limiter.

    Usage:
        limiter = RateLimiter(max_requests=5, window_seconds=10)

        if not await limiter.is_allowed("user123:like"):
            raise HTTPException(429, "Too many requests")
    """

    def __init__(self, max_requests: int = 5, window_seconds: float = 10.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> (request_count, window_start_time)
        self._windows: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.

        Uses a fixed window counter that resets after window_seconds.
        Returns True if allowed, False if rate limited.
        """
        async with self._lock:
            now = time.monotonic()
            req_count, window_start = self._windows[key]

            # Reset window if expired
            if now - window_start >= self.window_seconds:
                self._windows[key] = (1, now)
                return True

            # Check if within limit
            if req_count < self.max_requests:
                self._windows[key] = (req_count + 1, window_start)
                return True

            logger.warning(f"Rate limit exceeded for key: {key}")
            return False

    async def cleanup(self) -> None:
        """Remove expired entries to prevent memory leaks. Call periodically."""
        async with self._lock:
            now = time.monotonic()
            expired_keys = [k for k, (_, start) in self._windows.items() if now - start >= self.window_seconds * 2]
            for k in expired_keys:
                del self._windows[k]


# Shared rate limiter instances
like_rate_limiter = RateLimiter(max_requests=10, window_seconds=10.0)
