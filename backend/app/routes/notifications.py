from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_notification_service
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse
from app.schemas.user import User
from app.services.notification_service import NotificationService, _is_valid_uuid

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    before: str | None = Query(None, max_length=64),
) -> list[NotificationResponse]:
    """Get user notifications."""
    return cast(list[NotificationResponse], await service.get_notifications(current_user.id, limit, offset, before))


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationUnreadCountResponse:
    """Get count of unread notifications for current user."""
    count = await service.get_unread_count(current_user.id)
    return NotificationUnreadCountResponse(unread_count=count)


@router.put("/{id}/read", response_model=MessageResponse)
async def mark_as_read(
    id: str,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> MessageResponse:
    """Mark notification as read."""
    if not _is_valid_uuid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid notification ID format")
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
