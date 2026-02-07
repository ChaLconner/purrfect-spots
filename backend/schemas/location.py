from pydantic import BaseModel


class CatLocation(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: str | None = None
    tags: list[str] = []
    likes_count: int = 0
    comments_count: int = 0
    user_id: str | None = None  # Added user_id as well for ownership checks
    liked: bool = False
