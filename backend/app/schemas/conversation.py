"""Conversation and Message Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    sender_id: str = Field(..., min_length=1, description="External sender identifier")
    channel: str = Field(..., pattern="^(whatsapp|instagram|tiktok|snapchat|web)$")
    title: Optional[str] = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID
    client_id: UUID
    sender_id: str
    channel: str
    is_active: bool
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Schema for chat API request."""

    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[UUID] = Field(default=None, description="Existing conversation ID")
    sender_id: str = Field(default="api-user", description="Sender identifier")
    channel: str = Field(default="web", description="Communication channel")


class ChatResponse(BaseModel):
    """Schema for chat API response."""

    message: str = Field(..., description="AI response")
    conversation_id: UUID = Field(..., description="Conversation ID")
    metadata: Optional[dict] = Field(default=None, description="Response metadata")
