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
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _compute_etag(content: bytes) -> str:
    """Compute a strong ETag from response content."""
    hash_val = hashlib.md5(content, usedforsecurity=False).hexdigest()  # nosec B303
    return f'"{hash_val}"'


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds ETag headers to GET responses
    and returns 304 Not Modified when appropriate.

    Only applies to GET and HEAD requests.
    Skips responses that already have an ETag header.
    Skips streaming responses and error responses.
    """

    SAFE_METHODS = {"GET", "HEAD"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Only process GET/HEAD requests
        if request.method not in self.SAFE_METHODS:
            return await call_next(request)

        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        response = await call_next(request)

        # Skip if response already has ETag or is an error
        if response.status_code >= 400:
            return response

        if "etag" in response.headers or "ETag" in response.headers:
            return response

        # Read response body
        response_body = b""
        has_body = False
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            response_body += chunk if isinstance(chunk, bytes) else chunk.encode()
            has_body = True

        if not has_body or not response_body:
            return response

        # Compute ETag
        etag = _compute_etag(response_body)

        # Check If-None-Match header
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match:
            # Support multiple ETags: "etag1", "etag2"
            client_etags = [t.strip() for t in if_none_match.split(",")]
            if etag in client_etags or "*" in client_etags:
                from fastapi.responses import Response as StarletteResponse

                return StarletteResponse(
                    status_code=304,
                    headers={
                        "ETag": etag,
                        "Cache-Control": response.headers.get("Cache-Control", ""),
                    },
                )

        # Rebuild response with ETag header
        from fastapi.responses import Response as StarletteResponse

        headers = dict(response.headers)
        headers["ETag"] = etag

        return StarletteResponse(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
