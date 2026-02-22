from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    photo_id: UUID
    reason: str = Field(..., description="Reason for reporting (spam, nudity, not_a_cat, etc.)")
    details: str | None = Field(None, description="Additional details provided by the reporter")


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    status: str = Field(..., description="New status (pending, resolved, dismissed)")
    resolution_notes: str | None = None


class ReportResponse(ReportBase):
    id: UUID
    reporter_id: UUID | None
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    resolved_by: UUID | None
    resolution_notes: str | None

    model_config = ConfigDict(from_attributes=True)
