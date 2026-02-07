"""Client (Tenant) model.

Represents a business/tenant in the multi-tenant system.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.channel_config import ChannelConfig
    from app.models.conversation import Conversation
    from app.models.knowledge_document import KnowledgeDocument


class Client(Base):
    """Client/Tenant model.

    Represents a business customer using the AI concierge platform.
    Each client has isolated data through Row-Level Security.

    Attributes:
        id: Unique identifier (UUID).
        name: Business name.
        slug: URL-friendly unique identifier.
        email: Primary contact email.
        is_active: Whether the client is active.
        subscription_tier: Subscription level (free, basic, premium, enterprise).
        settings: JSONB settings (response_tone, max_tokens, language, etc.).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="client",
        cascade="all, delete-orphan",
    )
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="client",
        cascade="all, delete-orphan",
    )
    channel_configs: Mapped[list["ChannelConfig"]] = relationship(
        "ChannelConfig",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Client {self.slug} ({self.id})>"

    @property
    def response_tone(self) -> str:
        """Get configured response tone."""
        return self.settings.get("response_tone", "professional") if self.settings else "professional"

    @property
    def max_tokens(self) -> int:
        """Get configured max tokens for LLM responses."""
        return self.settings.get("max_tokens", 500) if self.settings else 500

    @property
    def language(self) -> str:
        """Get configured primary language."""
        return self.settings.get("language", "en") if self.settings else "en"
