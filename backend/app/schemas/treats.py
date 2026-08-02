from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.db_security import stringify_uuid


class GiveTreatRequest(BaseModel):
    photo_id: str
    amount: int = Field(..., ge=1, le=100, description="Number of treats to give (1-100)")


class PurchaseTreatsRequest(BaseModel):
    package: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Package identifier (e.g. 'small', 'medium', 'large')",
    )


class TreatTransaction(BaseModel):
    id: str
    amount: int
    transaction_type: str
    created_at: datetime
    photo_id: str | None = None
    from_user_id: str | None = None
    to_user_id: str | None = None

    @field_validator("id", "photo_id", "from_user_id", "to_user_id", mode="before")
    @classmethod
    def stringify_uuid_fields(cls, value: str | UUID | None) -> str | None:
        return stringify_uuid(value)


class TreatBalanceResponse(BaseModel):
    balance: int
    recent_transactions: list[TreatTransaction]


class GiveTreatResponse(BaseModel):
    """Response for giving treats to a photo owner."""

    message: str
    new_balance: int | None = None
    amount_given: int | None = None


class CheckoutUrlResponse(BaseModel):
    """Response containing a Stripe checkout URL."""

    checkout_url: str = ""
    url: str = ""
    session_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_url_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            url_val = data.get("checkout_url") or data.get("url") or ""
            data["checkout_url"] = url_val
            data["url"] = url_val
        return data


class TreatPackageInfo(BaseModel):
    """Individual treat package information."""

    name: str
    amount: int
    price: float | None = None
    price_id: str | None = None


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""

    id: str
    name: str | None = None
    username: str | None = None
    picture: str | None = None
    total_treats_received: int = 0

    @field_validator("id", mode="before")
    @classmethod
    def stringify_uuid_field(cls, value: str | UUID | None) -> str | None:
        return stringify_uuid(value)
