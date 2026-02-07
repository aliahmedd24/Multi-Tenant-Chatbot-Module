"""ChannelConfig model.

Stores channel-specific configuration for each client.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.client import Client


class ChannelConfig(Base):
    """Channel configuration model.

    Stores API credentials and settings for each channel per client.

    Attributes:
        id: Unique identifier (UUID).
        client_id: Foreign key to the owning client.
        channel: Channel type (whatsapp, instagram, tiktok, snapchat).
        config: Channel-specific configuration (tokens, IDs, etc.).
        is_active: Whether this channel is active.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "channel_configs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    client_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="channel_configs",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ChannelConfig {self.channel} for client {self.client_id}>"
