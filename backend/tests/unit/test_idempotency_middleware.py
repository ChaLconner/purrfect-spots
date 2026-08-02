from collections.abc import Awaitable, Callable
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.middleware import idempotency_middleware as middleware_module
from app.middleware.idempotency_middleware import IdempotencyMiddleware


def _middleware() -> IdempotencyMiddleware:
    # dispatch() is tested directly; the ASGI app is never invoked here.
    return IdempotencyMiddleware(cast(Any, object()))


def _request(authorization: str) -> Request:
    body = b'{"price_id":"price_pro"}'

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    headers = [
        (b"content-type", b"application/json"),
        (b"idempotency-key", b"same-key"),
        (b"authorization", authorization.encode()),
    ]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/subscription/checkout",
            "raw_path": b"/api/v1/subscription/checkout",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
        },
        receive,
    )


async def _response_chunks(response: JSONResponse):
    yield response.body


@pytest.mark.asyncio
async def test_idempotency_cache_isolated_between_bearer_tokens() -> None:
    middleware = _middleware()
    responses: dict[str, dict[str, Any]] = {}

    async def get_cached(key: str) -> dict[str, Any] | None:
        return responses.get(key)

    async def set_cached(key: str, value: dict[str, Any], ttl: int = 86400) -> None:
        responses[key] = value

    calls: list[str] = []

    async def call_next(request: Request) -> Response:
        calls.append(request.headers["authorization"])
        response = JSONResponse({"served_for": request.headers["authorization"]})
        response.body_iterator = _response_chunks(response)  # type: ignore[attr-defined]
        return response

    with (
        patch.object(middleware_module, "_get_cached_response", side_effect=get_cached),
        patch.object(middleware_module, "_set_cached_response", side_effect=set_cached),
    ):
        first = await middleware.dispatch(_request("Bearer token-a"), call_next)
        second = await middleware.dispatch(_request("Bearer token-b"), call_next)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.body == b'{"served_for":"Bearer token-a"}'
    assert second.body == b'{"served_for":"Bearer token-b"}'
    assert calls == ["Bearer token-a", "Bearer token-b"]
    assert "X-Idempotent-Replayed" not in second.headers


@pytest.mark.asyncio
async def test_idempotency_replays_for_same_bearer_token() -> None:
    middleware = _middleware()
    responses: dict[str, dict[str, Any]] = {}

    async def get_cached(key: str) -> dict[str, Any] | None:
        return responses.get(key)

    async def set_cached(key: str, value: dict[str, Any], ttl: int = 86400) -> None:
        responses[key] = value

    response = JSONResponse({"served_for": "token-a"})
    response.body_iterator = _response_chunks(response)  # type: ignore[attr-defined]
    call_next: Callable[[Request], Awaitable[Response]] = AsyncMock(return_value=response)

    with (
        patch.object(middleware_module, "_get_cached_response", side_effect=get_cached),
        patch.object(middleware_module, "_set_cached_response", side_effect=set_cached),
    ):
        await middleware.dispatch(_request("Bearer token-a"), call_next)
        replay = await middleware.dispatch(_request("Bearer token-a"), call_next)

    assert replay.headers["X-Idempotent-Replayed"] == "true"
    assert call_next.await_count == 1  # type: ignore[attr-defined]
