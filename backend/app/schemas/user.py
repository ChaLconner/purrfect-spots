"""
User model for authentication
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.constants.admin_permissions import normalize_permissions
from app.schemas.profile import BaseProfile


class UserBase(BaseProfile):
    username: str | None = None
    google_id: str | None = None
    email: str
    treat_balance: int = 0
    role: str = "user"
    permissions: list[str] = Field(default_factory=list)
    banned_at: datetime | None = None

    @field_validator("id", mode="before")
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


class User(UserBase):
    updated_at: datetime | None = None
    stripe_customer_id: str | None = None
    subscription_end_date: datetime | None = None
    cancel_at_period_end: bool = False
    role_id: str | None = None

    @field_validator("role_id", mode="before")
    @classmethod
    def stringify_role_id(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return value if isinstance(value, str) else str(value)


class UserResponse(UserBase):
    """
    Public-facing user representation.

    SEC-04: role_id is intentionally omitted to avoid exposing the
    internal RBAC structure to clients.  The ``permissions`` list IS
    included because the frontend admin panel reads it to gate UI
    access (no JWT decode on the client side).  Server-side
    authorization still relies exclusively on JWT claims.
    """
