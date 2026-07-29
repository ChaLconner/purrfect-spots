from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class NotificationType(StrEnum):
    LIKE = "like"
    COMMENT = "comment"
    TREAT = "treat"
    SYSTEM = "system"


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    actor_id: str | None = None
    type: NotificationType
    title: str | None = None
    message: str | None = None
    resource_id: str | None = None
    resource_type: str | None = None
    is_read: bool
    created_at: datetime
    actor_name: str | None = None
    actor_picture: str | None = None
