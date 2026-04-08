"""
Consent management schemas.
"""

from pydantic import BaseModel, Field


class ConsentRecord(BaseModel):
    consent_type: str = Field(..., description="Type of consent (tos, privacy, marketing, data_processing, cookies)")
    granted: bool = Field(..., description="Whether consent was granted")
    ip_address: str | None = Field(None, description="IP address when consent was given")
    user_agent: str | None = Field(None, description="User agent when consent was given")
