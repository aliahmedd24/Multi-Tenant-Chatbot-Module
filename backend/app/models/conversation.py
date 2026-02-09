"""Conversation model for tracking customer interactions."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import GUID, TenantModel


class ConversationStatus(str, Enum):
    """Conversation status states."""

    active = "active"
    closed = "closed"
    handoff = "handoff"  # Escalated to human agent


class Conversation(Base, TenantModel):
    """Conversation thread with a customer.

    Tracks the ongoing interaction between a customer and the AI/agent
    across a specific channel.
    """

    __tablename__ = "conversations"

    channel_id = Column(
        GUID(),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # External platform identifiers
    external_id = Column(String(255), nullable=True)  # Platform conversation ID
    customer_identifier = Column(String(255), nullable=False)  # Phone or username
    customer_name = Column(String(255), nullable=True)

    # Status tracking
    status = Column(String(20), default=ConversationStatus.active.value, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Metadata
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string for flexibility

    # Relationships
    channel = relationship("Channel", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.customer_identifier} ({self.status})>"
