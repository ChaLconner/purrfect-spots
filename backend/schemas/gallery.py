from pydantic import BaseModel

from schemas.location import CatLocation


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int
    limit: int
    offset: int
    has_more: bool
    page: int
    total_pages: int


class PaginatedGalleryResponse(BaseModel):
    """Paginated gallery response with metadata"""
    images: list[CatLocation]
    pagination: PaginationMeta


class GalleryResponse(BaseModel):
    """Legacy response for backward compatibility"""
    images: list[CatLocation]


class SearchResponse(BaseModel):
    results: list[CatLocation]
    total: int
    query: str | None = None
    tags: list[str] | None = None


class TagInfo(BaseModel):
    tag: str
    count: int


class PopularTagsResponse(BaseModel):
    tags: list[TagInfo]
