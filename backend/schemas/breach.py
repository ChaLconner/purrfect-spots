"""
Breach notification schemas.
"""

from pydantic import BaseModel, Field


class BreachReport(BaseModel):
    """Model for reporting a suspected data breach."""

    breach_type: str = Field(
        ..., description="Type of breach (unauthorized_access, data_leak, account_compromise, system_intrusion)"
    )
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of the breach")
    affected_users: list[str] | None = Field(None, description="List of affected user IDs")
    severity: str = Field(default="medium", description="Severity level (low, medium, high, critical)")


class BreachStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (investigating, contained, resolved, false_positive)")
    notes: str | None = None
