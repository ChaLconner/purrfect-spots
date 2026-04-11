from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from dependencies import (
    get_current_token,
    get_social_service,
)
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.common import MessageResponse
from schemas.social import CommentCreate, CommentResponse, CommentUpdate, LikeResponse
from schemas.user import User
from services.social_service import SocialService
from utils.action_throttle import like_rate_limiter
from utils.exceptions import ExternalServiceError, NotFoundError

router = APIRouter(prefix="/social", tags=["Social"])


def _validate_uuid_param(value: str, field_name: str) -> None:
    try:
        UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


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
) -> LikeResponse:
    """
    Toggle like on a photo.

    Uses atomic database function to prevent race conditions.
    Returns the new liked status and updated likes count.
    Rate limited to 10 requests per 10 seconds per user.
    """
    _validate_uuid_param(photo_id, "photo_id")
    if not await like_rate_limiter.is_allowed(f"like:{current_user.id}"):
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")

    try:
        result = await social_service.toggle_like(current_user.id, photo_id)
        return LikeResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        logger.error("Like failed (service error): %s", e)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error("Like failed (unexpected): %s", e)
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
) -> CommentResponse:
    """Add a comment to a photo."""
    _validate_uuid_param(photo_id, "photo_id")
    try:
        result = await social_service.add_comment(current_user.id, photo_id, comment.content)
        return CommentResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        logger.error("Comment failed (service error): %s", e)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error("Comment failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to post comment")


@router.get(
    "/photos/{photo_id}/comments",
    response_model=list[CommentResponse],
    responses={500: {"description": "Internal Server Error"}},
)
async def get_comments(
    photo_id: str,
    social_service: Annotated[SocialService, Depends(get_social_service)],
) -> list[CommentResponse]:
    """Get comments for a photo."""
    _validate_uuid_param(photo_id, "photo_id")
    try:
        results = await social_service.get_comments(photo_id)
        return [CommentResponse(**c) for c in results]
    except Exception as e:
        logger.error("Get comments failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get comments")


@router.delete(
    "/comments/{comment_id}",
    response_model=MessageResponse,
    responses={403: {"description": "Forbidden"}, 500: {"description": "Internal Server Error"}},
)
async def delete_comment(
    comment_id: str,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    social_service: Annotated[SocialService, Depends(get_social_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> MessageResponse:
    """Delete a comment."""
    _validate_uuid_param(comment_id, "comment_id")
    try:
        success = await social_service.delete_comment(current_user.id, comment_id)
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized or comment not found")
        return MessageResponse(message="Comment deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete comment failed: %s", e)
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
) -> CommentResponse:
    """Update an existing comment."""
    _validate_uuid_param(comment_id, "comment_id")
    try:
        updated_comment = await social_service.update_comment(
            user_id=current_user.id,
            comment_id=comment_id,
            content=comment.content,
        )
        if not updated_comment:
            raise HTTPException(status_code=403, detail="Not authorized or comment not found")
        return CommentResponse(**updated_comment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update comment failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update comment")
