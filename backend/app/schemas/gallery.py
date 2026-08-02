"""
Gallery response schemas with cursor-based pagination, sorting, and field selection.
"""

from enum import StrEnum

from pydantic import BaseModel

from app.schemas.location import CatLocation


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


class PaginatedGalleryResponse(BaseModel):
    """Unified response for offset-based gallery."""

    images: list[CatLocation]
    pagination: PaginationMeta


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
