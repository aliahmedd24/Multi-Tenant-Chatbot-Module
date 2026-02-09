"""Tenant configuration model for AI bot behavior."""

import enum

from sqlalchemy import Column, Enum, JSON, String, Text, UniqueConstraint

from app.database import Base
from app.models.base import TenantModel


class ToneType(str, enum.Enum):
    """Available tone settings for the AI bot."""

    formal = "formal"
    casual = "casual"
    friendly = "friendly"
    professional = "professional"


class TenantConfiguration(Base, TenantModel):
    """Configuration for a tenant's AI bot behavior.

    One-to-one relationship with Tenant (enforced by unique constraint).
    Inherits id, tenant_id, created_at, updated_at from TenantModel.
    """

    __tablename__ = "tenant_configurations"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_configurations_tenant_id"),
    )

    business_name = Column(String(255), nullable=False)
    business_hours = Column(JSON, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    custom_instructions = Column(Text, nullable=True)
    tone = Column(Enum(ToneType), default=ToneType.professional, nullable=False)
    response_language = Column(String(10), default="en", nullable=False)
    allowed_topics = Column(JSON, nullable=True)
    blocked_topics = Column(JSON, nullable=True)
