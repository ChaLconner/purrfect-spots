from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

class CommentResponse(BaseModel):
    id: str
    user_id: str
    photo_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_picture: Optional[str] = None

class LikeResponse(BaseModel):
    liked: bool
    likes_count: int
