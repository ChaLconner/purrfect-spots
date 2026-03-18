from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from dependencies import (
    get_current_token,
    get_social_service,
)
from exceptions import ExternalServiceError, NotFoundError
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.social import CommentCreate, CommentResponse, CommentUpdate, LikeResponse
from schemas.user import User
from services.social_service import SocialService
from utils.action_throttle import like_rate_limiter

router = APIRouter(prefix="/social", tags=["Social"])


@router.post(
    "/photos/{photo_id}/like",
    response_model=LikeResponse,
    responses={
        404: {"description": "Photo not found"},
        429: {"description": "Too many requests"},
        500: {"description": "Internal Server Error"},
        503: {"description": "Service unavailable"},
    },
)
async def toggle_like(
    photo_id: str,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    social_service: Annotated[SocialService, Depends(get_social_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> dict[str, Any]:
    """
    Toggle like on a photo.

    Uses atomic database function to prevent race conditions.
    Returns the new liked status and updated likes count.
    Rate limited to 10 requests per 10 seconds per user.

    Raises:
        HTTPException: 404 - If the photo is not found.
        HTTPException: 429 - If the rate limit is exceeded.
        HTTPException: 500 - If toggle like fails due to an unexpected error.
        HTTPException: 503 - If the service is temporarily unavailable.
    """
    # Rate limit per user
    if not await like_rate_limiter.is_allowed(f"like:{current_user.id}"):
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")

    try:
        return await social_service.toggle_like(current_user.id, photo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        logger.error(f"Like failed (service error): {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Like failed (unexpected): {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle like")


@router.post(
    "/photos/{photo_id}/comments",
    response_model=CommentResponse,
    responses={
        404: {"description": "Photo not found"},
        500: {"description": "Internal Server Error"},
        503: {"description": "Service unavailable"},
    },
)
async def add_comment(
    photo_id: str,
    comment: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    social_service: Annotated[SocialService, Depends(get_social_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> dict[str, Any]:
    """
    Add a comment to a photo.

    Raises:
        HTTPException: 404 - If the photo is not found.
        HTTPException: 500 - If posting a comment fails due to an internal error.
        HTTPException: 503 - If the service is temporarily unavailable.
    """
    try:
        return await social_service.add_comment(current_user.id, photo_id, comment.content)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        logger.error(f"Comment failed (service error): {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Comment failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to post comment")


@router.get(
    "/photos/{photo_id}/comments",
    response_model=list[CommentResponse],
    responses={500: {"description": "Internal Server Error"}},
)
async def get_comments(
    photo_id: str,
    social_service: Annotated[SocialService, Depends(get_social_service)],
) -> list[dict[str, Any]]:
    """
    Get comments for a photo.

    Raises:
        HTTPException: 500 - If fetching comments fails.
    """
    try:
        return await social_service.get_comments(photo_id)
    except Exception as e:
        logger.error(f"Get comments failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments")


@router.delete(
    "/comments/{comment_id}",
    responses={403: {"description": "Forbidden"}, 500: {"description": "Internal Server Error"}},
)
async def delete_comment(
    comment_id: str,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    social_service: Annotated[SocialService, Depends(get_social_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> dict[str, str]:
    """
    Delete a comment.

    Raises:
        HTTPException: 403 - If the user is not authorized or the comment is not found.
        HTTPException: 500 - If deleting the comment fails.
    """
    try:
        success = await social_service.delete_comment(current_user.id, comment_id)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or comment not found")
        return {"message": "Comment deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete comment failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    responses={403: {"description": "Forbidden"}, 500: {"description": "Internal Server Error"}},
)
async def update_comment(
    comment_id: str,
    comment: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    social_service: Annotated[SocialService, Depends(get_social_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> dict[str, Any]:
    """
    Update an existing comment.

    Raises:
        HTTPException: 403 - If the user is not authorized or the comment is not found.
        HTTPException: 500 - If updating the comment fails.
    """
    try:
        updated_comment = await social_service.update_comment(
            user_id=current_user.id,
            comment_id=comment_id,
            content=comment.content,
        )
        if not updated_comment:
            raise HTTPException(status_code=403, detail="Not authorized or comment not found")
        return updated_comment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update comment failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment")
