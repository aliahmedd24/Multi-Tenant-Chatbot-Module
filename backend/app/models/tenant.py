"""Tenant model - represents a client organization."""

import enum
import uuid

from sqlalchemy import Boolean, Column, Enum, JSON, String

from app.database import Base
from app.models.base import GUID, TimestampMixin


class SubscriptionTier(str, enum.Enum):
    """Available subscription tiers."""

    free = "free"
    basic = "basic"
    premium = "premium"


class Tenant(Base, TimestampMixin):
    """A tenant (client organization) in the multi-tenant system.

    This is the top-level entity. All other data models reference
    a tenant via tenant_id foreign key.
    """

    __tablename__ = "tenants"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(
        Enum(SubscriptionTier), default=SubscriptionTier.free, nullable=False
    )
    settings = Column(JSON, default=dict, nullable=False)
