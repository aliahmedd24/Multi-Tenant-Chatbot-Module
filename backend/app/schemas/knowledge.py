"""Pydantic schemas for knowledge base documents and chunks."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.knowledge import DocumentStatus, FileType


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    id: UUID
    filename: str
    file_type: FileType
    file_size_bytes: int
    status: DocumentStatus
    message: str = "Document uploaded and queued for processing"

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    """Individual text chunk from a document."""

    id: UUID
    chunk_index: int
    content: str
    token_count: int
    metadata: Optional[dict] = Field(default=None, alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentResponse(BaseModel):
    """Full document details."""

    id: UUID
    filename: str
    file_type: FileType
    file_size_bytes: int
    status: DocumentStatus
    processing_error: Optional[str] = None
    chunk_count: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Optional[dict] = Field(default=None, alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
