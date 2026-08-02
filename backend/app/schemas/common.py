"""
Common response schemas for unified API response format.
"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str | None = None
    status: str | None = None
