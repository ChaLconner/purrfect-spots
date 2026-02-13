from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class NotificationType(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    TREAT = "treat"
    SYSTEM = "system"


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    actor_id: Optional[str] = None
    type: NotificationType
    title: Optional[str] = None
    message: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    actor_name: Optional[str] = None
    actor_picture: Optional[str] = None
