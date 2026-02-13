"""
Request ID Middleware for tracing and audit logging.

Adds a unique request ID to each request for:
- Distributed tracing
- Log correlation
- Audit trail
- Debugging
"""

import uuid
from contextvars import ContextVar

from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Context variable for request ID (thread-safe, async-safe)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Adds unique request ID to each request.

    Features:
    - Accepts existing X-Request-ID from load balancer/proxy
    - Generates UUID v4 if not provided
    - Adds ID to response headers for client correlation
    - Stores in context variable for logging access
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Get existing request ID or generate new one
        request_id = request.headers.get(self.HEADER_NAME)
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set in context for logging
        token = request_id_ctx.set(request_id)

        # Add to request state for handlers to access
        request.state.request_id = request_id

        try:
            # Process request
            response = await call_next(request)

            # Add to response headers for client tracing
            response.headers[self.HEADER_NAME] = request_id

            return response
        finally:
            # Reset context
            request_id_ctx.reset(token)


def get_request_id() -> str:
    """
    Get current request ID from context.

    Returns empty string if called outside of request context.
    """
    return request_id_ctx.get()


def get_request_id_optional() -> str | None:
    """
    Get current request ID, returning None if not in request context.
    """
    rid = request_id_ctx.get()
    return rid if rid else None
