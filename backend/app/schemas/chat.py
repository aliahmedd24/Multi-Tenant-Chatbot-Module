"""Pydantic schemas for chat/RAG endpoints."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=4000)


class SourceDocument(BaseModel):
    """A source document used in the RAG response."""

    document_id: UUID
    filename: str
    chunk_content: str
    relevance_score: float


class UsageMetrics(BaseModel):
    """Token usage metrics for the request."""

    context_chunks: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    response: str
    sources: list[SourceDocument] = []
    usage: UsageMetrics
