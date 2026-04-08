"""
Gallery routes with API-side pagination, cursor-based pagination,
sorting, field selection, and ETag support.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request, Response

from dependencies import get_current_token, get_gallery_service
from limiter import get_api_limit, limiter
from logger import logger, sanitize_log_value
from middleware.auth_middleware import (
    get_current_user_from_credentials,
    get_current_user_optional,
)
from schemas.gallery import (
    GALLERY_ALLOWED_FIELDS,
    CursorPaginatedGalleryResponse,
    CursorPaginationMeta,
    GalleryResponse,
    PaginatedGalleryResponse,
    PaginationMeta,
    PopularTagsResponse,
    SearchResponse,
    SortField,
    SortOrder,
    TagInfo,
    decode_cursor,
    encode_cursor,
)
from schemas.location import CatLocation
from schemas.user import User
from services.gallery_service import GalleryService
from services.storage_service import storage_service
from utils.location_utils import protect_photo_location, protect_photo_locations

router = APIRouter(prefix="/gallery", tags=["Gallery"])

PhotoIdPath = Annotated[UUID, Path(title="The ID of the photo", description="Must be a valid UUID")]


def _filter_fields(data: dict[str, Any], fields: set[str] | None) -> dict[str, Any]:
    """Filter a dict to only include specified fields."""
    if not fields:
        return data
    return {k: v for k, v in data.items() if k in fields}


def _apply_sort(
    photos: list[dict[str, Any]],
    sort: SortField | None,
    order: SortOrder,
) -> list[dict[str, Any]]:
    """Sort photos list by the given field and order."""
    if not sort:
        return photos

    reverse = order == SortOrder.DESC
    sort_key = sort.value

    def _get_sort_val(item: dict[str, Any]) -> Any:
        val = item.get(sort_key)
        if val is None:
            return "" if isinstance(val, str) else 0
        return val

    return sorted(photos, key=_get_sort_val, reverse=reverse)


# ---- Offset-based pagination (default) ----


@router.get(
    "",
    response_model=PaginatedGalleryResponse,
    responses={
        200: {"description": "Successful Response"},
        500: {"description": "Internal Server Error"},
    },
)
@limiter.limit(get_api_limit)
async def get_gallery(
    request: Request,
    response: Response,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    token: Annotated[str | None, Depends(get_current_token)],
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    page: int | None = Query(None, ge=1, description="Page number (alternative to offset)"),
    sort: SortField | None = Query(None, description="Sort field: uploaded_at, likes_count, comments_count"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order: asc or desc"),
    fields: str | None = Query(None, description="Comma-separated list of fields to include"),
) -> PaginatedGalleryResponse:
    """
    Get cat images with pagination, sorting, and field selection.

    Examples:
    - `/gallery?limit=20&offset=0` - First 20 images
    - `/gallery?limit=20&page=2` - Second page of 20 images
    - `/gallery?sort=likes_count&order=desc` - Sort by most liked
    - `/gallery?fields=id,image_url,location_name` - Only specific fields
    """
    # Dynamic caching strategy
    if current_user:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        # Improved caching for public gallery
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

    # Parse fields filter
    selected_fields: set[str] | None = None
    if fields:
        requested = {f.strip() for f in fields.split(",") if f.strip()}
        selected_fields = requested & GALLERY_ALLOWED_FIELDS
        # Always include id
        selected_fields.add("id")

    try:
        actual_offset = offset
        if page is not None:
            actual_offset = (page - 1) * limit

        result = await gallery_service.get_all_photos(
            limit=limit,
            offset=actual_offset,
            include_total=True,
            user_id=current_user.id if current_user else None,
            jwt_token=token if current_user else None,
        )

        if not result["data"]:
            return PaginatedGalleryResponse(
                images=[],
                pagination=PaginationMeta(
                    total=0,
                    limit=limit,
                    offset=actual_offset,
                    has_more=False,
                    page=1,
                    total_pages=0,
                ),
            )

        # Apply sorting
        sorted_data = _apply_sort(result["data"], sort, order)
        protected_data = protect_photo_locations(sorted_data)

        # Apply field selection
        if selected_fields:
            protected_data = [_filter_fields(d, selected_fields) for d in protected_data]

        total = result["total"]
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        current_page = (actual_offset // limit) + 1 if limit > 0 else 1

        cat_locations = [CatLocation(**photo) for photo in protected_data]

        return PaginatedGalleryResponse(
            images=cat_locations,
            pagination=PaginationMeta(
                total=total,
                limit=limit,
                offset=actual_offset,
                has_more=result["has_more"],
                page=current_page,
                total_pages=total_pages,
            ),
        )

    except Exception as e:
        logger.error("Gallery fetch error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


@router.get(
    "/cursor",
    response_model=CursorPaginatedGalleryResponse,
    deprecated=True,
    responses={
        200: {"description": "Successful Response"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_gallery_cursor(
    request: Request,
    response: Response,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    token: Annotated[str | None, Depends(get_current_token)],
    cursor: str | None = Query(None, description="Cursor for pagination (from previous response)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort: SortField | None = Query(SortField.UPLOADED_AT, description="Sort field"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    fields: str | None = Query(None, description="Comma-separated list of fields to include"),
) -> CursorPaginatedGalleryResponse:
    """
    Get cat images with cursor-based pagination.

    DEPRECATED: Frontend uses offset-based pagination.
    Sunset: 2026-07-01
    """
    response.headers["X-API-Warn"] = "Deprecated: Cursor-based pagination is scheduled for removal on 2026-07-01."
    if current_user:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        response.headers["Cache-Control"] = "public, max-age=60"

    selected_fields: set[str] | None = None
    if fields:
        requested = {f.strip() for f in fields.split(",") if f.strip()}
        selected_fields = requested & GALLERY_ALLOWED_FIELDS
        selected_fields.add("id")

    try:
        # Decode cursor to get the starting photo_id
        after_id = decode_cursor(cursor) if cursor else None

        # Fetch one extra to determine has_more
        result = await gallery_service.get_all_photos_cursor(
            limit=limit + 1,
            after_id=after_id,
            sort_field=sort.value if sort else "uploaded_at",
            sort_order=order.value,
            user_id=current_user.id if current_user else None,
            jwt_token=token if current_user else None,
        )

        photos = result.get("data", [])
        has_more = len(photos) > limit

        # Trim to requested limit
        if has_more:
            photos = photos[:limit]

        photos = protect_photo_locations(photos)

        # Apply field selection
        if selected_fields:
            photos = [_filter_fields(d, selected_fields) for d in photos]

        cat_locations = [CatLocation(**photo) for photo in photos]

        # Build cursors
        next_cursor = encode_cursor(cat_locations[-1].id) if has_more and cat_locations else None
        prev_cursor = encode_cursor(cat_locations[0].id) if cat_locations and cursor else None

        return CursorPaginatedGalleryResponse(
            images=cat_locations,
            pagination=CursorPaginationMeta(
                has_more=has_more,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
                limit=limit,
            ),
        )

    except Exception as e:
        logger.error("Cursor gallery fetch error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


# ---- Locations endpoint ----


@router.get("/locations", response_model=list[CatLocation])
async def get_locations(
    response: Response,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
) -> list[CatLocation]:
    """Get all cat locations from Supabase (for map display)."""
    response.headers["Cache-Control"] = "public, max-age=300"

    try:
        photos = await gallery_service.get_map_locations()
        if not photos:
            return []
        photos = protect_photo_locations(photos)
        return [CatLocation(**photo) for photo in photos]
    except Exception as e:
        logger.error("Locations fetch error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch cat locations")


# ---- Viewport endpoint ----


@router.get("/viewport", response_model=GalleryResponse)
async def get_locations_in_viewport(
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    north: float = Query(..., description="North latitude bound"),
    south: float = Query(..., description="South latitude bound"),
    east: float = Query(..., description="East longitude bound"),
    west: float = Query(..., description="West longitude bound"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
) -> GalleryResponse:
    """Get cat locations within a geographic viewport (bounding box)."""
    try:
        center_lat = (north + south) / 2
        center_lng = (east + west) / 2
        lat_diff = abs(north - south)
        lng_diff = abs(east - west)
        radius_km = max(lat_diff, lng_diff) * 111 / 2

        photos = await gallery_service.get_nearby_photos(
            latitude=center_lat,
            longitude=center_lng,
            radius_km=max(radius_km, 1.0),
            limit=limit,
        )

        if not photos:
            return GalleryResponse(images=[])

        if current_user:
            photos = await gallery_service.enrich_with_user_data(photos, current_user.id)

        photos = protect_photo_locations(photos)
        cat_locations = [CatLocation(**photo) for photo in photos]
        return GalleryResponse(images=cat_locations)

    except Exception as e:
        logger.error("Viewport fetch error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch locations in viewport")


# ---- Search endpoint ----


@router.get("/search", response_model=SearchResponse)
@limiter.limit(get_api_limit)
async def search_locations(
    request: Request,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    q: str | None = Query(None, description="Text to search in location name and description"),
    tags: str | None = Query(None, description="Comma-separated list of tags to filter by"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    page: int | None = Query(None, ge=1, description="Page number (alternative to offset)"),
    sort: SortField | None = Query(None, description="Sort field"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
) -> SearchResponse:
    """Search cat locations with optional text query and/or tag filters."""
    try:
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        actual_offset = offset
        if page is not None:
            actual_offset = (page - 1) * limit

        photos = await gallery_service.search_photos(
            query=q,
            tags=tag_list,
            limit=limit,
            offset=actual_offset,
            user_id=current_user.id if current_user else None,
        )

        # Apply sorting
        if photos:
            photos = _apply_sort(photos, sort, order)
            photos = protect_photo_locations(photos)

        results = [CatLocation(**photo) for photo in photos] if photos else []

        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
            tags=tag_list,
            limit=limit,
            offset=actual_offset,
        )

    except Exception as e:
        logger.error("Search error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search locations")


# ---- Popular tags endpoint ----


@router.get("/popular-tags", response_model=PopularTagsResponse)
@limiter.limit(get_api_limit)
async def get_popular_tags(
    request: Request,
    response: Response,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    limit: int = Query(20, ge=1, le=100, description="Number of top tags to return"),
) -> PopularTagsResponse:
    """Get the most popular tags used across all cat photos."""
    response.headers["Cache-Control"] = "public, max-age=3600"

    try:
        tags_data = await gallery_service.get_popular_tags(limit=limit)
        tags = [TagInfo(**t) for t in tags_data]
        return PopularTagsResponse(tags=tags)
    except Exception as e:
        logger.error("Popular tags error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch popular tags")


# ---- Single photo endpoint ----


@router.get("/{photo_id}", response_model=CatLocation)
@limiter.limit(get_api_limit)
async def get_photo(
    request: Request,
    photo_id: PhotoIdPath,
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> CatLocation:
    """Get a specific photo by its ID."""
    photo_id_str = str(photo_id)
    try:
        photo = await gallery_service.get_photo_by_id(photo_id_str)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        if current_user and photo:
            enriched = await gallery_service.enrich_with_user_data([photo], current_user.id)
            if enriched:
                photo = enriched[0]

        photo = protect_photo_location(photo)
        return CatLocation(**photo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching photo %s: %s", sanitize_log_value(photo_id_str), e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch photo")


# ---- Delete photo endpoint ----


@router.delete("/{photo_id}", status_code=202)
async def delete_photo(
    photo_id: PhotoIdPath,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
) -> dict[str, str]:
    """Delete a photo. Returns 202 Accepted (deletion runs in background)."""
    photo_id_str = str(photo_id)
    try:
        photo = await gallery_service.verify_photo_ownership(photo_id_str, current_user.id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found or access denied")

        background_tasks.add_task(
            gallery_service.process_photo_deletion,
            photo_id=photo_id_str,
            image_url=photo.get("image_url") or "",
            user_id=current_user.id,
            storage_service=storage_service,
        )

        return {"message": "Deletion scheduled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete request failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule deletion")
