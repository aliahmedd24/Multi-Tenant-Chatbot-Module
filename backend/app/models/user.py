"""User (tenant admin) model."""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import GUID, TenantModel


class UserRole(str, enum.Enum):
    """Roles available to tenant users."""

    owner = "owner"
    admin = "admin"
    viewer = "viewer"


class User(Base, TenantModel):
    """A user who administers a tenant's account.

    Inherits tenant_id, id, created_at, updated_at from TenantModel.
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", foreign_keys="[User.tenant_id]", lazy="joined")
