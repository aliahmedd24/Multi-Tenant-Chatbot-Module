"""Authentication Pydantic schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str  # User ID
    type: str  # access or refresh
    exp: int  # Expiration timestamp


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(default=None, max_length=255)
    client_id: Optional[UUID] = Field(default=None, description="Associated client ID")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    client_id: Optional[UUID]

    model_config = {"from_attributes": True}
