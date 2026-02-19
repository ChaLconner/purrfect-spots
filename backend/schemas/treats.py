from datetime import datetime

from pydantic import BaseModel, Field


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


class TreatBalanceResponse(BaseModel):
    balance: int
    recent_transactions: list[TreatTransaction]
