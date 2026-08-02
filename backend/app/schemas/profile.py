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


class BaseProfile(BaseModel):
    id: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    is_pro: bool = False


class PublicProfileResponse(BaseProfile):
    pass


class ProfileResponse(BaseProfile):
    email: str
    username: str | None = None


class BaseMessageResponse(BaseModel):
    message: str


class ProfileUpdateResponse(BaseModel):
    message: str
    user: dict[str, Any]


class UploadsResponse(BaseModel):
    uploads: list[dict[str, Any]]
    count: int


class PublicProfileBundleResponse(BaseModel):
    profile: PublicProfileResponse
    uploads: list[dict[str, Any]]
    count: int


class ProfilePictureResponse(BaseMessageResponse):
    picture: str


class PasswordChangeResponse(BaseMessageResponse):
    pass


class PhotoUpdateResponse(BaseMessageResponse):
    pass


class PhotoDeleteResponse(BaseMessageResponse):
    pass


class AccountDeletionResponse(BaseMessageResponse):
    pass
