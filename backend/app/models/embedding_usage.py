"""Embedding usage log for tracking token consumption per tenant."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String

from app.database import Base
from app.models.base import GUID


class EmbeddingOperation(str, enum.Enum):
    """Types of embedding operations."""

    embed_document = "embed_document"
    embed_query = "embed_query"


class EmbeddingUsageLog(Base):
    """Append-only log of embedding API usage per tenant.

    Does not inherit TenantModel because it is immutable
    (no updated_at needed) and follows the AuditLog pattern.
    """

    __tablename__ = "embedding_usage_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        GUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    operation = Column(Enum(EmbeddingOperation), nullable=False)
    model = Column(String(100), nullable=False)
    token_count = Column(Integer, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
