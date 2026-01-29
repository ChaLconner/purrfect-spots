"""
Gallery routes with API-side pagination support
Enhanced with rate limiting and caching
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from dependencies import get_supabase_client
from limiter import limiter
from logger import logger
from schemas.location import CatLocation
from services.gallery_service import GalleryService

router = APIRouter(prefix="/gallery", tags=["Gallery"])

from schemas.gallery import (
    GalleryResponse,
    PaginatedGalleryResponse,
    PaginationMeta,
    PopularTagsResponse,
    SearchResponse,
    TagInfo,
)


def get_gallery_service(supabase=Depends(get_supabase_client)) -> GalleryService:
    return GalleryService(supabase)


@router.get("/", response_model=PaginatedGalleryResponse)
@limiter.limit("120/minute")  # Rate limit for paginated endpoint
async def get_gallery(
    request: Request,  # Required for rate limiting
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    page: int | None = Query(None, ge=1, description="Page number (alternative to offset)"),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get cat images with pagination support.

    Pagination can be done via:
    - `offset` + `limit`: Skip N items, return M items
    - `page` + `limit`: Return page N with M items per page (page starts at 1)

    Examples:
    - `/gallery?limit=20&offset=0` - First 20 images
    - `/gallery?limit=20&page=2` - Second page of 20 images
    """
    try:
        # Calculate offset from page if provided
        actual_offset = offset
        if page is not None:
            actual_offset = (page - 1) * limit

        # Run synchronous service call in threadpool to avoid blocking event loop
        result = await run_in_threadpool(
            gallery_service.get_all_photos, 
            limit=limit, 
            offset=actual_offset, 
            include_total=True
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

        # Calculate pagination metadata
        total = result["total"]
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        current_page = (actual_offset // limit) + 1 if limit > 0 else 1

        cat_locations = [CatLocation(**photo) for photo in result["data"]]

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
):
    """
    Get all cat images with optional limit (use with caution for large datasets).
    For backward compatibility and map display.

    Consider using the paginated `/gallery` endpoint for better performance with large datasets.
    """
    try:
        photos = await run_in_threadpool(gallery_service.get_all_photos_simple, limit=limit)
        if not photos:
            return GalleryResponse(images=[])

        cat_locations = [CatLocation(**photo) for photo in photos]
        return GalleryResponse(images=cat_locations)

    except Exception as e:
        logger.error(f"Gallery fetch error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


@router.get("/locations", response_model=list[CatLocation])
async def get_locations(
    response: Response,
    gallery_service: GalleryService = Depends(get_gallery_service)
):
    """Get all cat locations from Supabase (for map display)."""
    # Cache for 5 minutes (300 seconds)
    response.headers["Cache-Control"] = "public, max-age=300"
    
    try:
        photos = await run_in_threadpool(gallery_service.get_map_locations)
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
):
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

        photos = await run_in_threadpool(
            gallery_service.get_nearby_photos,
            latitude=center_lat,
            longitude=center_lng,
            radius_km=max(radius_km, 1.0),
            limit=limit,
        )

        if not photos:
            return GalleryResponse(images=[])

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
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Search cat locations with optional text query and/or tag filters.

    Examples:
    - `/gallery/search?q=park` - Search for "park" in name or description
    - `/gallery/search?tags=orange,sleeping` - Filter by tags
    - `/gallery/search?q=sunny&tags=cute` - Combined search
    """
    try:
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        photos = await run_in_threadpool(
            gallery_service.search_photos,
            query=q,
            tags=tag_list,
            limit=limit
        )

        results = [CatLocation(**photo) for photo in photos] if photos else []

        return SearchResponse(results=results, total=len(results), query=q, tags=tag_list)

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
):
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
        tags_data = await run_in_threadpool(gallery_service.get_popular_tags, limit=limit)
        tags = [TagInfo(**t) for t in tags_data]

        return PopularTagsResponse(tags=tags)

    except Exception as e:
        logger.error(f"Popular tags error: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch popular tags")


@router.get("/{photo_id}", response_model=CatLocation)
@limiter.limit("60/minute")
async def get_photo(
    request: Request,
    photo_id: str,
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get a specific photo by its ID.
    Useful for deep linking and sharing.
    """
    try:
        photo = await run_in_threadpool(gallery_service.get_photo_by_id, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        return CatLocation(**photo)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching photo {photo_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch photo")
