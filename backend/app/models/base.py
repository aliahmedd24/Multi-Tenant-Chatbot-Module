"""Base model mixins for multi-tenant architecture."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TenantModel(TimestampMixin):
    """Base mixin for all tenant-scoped models.

    Every model that stores tenant data MUST inherit from this mixin
    to ensure tenant_id is always present and indexed.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        String(36), nullable=False, index=True, doc="Tenant identifier for data isolation"
    )
