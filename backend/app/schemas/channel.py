"""Channel configuration Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WhatsAppConfig(BaseModel):
    """WhatsApp-specific configuration."""

    phone_number_id: str = Field(..., description="WhatsApp phone number ID")
    access_token: str = Field(..., description="Graph API access token")
    business_account_id: Optional[str] = Field(default=None)


class InstagramConfig(BaseModel):
    """Instagram-specific configuration."""

    page_id: str = Field(..., description="Instagram page ID")
    access_token: str = Field(..., description="Graph API access token")


class ChannelConfigCreate(BaseModel):
    """Schema for creating channel configuration."""

    channel: str = Field(
        ...,
        pattern="^(whatsapp|instagram|tiktok|snapchat)$",
        description="Channel type",
    )
    config: dict = Field(..., description="Channel-specific configuration")
    is_active: bool = Field(default=True)


class ChannelConfigUpdate(BaseModel):
    """Schema for updating channel configuration."""

    config: Optional[dict] = None
    is_active: Optional[bool] = None


class ChannelConfigResponse(BaseModel):
    """Schema for channel configuration response."""

    id: UUID
    client_id: UUID
    channel: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
