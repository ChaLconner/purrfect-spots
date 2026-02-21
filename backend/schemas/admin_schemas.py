from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserUpdateAdmin(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=255)
    picture: Optional[str] = Field(None, max_length=1000)
    role: Optional[str] = Field(None, pattern="^(user|admin|moderator|super_admin)$")


class RoleUpdateAdmin(BaseModel):
    role_id: str = Field(..., description="UUID of the role")


class PhotoUpdateAdmin(BaseModel):
    location_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class BulkReportUpdate(BaseModel):
    report_ids: List[UUID] = Field(..., min_length=1)
    status: str = Field(..., pattern="^(pending|resolved|dismissed)$")
    resolution_notes: Optional[str] = None
    delete_content: bool = False


class UserBan(BaseModel):
    reason: str = Field(..., min_length=1, max_length=255)
