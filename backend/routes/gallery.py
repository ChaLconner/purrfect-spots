"""
Gallery routes with API-side pagination support
Enhanced with rate limiting and caching
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response

from dependencies import get_current_token, get_gallery_service
from limiter import limiter
from logger import logger
from middleware.auth_middleware import (
    get_current_user_from_credentials,
    get_current_user_optional,
)
from schemas.location import CatLocation
from services.gallery_service import GalleryService
from user_models.user import User

router = APIRouter(prefix="/gallery", tags=["Gallery"])

from schemas.gallery import (
    GalleryResponse,
    PaginatedGalleryResponse,
    PaginationMeta,
    PopularTagsResponse,
    SearchResponse,
    TagInfo,
)

PhotoIdPath = Annotated[UUID, Path(title="The ID of the photo", description="Must be a valid UUID")]


@router.get(
    "",
    response_model=PaginatedGalleryResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "images": [
                            {
                                "id": "123",
                                "url": "https://example.com/cat.jpg",
                                "latitude": 13.7563,
                                "longitude": 100.5018,
                                "location_name": "Bangkok",
                                "uploaded_at": "2024-03-20T10:00:00Z",
                            }
                        ],
                        "pagination": {
                            "total": 1,
                            "limit": 20,
                            "offset": 0,
                            "has_more": False,
                            "page": 1,
                            "total_pages": 1,
                        },
                    }
                }
            },
        },
        500: {"description": "Internal Server Error"},
    },
)
@router.get("/", response_model=PaginatedGalleryResponse, include_in_schema=False)
@limiter.limit("120/minute")  # Rate limit for paginated endpoint
async def get_gallery(
    request: Request,  # Required for rate limiting
    response: Response,
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    page: int | None = Query(None, ge=1, description="Page number (alternative to offset)"),
    gallery_service: GalleryService = Depends(get_gallery_service),
    current_user: User | None = Depends(get_current_user_optional),
    token: str | None = Depends(get_current_token),
) -> PaginatedGalleryResponse:
    """
    Get cat images with pagination support.

    Pagination can be done via:
    - `offset` + `limit`: Skip N items, return M items
    - `page` + `limit`: Return page N with M items per page (page starts at 1)

    Examples:
    - `/gallery?limit=20&offset=0` - First 20 images
    - `/gallery?limit=20&page=2` - Second page of 20 images
    """
    # Dynamic caching strategy
    if current_user:
        # Authenticated users need data fresh (for 'liked' status)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        logger.info("HTTP Cache-Control set to: no-cache (Authenticated)")
    else:
        # Guests can use cached version
        response.headers["Cache-Control"] = "public, max-age=60"
        logger.info("HTTP Cache-Control set to: public, max-age=60 (Guest)")

    try:
        # Calculate offset from page if provided
        actual_offset = offset
        if page is not None:
            actual_offset = (page - 1) * limit

        logger.info(f"Gallery request: limit={limit}, offset={actual_offset}, page={page}")

        # Call asynchronous service directly
        result = await gallery_service.get_all_photos(
            limit=limit,
            offset=actual_offset,
            include_total=True,
            user_id=current_user.id if current_user else None,
            jwt_token=token if current_user else None,
        )

        if not result["data"]:
            logger.info("No photos found in gallery")
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

        # Calculate pagination metadata
        total = result["total"]
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        current_page = (actual_offset // limit) + 1 if limit > 0 else 1

        cat_locations = [CatLocation(**photo) for photo in result["data"]]

        logger.info(f"Returning {len(cat_locations)} photos, total={total}, page={current_page}/{total_pages}")

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
        logger.error(f"Gallery fetch error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


@router.get("/all", response_model=GalleryResponse)
@limiter.limit("30/minute")  # Lower rate limit for heavy endpoint
async def get_all_gallery(
    request: Request,  # Required for rate limiting
    limit: int = Query(
        1000,
        ge=1,
        le=5000,
        description="Maximum number of images to return (default: 1000)",
    ),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> GalleryResponse:
    """
    Get all cat images with optional limit (use with caution for large datasets).
    For backward compatibility and map display.

    Consider using the paginated `/gallery` endpoint for better performance with large datasets.
    """
    try:
        photos = await gallery_service.get_all_photos_simple(limit=limit)
        if not photos:
            return GalleryResponse(images=[])

        cat_locations = [CatLocation(**photo) for photo in photos]
        return GalleryResponse(images=cat_locations)

    except Exception as e:
        logger.error(f"Gallery fetch error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


@router.get("/locations", response_model=list[CatLocation])
async def get_locations(
    response: Response, gallery_service: GalleryService = Depends(get_gallery_service)
) -> list[CatLocation]:
    """Get all cat locations from Supabase (for map display)."""
    # Cache for 5 minutes (300 seconds)
    response.headers["Cache-Control"] = "public, max-age=300"

    try:
        photos = await gallery_service.get_map_locations()
        if not photos:
            return []

        return [CatLocation(**photo) for photo in photos]

    except Exception as e:
        logger.error(f"Locations fetch error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch cat locations")


@router.get("/viewport", response_model=GalleryResponse)
async def get_locations_in_viewport(
    north: float = Query(..., description="North latitude bound"),
    south: float = Query(..., description="South latitude bound"),
    east: float = Query(..., description="East longitude bound"),
    west: float = Query(..., description="West longitude bound"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    gallery_service: GalleryService = Depends(get_gallery_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> GalleryResponse:
    """
    Get cat locations within a geographic viewport (bounding box).

    This endpoint is optimized for map views that only need to display
    markers within the current visible area.

    Args:
        north: Maximum latitude (top of viewport)
        south: Minimum latitude (bottom of viewport)
        east: Maximum longitude (right of viewport)
        west: Minimum longitude (left of viewport)
        limit: Maximum pins to return (default 100)

    Example:
        `/gallery/viewport?north=13.8&south=13.7&east=100.6&west=100.4`
    """
    try:
        # Calculate center for nearby search
        center_lat = (north + south) / 2
        center_lng = (east + west) / 2

        # Approximate radius in km from viewport size
        lat_diff = abs(north - south)
        lng_diff = abs(east - west)
        radius_km = max(lat_diff, lng_diff) * 111 / 2  # ~111 km per degree

        photos = await gallery_service.get_nearby_photos(
            latitude=center_lat,
            longitude=center_lng,
            radius_km=max(radius_km, 1.0),
            limit=limit,
        )

        if not photos:
            return GalleryResponse(images=[])

        # Enrich with user data (liked status) if authenticated
        if current_user:
            photos = await gallery_service.enrich_with_user_data(photos, current_user.id)

        cat_locations = [CatLocation(**photo) for photo in photos]
        return GalleryResponse(images=cat_locations)

    except Exception as e:
        logger.error(f"Viewport fetch error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch locations in viewport")


@router.get("/search", response_model=SearchResponse)
@limiter.limit("60/minute")  # Rate limit for search
async def search_locations(
    request: Request,  # Required for rate limiting
    q: str | None = Query(None, description="Text to search in location name and description"),
    tags: str | None = Query(None, description="Comma-separated list of tags to filter by"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    page: int | None = Query(None, ge=1, description="Page number (alternative to offset)"),
    gallery_service: GalleryService = Depends(get_gallery_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> SearchResponse:
    """
    Search cat locations with optional text query and/or tag filters.
    """
    try:
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # Calculate offset from page if provided
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

        results = [CatLocation(**photo) for photo in photos] if photos else []

        return SearchResponse(
            results=results, total=len(results), query=q, tags=tag_list, limit=limit, offset=actual_offset
        )

    except Exception as e:
        logger.error(f"Search error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search locations")


@router.get("/popular-tags", response_model=PopularTagsResponse)
@limiter.limit("60/minute")  # Rate limit for tags
async def get_popular_tags(
    request: Request,  # Required for rate limiting
    response: Response,
    limit: int = Query(20, ge=1, le=100, description="Number of top tags to return"),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> PopularTagsResponse:
    """
    Get the most popular tags used across all cat photos.

    Useful for:
    - Tag autocomplete in upload form
    - Tag cloud visualization
    - Quick filter buttons
    """
    # Cache for 1 hour (3600 seconds) - tags change slowly
    response.headers["Cache-Control"] = "public, max-age=3600"

    try:
        tags_data = await gallery_service.get_popular_tags(limit=limit)
        tags = [TagInfo(**t) for t in tags_data]

        return PopularTagsResponse(tags=tags)

    except Exception as e:
        logger.error(f"Popular tags error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch popular tags")


@router.get("/{photo_id}", response_model=CatLocation)
@limiter.limit("60/minute")
async def get_photo(
    request: Request,
    photo_id: PhotoIdPath,
    gallery_service: GalleryService = Depends(get_gallery_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> CatLocation:
    """
    Get a specific photo by its ID.
    Useful for deep linking and sharing.
    """
    photo_id_str = str(photo_id)
    try:
        photo = await gallery_service.get_photo_by_id(photo_id_str)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        # Enrich with liked status if user is authenticated
        if current_user and photo:
            enriched = await gallery_service.enrich_with_user_data([photo], current_user.id)
            if enriched:
                photo = enriched[0]

        return CatLocation(**photo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching photo {photo_id_str}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch photo")


from fastapi import BackgroundTasks

from services.storage_service import storage_service


@router.delete("/{photo_id}", status_code=202)
async def delete_photo(
    photo_id: PhotoIdPath,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_from_credentials),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> dict[str, str]:
    """
    Delete a photo.

    Optimized for performance:
    1. Quick ownership check (fast DB read)
    2. Scheduled background deletion (S3 + DB + Cache)
    3. Returns immediately (202 Accepted)
    """
    photo_id_str = str(photo_id)
    try:
        # 1. Verify ownership quickly
        # We use a lightweight query just to check user_id
        photo = await gallery_service.verify_photo_ownership(photo_id_str, current_user.id)

        if not photo:
            # Check if it exists at all to differentiate 404 from 403
            # But for security/speed, generic 404 or 403 is fine.
            # Let's assume if it's not found with user_id, it's either not yours or doesn't exist.
            # We can do a second check if we want precise error messages, but that slows it down.
            # Let's just say "Photo not found or access denied"
            raise HTTPException(status_code=404, detail="Photo not found or access denied")

        # 2. Schedule background deletion
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
        logger.error(f"Delete request failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule deletion")
