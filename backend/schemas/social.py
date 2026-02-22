from datetime import datetime

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
    updated_at: datetime | None = None
    user_name: str | None = None
    user_picture: str | None = None


class LikeResponse(BaseModel):
    liked: bool
    likes_count: int
