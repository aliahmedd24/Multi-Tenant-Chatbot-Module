"""Pydantic schemas for channel management."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    """Supported channel types."""

    whatsapp = "whatsapp"
    instagram = "instagram"


# -----------------------------------------------------------------------------
# Channel Schemas
# -----------------------------------------------------------------------------


class ChannelCreate(BaseModel):
    """Schema for creating a new channel."""

    name: str = Field(..., min_length=1, max_length=100)
    channel_type: ChannelType
    phone_number_id: Optional[str] = Field(None, description="WhatsApp phone number ID")
    instagram_page_id: Optional[str] = Field(None, description="Instagram page ID")
    access_token: Optional[str] = Field(None, description="Platform API token")
    webhook_secret: Optional[str] = Field(None, description="Webhook signature secret")
    config: Optional[dict] = None


class ChannelUpdate(BaseModel):
    """Schema for updating a channel."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    phone_number_id: Optional[str] = None
    instagram_page_id: Optional[str] = None
    access_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    config: Optional[dict] = None


class ChannelResponse(BaseModel):
    """Schema for channel response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    channel_type: str
    is_active: bool
    phone_number_id: Optional[str] = None
    instagram_page_id: Optional[str] = None
    # Note: access_token is NOT returned for security
    has_webhook_secret: bool = Field(default=False, description="Whether webhook secret is configured")
    config: Optional[dict] = None
    last_webhook_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChannelListResponse(BaseModel):
    """Schema for paginated channel list."""

    channels: list[ChannelResponse]
    total: int


# -----------------------------------------------------------------------------
# Conversation Schemas
# -----------------------------------------------------------------------------


class ConversationStatus(str, Enum):
    """Conversation status."""

    active = "active"
    closed = "closed"
    handoff = "handoff"


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: uuid.UUID
    channel_id: uuid.UUID
    channel_name: Optional[str] = None
    customer_identifier: str
    customer_name: Optional[str] = None
    status: str
    last_message_at: datetime
    message_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""

    conversations: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ConversationDetailResponse(BaseModel):
    """Conversation with full message thread."""

    id: uuid.UUID
    channel_id: uuid.UUID
    channel_name: Optional[str] = None
    customer_identifier: str
    customer_name: Optional[str] = None
    status: str
    last_message_at: datetime
    message_count: int = 0
    created_at: datetime
    messages: list["MessageResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# -----------------------------------------------------------------------------
# Message Schemas
# -----------------------------------------------------------------------------


class MessageDirection(str, Enum):
    """Message direction."""

    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, Enum):
    """Message delivery status."""

    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    content: str
    content_type: str = "text"
    status: str
    external_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """Schema for paginated message list."""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
