from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.db_security import stringify_uuid


class CatLocation(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: datetime | str | None = None
    tags: list[str] = Field(default_factory=list)
    likes_count: int = 0
    comments_count: int = 0
    user_id: str | None = None  # Added user_id as well for ownership checks
    liked: bool = False

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def stringify_uuid_fields(cls, value: str | UUID | None) -> str | None:
        """Normalize UUID objects from DB clients into API-safe string IDs."""
        return stringify_uuid(value)
