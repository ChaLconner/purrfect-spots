"""
Idempotency Key Middleware for POST operations.

Provides exactly-once semantics for state-changing POST requests
by caching responses keyed by Idempotency-Key header.

Usage:
    Client sends: Idempotency-Key: <unique-uuid>
    Server caches the response for 24 hours.
    Duplicate requests with the same key return the cached response.
"""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.logger import logger

# In-memory fallback store (used when Redis is unavailable)
_memory_store: dict[str, dict[str, Any]] = {}
_inflight_locks: dict[str, asyncio.Lock] = {}

# Redis key prefix
REDIS_PREFIX = "idempotency:"
DEFAULT_TTL = 86400  # 24 hours


def _build_idempotency_key(header_key: str, method: str, path: str, body_hash: str) -> str:
    """Build a composite idempotency key to prevent key reuse across endpoints."""
    raw = f"{header_key}:{method}:{path}:{body_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_principal_fingerprint(request: Request) -> str | None:
    """Return a non-secret credential fingerprint for idempotency scoping.

    This middleware runs before FastAPI dependencies authenticate the request.
    Hashing the presented credential keeps the cache isolated between sessions
    without trusting unverified JWT claims or logging bearer tokens.
    """
    authorization = request.headers.get("Authorization", "").strip()
    if authorization:
        return hashlib.sha256(f"bearer:{authorization}".encode()).hexdigest()

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        return hashlib.sha256(f"refresh:{refresh_token}".encode()).hexdigest()

    # Never share state-changing responses between anonymous callers.
    return None


async def _get_cached_response(key: str) -> dict[str, Any] | None:
    """Try to get a cached idempotency response from Redis or memory."""
    # Try Redis first
    try:
        from app.utils.cache import redis_client

        if redis_client:
            cached = await redis_client.get(f"{REDIS_PREFIX}{key}")
            if cached:
                from typing import cast

                return cast(dict[str, Any], json.loads(cached))
    except Exception as e:
        logger.debug(f"Failed to fetch cached idempotency response: {e}")
        # pass

    # Fallback to memory
    return _memory_store.get(key)


async def _set_cached_response(key: str, response_data: dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
    """Cache an idempotency response in Redis or memory."""
    try:
        from app.utils.cache import redis_client

        if redis_client:
            await redis_client.setex(f"{REDIS_PREFIX}{key}", ttl, json.dumps(response_data))
            return
    except Exception as e:
        logger.warning("Failed to cache idempotency response in Redis: %s", e)

    # Fallback to memory (with basic cleanup)
    if len(_memory_store) > 1000:
        # Simple eviction: remove oldest 20%
        keys = list(_memory_store.keys())
        for k in keys[:200]:
            _memory_store.pop(k, None)
    _memory_store[key] = response_data


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides idempotency for POST requests.

    Only applies to POST requests that include an Idempotency-Key header.
    Caches the full response (status + body) for 24 hours.

    Security: The cached response is keyed by a credential fingerprint plus
    (idempotency_key + method + path + body_hash) so one account cannot replay
    another account's response.
    """

    IDEMPOTENT_METHODS = {"POST"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Only process POST requests with Idempotency-Key header
        if request.method not in self.IDEMPOTENT_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        principal_fingerprint = _get_principal_fingerprint(request)
        if principal_fingerprint is None:
            return await call_next(request)

        # Multipart uploads are streamed and must not be copied into memory by
        # middleware. Upload routes own their idempotency token handling.
        content_type = request.headers.get("content-type", "").lower()
        if not content_type.startswith("application/json"):
            return await call_next(request)

        # Read and hash the request body
        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest()[:16]

        # Build composite key
        composite_key = _build_idempotency_key(
            header_key=f"{principal_fingerprint}:{idempotency_key}",
            method=request.method,
            path=request.url.path,
            body_hash=body_hash,
        )

        lock = _inflight_locks.setdefault(composite_key, asyncio.Lock())
        try:
            async with lock:
                # Re-check after waiting so concurrent requests share one result.
                cached = await _get_cached_response(composite_key)
                if cached is not None:
                    logger.info(
                        "Idempotent replay: key=%s path=%s",
                        idempotency_key[:16] + "...",
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=cached.get("status_code", 200),
                        content=cached.get("body", {}),
                        headers={
                            **cached.get("headers", {}),
                            "X-Idempotent-Replayed": "true",
                        },
                    )

                response = await call_next(request)

                # Cache only bounded JSON responses. Never copy an unbounded body.
                if 200 <= response.status_code < 500:
                    content_length = int(response.headers.get("content-length", "0") or 0)
                    if 0 < content_length <= 1_048_576:
                        response_chunks: list[bytes] = []
                        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                            response_chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
                        response_body = b"".join(response_chunks)

                        try:
                            body_json = json.loads(response_body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            body_json = None

                        if body_json is not None:
                            response_data = {
                                "status_code": response.status_code,
                                "body": body_json,
                                "headers": {"Content-Type": "application/json"},
                            }
                            await _set_cached_response(composite_key, response_data)
                            return JSONResponse(
                                status_code=response.status_code,
                                content=body_json,
                                headers=dict(response.headers),
                            )

                return response
        finally:
            waiters = getattr(lock, "_waiters", None)
            if not lock.locked() and not waiters:
                _inflight_locks.pop(composite_key, None)
