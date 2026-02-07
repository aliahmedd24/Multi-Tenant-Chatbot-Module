"""KnowledgeDocument model.

Represents an uploaded document in the knowledge base.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.client import Client


class KnowledgeDocument(Base):
    """Knowledge document model.

    Represents an uploaded document that has been indexed for RAG.
    Bound to a client for tenant isolation.

    Attributes:
        id: Unique identifier (UUID).
        client_id: Foreign key to the owning client (for RLS).
        filename: Original filename.
        document_type: Type of document (menu, faq, policy, general).
        content_hash: SHA-256 hash of content for deduplication.
        chunk_count: Number of chunks created from the document.
        vector_ids: List of vector IDs in the vector store.
        metadata: Additional document metadata.
        created_at: Creation timestamp.
    """

    __tablename__ = "knowledge_documents"

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
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vector_ids: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), default=list
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="knowledge_documents",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<KnowledgeDocument {self.filename} ({self.document_type})>"
