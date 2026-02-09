"""Message model for individual messages in conversations."""

from enum import Enum

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import GUID, TenantModel


class MessageDirection(str, Enum):
    """Message direction (inbound from customer, outbound to customer)."""

    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, Enum):
    """Message delivery status."""

    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class Message(Base, TenantModel):
    """Individual message in a conversation.

    Stores both inbound (customer) and outbound (AI/agent) messages
    with delivery status tracking.
    """

    __tablename__ = "messages"

    conversation_id = Column(
        GUID(),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    direction = Column(String(20), nullable=False)  # MessageDirection
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text", nullable=False)  # text, image, etc.

    # External platform identifiers
    external_id = Column(String(255), nullable=True)  # Platform message ID

    # Status tracking
    status = Column(String(20), default=MessageStatus.pending.value, nullable=False)
    error_message = Column(Text, nullable=True)  # If status is 'failed'

    # Metadata (platform-specific data as JSON string)
    metadata_ = Column("metadata", Text, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.direction} ({self.status})>"
