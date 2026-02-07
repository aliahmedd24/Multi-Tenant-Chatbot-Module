"""Knowledge base Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeUpload(BaseModel):
    """Schema for knowledge document upload metadata."""

    document_type: str = Field(
        ...,
        pattern="^(menu|faq|policy|hours|general)$",
        description="Type of document",
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class KnowledgeDocumentResponse(BaseModel):
    """Schema for knowledge document response."""

    id: UUID
    client_id: UUID
    filename: str
    document_type: str
    chunk_count: int
    metadata: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeChunk(BaseModel):
    """Schema for a knowledge chunk."""

    id: str = Field(..., description="Chunk ID")
    text: str = Field(..., description="Chunk text content")
    document_id: UUID = Field(..., description="Parent document ID")
    metadata: Optional[dict] = Field(default=None)


class KnowledgeSearchResult(BaseModel):
    """Schema for knowledge search results."""

    text: str = Field(..., description="Retrieved text")
    score: float = Field(..., description="Similarity score")
    document_type: str = Field(..., description="Source document type")
    metadata: Optional[dict] = Field(default=None)
