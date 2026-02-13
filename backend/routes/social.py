from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from dependencies import get_supabase_admin_client
from exceptions import ExternalServiceError, NotFoundError
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.social import CommentCreate, CommentResponse, LikeResponse
from services.social_service import SocialService
from user_models.user import User
from services.subscription_service import SubscriptionService
from user_models.user import User
from utils.rate_limiter import like_rate_limiter

router = APIRouter(prefix="/social", tags=["Social"])


def get_social_service(supabase: Client = Depends(get_supabase_admin_client)) -> SocialService:
    # Use admin client to bypass RLS - user authentication is handled by middleware
    return SocialService(supabase)


def get_subscription_service(supabase: Client = Depends(get_supabase_admin_client)) -> SubscriptionService:
    # Use admin client to ensure we can update user subscription status securely
    return SubscriptionService(supabase)


@router.post("/photos/{photo_id}/like", response_model=LikeResponse)
async def toggle_like(
    photo_id: str,
    current_user: User = Depends(get_current_user_from_credentials),
    social_service: SocialService = Depends(get_social_service),
) -> dict[str, Any]:
    """
    Toggle like on a photo.
    
    Uses atomic database function to prevent race conditions.
    Returns the new liked status and updated likes count.
    Rate limited to 10 requests per 10 seconds per user.
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


@router.post("/photos/{photo_id}/comments", response_model=CommentResponse)
async def add_comment(
    photo_id: str,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user_from_credentials),
    social_service: SocialService = Depends(get_social_service),
) -> dict[str, Any]:
    """Add a comment to a photo."""
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


@router.get("/photos/{photo_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    photo_id: str,
    social_service: SocialService = Depends(get_social_service),
) -> List[dict[str, Any]]:
    """Get comments for a photo."""
    try:
        return await social_service.get_comments(photo_id)
    except Exception as e:
        logger.error(f"Get comments failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments")


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user_from_credentials),
    social_service: SocialService = Depends(get_social_service),
) -> dict[str, str]:
    """Delete a comment."""
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
