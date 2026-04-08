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

    has_more: bool
    next_cursor: str | None = None
    prev_cursor: str | None = None
    limit: int


class PaginatedGalleryResponse(BaseModel):
    """Paginated gallery response with offset-based metadata."""

    images: list[CatLocation]
    pagination: PaginationMeta


class CursorPaginatedGalleryResponse(BaseModel):
    """Paginated gallery response with cursor-based metadata."""

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


# ---- Cursor helpers ----


def encode_cursor(photo_id: str) -> str:
    """Encode a photo_id into an opaque cursor string."""
    payload = json.dumps({"id": photo_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> str | None:
    """Decode cursor string back to photo_id. Returns None if invalid."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return payload.get("id")
    except Exception:
        return None


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
