from typing import List

from fastapi import APIRouter, Depends, Query

from dependencies import get_supabase_client
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.notification import NotificationResponse
from services.notification_service import NotificationService
from user_models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def get_notification_service(supabase=Depends(get_supabase_client)):
    return NotificationService(supabase)

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_credentials),
    service: NotificationService = Depends(get_notification_service),
):
    """Get user notifications"""
    return await service.get_notifications(current_user.id, limit, offset)

@router.put("/{id}/read")
async def mark_as_read(
    id: str,
    current_user: User = Depends(get_current_user_from_credentials),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark notification as read"""
    await service.mark_as_read(current_user.id, id)
    return {"status": "success"}

@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user_from_credentials),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read"""
    await service.mark_all_as_read(current_user.id)
    return {"status": "success"}
