"""Base model mixins for multi-tenant architecture."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses String(36) as the underlying storage, so it works with both
    PostgreSQL and SQLite (for tests).
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value


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

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        GUID(),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
        doc="Tenant identifier for data isolation",
    )
