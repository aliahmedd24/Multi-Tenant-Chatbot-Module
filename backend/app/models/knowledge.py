"""Knowledge base models - documents and chunks for RAG pipeline."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import GUID, TenantModel


class FileType(str, enum.Enum):
    """Supported file types for knowledge base uploads."""

    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    csv = "csv"
    json = "json"


class DocumentStatus(str, enum.Enum):
    """Processing status of a knowledge document."""

    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class KnowledgeDocument(Base, TenantModel):
    """A document uploaded to a tenant's knowledge base.

    Inherits id, tenant_id, created_at, updated_at from TenantModel.
    """

    __tablename__ = "knowledge_documents"

    filename = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    status = Column(
        Enum(DocumentStatus), default=DocumentStatus.uploading, nullable=False
    )
    processing_error = Column(Text, nullable=True)
    uploaded_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    uploader = relationship("User", foreign_keys=[uploaded_by], lazy="joined")


class KnowledgeChunk(Base, TenantModel):
    """A text chunk from a processed knowledge document.

    Inherits id, tenant_id, created_at, updated_at from TenantModel.
    Tenant_id is denormalized here for direct isolation queries.
    """

    __tablename__ = "knowledge_chunks"

    document_id = Column(
        GUID(),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(255), nullable=True)
    token_count = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="chunks")
