"""
User model for authentication
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from constants.admin_permissions import normalize_permissions


class User(BaseModel):
    id: str
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_pro: bool = False
    stripe_customer_id: str | None = None
    subscription_end_date: datetime | None = None
    cancel_at_period_end: bool = False
    treat_balance: int = 0
    role: str = "user"
    role_id: str | None = None
    permissions: list[str] = Field(default_factory=list)
    banned_at: datetime | None = None

    @field_validator("id", "role_id", mode="before")
    @classmethod
    def stringify_uuid_fields(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return value if isinstance(value, str) else str(value)

    @field_validator("permissions", mode="before")
    @classmethod
    def normalize_permissions_field(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return normalize_permissions(value)
        return []


class UserCreate(BaseModel):
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str
    picture: str | None = None
    bio: str | None = None


class UserCreateWithPassword(BaseModel):
    username: str | None = None
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    """
    Public-facing user representation.

    SEC-04: role_id and permissions are intentionally omitted to avoid
    exposing the internal RBAC structure to clients. Those values are
    embedded in the JWT claims used server-side only.
    """

    id: str
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    is_pro: bool = False
    treat_balance: int = 0
    role: str = "user"
    permissions: list[str] = Field(default_factory=list)
    banned_at: datetime | None = None

    @field_validator("id", mode="before")
    @classmethod
    def stringify_uuid_fields(cls, value: object) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value if isinstance(value, str) else str(value)

    @field_validator("permissions", mode="before")
    @classmethod
    def normalize_permissions_field(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return normalize_permissions(value)
        return []
