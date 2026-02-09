"""Admin (user) request/response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminResponse(BaseModel):
    """Admin user details (excludes password_hash)."""

    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminCreate(BaseModel):
    """Schema for creating a new admin user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., max_length=255)
    role: str = Field(default="viewer", pattern="^(admin|viewer)$")
