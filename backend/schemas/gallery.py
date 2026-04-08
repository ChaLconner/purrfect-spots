"""
Gallery response schemas with cursor-based pagination, sorting, and field selection.
"""

import base64
import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from schemas.location import CatLocation


class SortField(StrEnum):
    """Allowed sort fields for gallery."""

    UPLOADED_AT = "uploaded_at"
    LIKES_COUNT = "likes_count"
    COMMENTS_COUNT = "comments_count"


class SortOrder(StrEnum):
    """Sort order."""

    ASC = "asc"
    DESC = "desc"


class PaginationMeta(BaseModel):
    """Offset-based pagination metadata."""

    total: int
    limit: int
    offset: int
    has_more: bool
    page: int
    total_pages: int


class CursorPaginationMeta(BaseModel):
    """Cursor-based pagination metadata."""

    next_cursor: str | None = None
    has_more: bool


class PaginatedGalleryResponse(BaseModel):
    """Unified response for offset-based gallery."""

    images: list[CatLocation]
    pagination: PaginationMeta


class CursorPaginatedGalleryResponse(BaseModel):
    """Unified response for cursor-based gallery."""

    images: list[CatLocation]
    pagination: CursorPaginationMeta


class GalleryResponse(BaseModel):
    """Legacy response for backward compatibility."""

    images: list[CatLocation]


class SearchResponse(BaseModel):
    results: list[CatLocation]
    total: int
    query: str | None = None
    tags: list[str] | None = None
    limit: int | None = None
    offset: int | None = None


class TagInfo(BaseModel):
    tag: str
    count: int


class PopularTagsResponse(BaseModel):
    tags: list[TagInfo]


class UploadQuotaResponse(BaseModel):
    """Upload quota status response."""

    used: int
    limit: int
    remaining: int
    is_pro: bool
    reset_type: str | None = None
    resets_at: str | None = None


class UploadPhotoResponse(BaseModel):
    """Response after successful photo upload."""

    success: bool = True
    message: str
    photo: dict[str, Any]
    cat_detection: dict[str, Any] | None = None
    uploaded_by: str | None = None


class BulkDeleteRequest(BaseModel):
    """Request body for bulk delete."""

    photo_ids: list[str] = Field(..., min_length=1, max_length=50)


class BulkDeleteResponse(BaseModel):
    """Response for bulk delete."""

    message: str
    deleted_count: int
    failed_ids: list[str] = []


# ---- Allowed fields for ?fields= parameter ----

GALLERY_ALLOWED_FIELDS: set[str] = {
    "id",
    "image_url",
    "latitude",
    "longitude",
    "description",
    "location_name",
    "uploaded_at",
    "tags",
    "likes_count",
    "comments_count",
    "user_id",
    "liked",
}


# ---- Cursor helpers ----


def encode_cursor(data: dict[str, Any]) -> str:
    """Encode a dictionary to a base64 cursor string."""
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a base64 cursor string to a dictionary."""
    if not cursor:
        return {}
    try:
        # Add padding back if needed
        padding = "=" * (4 - len(cursor) % 4)
        json_str = base64.urlsafe_b64decode(cursor + padding).decode()
        return json.loads(json_str)
    except Exception:
        return {}
