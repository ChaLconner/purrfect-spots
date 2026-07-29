from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _stringify_uuid(value: str | UUID | None) -> str | None:
    """Normalize UUID objects from DB clients into API-safe string IDs."""
    if isinstance(value, UUID):
        return str(value)
    return value


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
    user_is_pro: bool | None = False

    @field_validator("id", "user_id", "photo_id", mode="before")
    @classmethod
    def stringify_uuid_fields(cls, value: str | UUID | None) -> str | None:
        return _stringify_uuid(value)


class LikeResponse(BaseModel):
    liked: bool
    likes_count: int
