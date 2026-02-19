from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    photo_id: UUID
    reason: str = Field(..., description="Reason for reporting (spam, nudity, not_a_cat, etc.)")
    details: Optional[str] = Field(None, description="Additional details provided by the reporter")


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    status: str = Field(..., description="New status (pending, resolved, dismissed)")
    resolution_notes: Optional[str] = None


class ReportResponse(ReportBase):
    id: UUID
    reporter_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)
