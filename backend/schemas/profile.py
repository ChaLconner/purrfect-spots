from datetime import datetime
from typing import Any

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


class ProfileData(BaseModel):
    id: str
    email: str
    name: str | None = None
    username: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    is_pro: bool = False


class ProfileUpdateResponse(BaseModel):
    message: str
    user: dict[str, Any]


class ProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None


class PublicProfileResponse(BaseModel):
    id: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    is_pro: bool = False


class UploadsResponse(BaseModel):
    uploads: list[dict[str, Any]]
    count: int


class ProfilePictureResponse(BaseModel):
    message: str
    picture: str


class PasswordChangeResponse(BaseModel):
    message: str


class PhotoUpdateResponse(BaseModel):
    message: str


class PhotoDeleteResponse(BaseModel):
    message: str


class AccountDeletionResponse(BaseModel):
    message: str
