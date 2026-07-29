"""
Common response schemas for unified API response format.
"""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Individual error detail for validation errors."""

    field: str | None = None
    reason: str | None = None
    value: str | None = None


class ErrorResponse(BaseModel):
    """Unified error response format for all endpoints."""

    error: bool = True
    error_code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class SuccessResponse(BaseModel):
    """Generic success response wrapper."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str | None = None
    status: str | None = None


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    message: str = "Resource deleted successfully"
