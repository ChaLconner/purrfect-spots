from typing import Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

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
    change_reason: str | None = None
    created_at: datetime

class PendingConfigChangeResponse(BaseModel):
    id: UUID
    config_key: str
    proposed_value: Any
    requester_id: UUID
    approver_id: UUID | None = None
    status: str
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

class PendingActionRequest(BaseModel):
    rejection_reason: str | None = None
