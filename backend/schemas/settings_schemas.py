from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ConfigUpdate(BaseModel):
    value: Any
    description: str | None = None
    is_public: bool | None = None
    category: str | None = None
    requires_approval: bool | None = False


class ConfigResponse(BaseModel):
    key: str
    value: Any
    type: str
    description: str | None = None
    category: str
    is_public: bool
    is_encrypted: bool
    requires_approval: bool
    updated_at: datetime
    updated_by: UUID | None = None


class ConfigHistoryResponse(BaseModel):
    id: UUID
    config_key: str
    old_value: Any | None = None
    new_value: Any | None = None
    changed_by: UUID | None = None
    user_email: str | None = None
    change_reason: str | None = None
    created_at: datetime


class PendingConfigChangeResponse(BaseModel):
    id: UUID
    config_key: str
    proposed_value: Any
    current_value: Any | None = None
    requester_id: UUID
    requester_email: str | None = None
    approver_id: UUID | None = None
    status: str
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class PendingActionRequest(BaseModel):
    rejection_reason: str | None = None
