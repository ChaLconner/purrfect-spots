from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    actor_id: Optional[str] = None
    type: str
    title: Optional[str] = None
    message: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    actor_name: Optional[str] = None
    actor_picture: Optional[str] = None
