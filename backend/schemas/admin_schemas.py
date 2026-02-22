from uuid import UUID

from pydantic import BaseModel, Field


class UserUpdateAdmin(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=255)
    picture: str | None = Field(None, max_length=1000)
    role: str | None = Field(None, pattern="^(user|admin|moderator|super_admin)$")


class RoleUpdateAdmin(BaseModel):
    role_id: str = Field(..., description="UUID of the role")


class PhotoUpdateAdmin(BaseModel):
    location_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class BulkReportUpdate(BaseModel):
    report_ids: list[UUID] = Field(..., min_length=1)
    status: str = Field(..., pattern="^(pending|resolved|dismissed)$")
    resolution_notes: str | None = None
    delete_content: bool = False


class UserBan(BaseModel):
    reason: str = Field(..., min_length=1, max_length=255)
