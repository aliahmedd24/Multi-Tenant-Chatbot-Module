"""Pydantic schemas for tenant configuration."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantConfigResponse(BaseModel):
    """Tenant configuration response."""

    id: UUID
    tenant_id: UUID
    business_name: str
    business_hours: Optional[dict] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    custom_instructions: Optional[str] = None
    tone: str
    response_language: str
    allowed_topics: Optional[list] = None
    blocked_topics: Optional[list] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantConfigUpdate(BaseModel):
    """Schema for creating or updating tenant configuration."""

    business_name: str = Field(..., max_length=255)
    business_hours: Optional[dict] = None
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    custom_instructions: Optional[str] = None
    tone: str = Field(default="professional")
    response_language: str = Field(default="en", max_length=10)
    allowed_topics: Optional[list] = None
    blocked_topics: Optional[list] = None


class ConfigValidationResponse(BaseModel):
    """Response for configuration validation check."""

    is_valid: bool
    missing_fields: list[str]
    warnings: list[str]
