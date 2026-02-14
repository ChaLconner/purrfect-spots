from pydantic import BaseModel


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    bio: str | None = None
    picture: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdatePhotoRequest(BaseModel):
    location_name: str | None = None
    description: str | None = None
