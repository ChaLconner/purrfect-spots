from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_notification_service
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationResponse
from app.schemas.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
) -> list[NotificationResponse]:
    """Get user notifications."""
    return cast(list[NotificationResponse], await service.get_notifications(current_user.id, limit, offset))


@router.put("/{id}/read", response_model=MessageResponse)
async def mark_as_read(
    id: str,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> MessageResponse:
    """Mark notification as read."""
    await service.mark_as_read(current_user.id, id)
    return MessageResponse(message="Notification marked as read")


@router.put("/read-all", response_model=MessageResponse)
async def mark_all_as_read(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> MessageResponse:
    """Mark all notifications as read."""
    await service.mark_all_as_read(current_user.id)
    return MessageResponse(message="All notifications marked as read")
