"""Channel model for WhatsApp and Instagram integrations."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import GUID, TenantModel


class ChannelType(str, Enum):
    """Supported messaging channel types."""

    whatsapp = "whatsapp"
    instagram = "instagram"


class Channel(Base, TenantModel):
    """Channel configuration for a tenant.

    Each tenant can have multiple channels (e.g., one WhatsApp, one Instagram).
    Channels store credentials and configuration for the messaging platform.
    """

    __tablename__ = "channels"

    name = Column(String(100), nullable=False)
    channel_type = Column(String(20), nullable=False)  # ChannelType enum value
    is_active = Column(Boolean, default=True, nullable=False)

    # Platform-specific identifiers
    phone_number_id = Column(String(100), nullable=True)  # WhatsApp only
    instagram_page_id = Column(String(100), nullable=True)  # Instagram only

    # Credentials (encrypted in production)
    access_token = Column(Text, nullable=True)  # Platform API token
    webhook_secret = Column(String(255), nullable=True)  # For signature verification

    # Metadata
    config = Column(JSON, nullable=True)  # Additional platform-specific config
    last_webhook_at = Column(DateTime, nullable=True)

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Channel {self.name} ({self.channel_type})>"
