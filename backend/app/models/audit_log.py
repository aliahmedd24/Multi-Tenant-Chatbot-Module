"""Audit log model for tracking tenant operations."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from app.database import Base
from app.models.base import GUID


class AuditLog(Base):
    """Immutable log of actions performed within a tenant.

    Does not use TenantModel mixin because audit logs are append-only
    and don't need updated_at.
    """

    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        GUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
