from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _stringify_uuid(value: str | UUID | None) -> str | None:
    """Normalize UUID objects from DB clients into API-safe string IDs."""
    if isinstance(value, UUID):
        return str(value)
    return value


class GiveTreatRequest(BaseModel):
    photo_id: str
    amount: int = Field(..., ge=1, le=100, description="Number of treats to give (1-100)")


class PurchaseTreatsRequest(BaseModel):
    package: str  # 'small' (5), 'medium' (20), 'large' (50)


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
        return _stringify_uuid(value)


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

    url: str


class TreatPackageInfo(BaseModel):
    """Individual treat package information."""

    name: str
    amount: int
    price: float | None = None
    price_id: str | None = None


class TreatPackagesResponse(BaseModel):
    """Response containing available treat packages."""

    packages: dict[str, TreatPackageInfo] = Field(default_factory=dict)


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
        return _stringify_uuid(value)
