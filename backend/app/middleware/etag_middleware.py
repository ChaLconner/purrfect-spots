"""
ETag Middleware for conditional HTTP requests.

Provides ETag support for GET requests to reduce bandwidth
and improve response times via 304 Not Modified responses.

How it works:
1. Server computes ETag (hash of response body) for GET requests
2. Server includes ETag header in response
3. Client sends If-None-Match header on subsequent requests
4. Server returns 304 Not Modified if ETag matches
"""

import hashlib
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse


def _compute_etag(content: bytes) -> str:
    """Compute a strong ETag from response content."""
    hash_val = hashlib.md5(content, usedforsecurity=False).hexdigest()  # nosec B303
    return f'"{hash_val}"'


def _request_is_authenticated(request: Request) -> bool:
    """Best-effort check for requests carrying user-specific auth context."""
    if request.headers.get("Authorization"):
        return True
    return bool(request.headers.get("Cookie"))


def _is_cacheable_response(response: Response) -> bool:
    """Only generate validators for explicitly cacheable responses."""
    cache_control = response.headers.get("Cache-Control", "")
    if not cache_control:
        return False

    normalized = cache_control.lower()
    skip_tokens = ("no-store", "no-cache", "private")
    if any(token in normalized for token in skip_tokens):
        return False

    allowed_tokens = ("public", "max-age", "s-maxage", "immutable", "stale-while-revalidate")
    return any(token in normalized for token in allowed_tokens)


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds ETag headers to GET responses
    and returns 304 Not Modified when appropriate.

    Only applies to GET and HEAD requests.
    Skips responses that already have an ETag header.
    Skips streaming responses and error responses.
    """

    SAFE_METHODS = {"GET", "HEAD"}
    # PERF: Skip ETag for responses larger than 1MB to avoid excessive memory buffering
    MAX_ETAG_BODY_SIZE = 1_048_576  # 1MB

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self._should_process_request(request):
            return await call_next(request)

        response = await call_next(request)
        skip_response = self._prepare_response(request, response)
        if skip_response is not None:
            return skip_response

        body, replay_response = await self._read_response_body(response)
        if replay_response is not None:
            return replay_response
        if not body:
            return response

        return self._build_etag_response(request, response, body)

    def _should_process_request(self, request: Request) -> bool:
        return request.method in self.SAFE_METHODS and request.url.path.startswith("/api/")

    def _prepare_response(self, request: Request, response: Response) -> Response | None:
        if response.status_code >= 400:
            return response

        if _request_is_authenticated(request) and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        if "etag" in response.headers or "ETag" in response.headers:
            return response

        if not _is_cacheable_response(response):
            return response

        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_ETAG_BODY_SIZE:
            return response
        return None

    async def _read_response_body(self, response: Response) -> tuple[bytes | None, Response | None]:
        chunks: list[bytes] = []
        body_size = 0
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            chunk_bytes = chunk if isinstance(chunk, bytes) else chunk.encode()
            chunks.append(chunk_bytes)
            body_size += len(chunk_bytes)
            if body_size > self.MAX_ETAG_BODY_SIZE:
                return None, self._replay_large_response(response, chunks)

        response_body = b"".join(chunks)
        return (response_body or None), None

    def _replay_large_response(self, response: Response, chunks: list[bytes]) -> StreamingResponse:
        async def replay_body() -> AsyncIterator[bytes]:
            for replay_chunk in chunks:
                yield replay_chunk
            async for extra in response.body_iterator:  # type: ignore[attr-defined]
                yield extra if isinstance(extra, bytes) else extra.encode()

        return StreamingResponse(
            replay_body(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=response.background,
        )

    def _build_etag_response(self, request: Request, response: Response, response_body: bytes) -> Response:
        etag = _compute_etag(response_body)

        if_none_match = request.headers.get("If-None-Match")
        if if_none_match:
            client_etags = [t.strip() for t in if_none_match.split(",")]
            if etag in client_etags or "*" in client_etags:
                headers = {
                    "ETag": etag,
                    "Cache-Control": response.headers.get("Cache-Control", ""),
                }
                vary = response.headers.get("Vary")
                if vary:
                    headers["Vary"] = vary

                return Response(
                    status_code=304,
                    headers=headers,
                )

        headers = dict(response.headers)
        headers["ETag"] = etag

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
