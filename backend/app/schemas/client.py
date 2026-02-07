"""Client/Tenant Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClientSettings(BaseModel):
    """Client settings schema."""

    response_tone: str = Field(default="professional", description="AI response tone")
    max_tokens: int = Field(default=500, ge=100, le=4000, description="Max tokens per response")
    language: str = Field(default="en", description="Primary language")
    welcome_message: Optional[str] = Field(default=None, description="Custom welcome message")
    fallback_message: Optional[str] = Field(
        default=None,
        description="Message when AI cannot answer",
    )


class ClientCreate(BaseModel):
    """Schema for creating a new client."""

    name: str = Field(..., min_length=1, max_length=255, description="Business name")
    email: EmailStr = Field(..., description="Primary contact email")
    subscription_tier: str = Field(default="free", description="Subscription tier")
    description: Optional[str] = Field(default=None, description="Business description")
    settings: Optional[ClientSettings] = Field(default=None, description="Client settings")


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    subscription_tier: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[ClientSettings] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    """Schema for client response."""

    id: UUID
    name: str
    slug: str
    email: str
    is_active: bool
    subscription_tier: str
    description: Optional[str]
    settings: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
