"""Tenant request/response schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantResponse(BaseModel):
    """Tenant details returned to authenticated users."""

    id: UUID
    name: str
    slug: str
    is_active: bool
    subscription_tier: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantUpdate(BaseModel):
    """Fields that can be updated on a tenant."""

    name: Optional[str] = Field(None, max_length=255)
    settings: Optional[dict[str, Any]] = None
