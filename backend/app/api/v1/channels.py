"""Channel management API endpoints.

Protected endpoints for tenant admins to manage channel configurations.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.channel import Channel
from app.models.user import User
from app.schemas.channel import (
    ChannelCreate,
    ChannelListResponse,
    ChannelResponse,
    ChannelUpdate,
)
from app.services.audit import log_action

router = APIRouter()


def _channel_to_response(channel: Channel) -> ChannelResponse:
    """Convert Channel model to response schema."""
    return ChannelResponse(
        id=channel.id,
        tenant_id=channel.tenant_id,
        name=channel.name,
        channel_type=channel.channel_type,
        is_active=channel.is_active,
        phone_number_id=channel.phone_number_id,
        instagram_page_id=channel.instagram_page_id,
        has_webhook_secret=bool(channel.webhook_secret),
        config=channel.config,
        last_webhook_at=channel.last_webhook_at,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


@router.post("", response_model=ChannelResponse, status_code=201)
def create_channel(
    data: ChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new channel configuration.

    Only tenant admins can create channels.
    """
    # Check if channel with same type already exists for tenant
    existing = (
        db.query(Channel)
        .filter(
            Channel.tenant_id == current_user.tenant_id,
            Channel.channel_type == data.channel_type.value,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Channel of type '{data.channel_type}' already exists for this tenant",
        )

    channel = Channel(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=data.name,
        channel_type=data.channel_type.value,
        phone_number_id=data.phone_number_id,
        instagram_page_id=data.instagram_page_id,
        access_token=data.access_token,
        webhook_secret=data.webhook_secret,
        config=data.config,
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="channel_create",
        resource_type="channel",
        resource_id=str(channel.id),
        details={"name": channel.name, "type": channel.channel_type},
    )

    return _channel_to_response(channel)


@router.get("", response_model=ChannelListResponse)
def list_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all channels for the current tenant."""
    channels = (
        db.query(Channel)
        .filter(Channel.tenant_id == current_user.tenant_id)
        .all()
    )

    return ChannelListResponse(
        channels=[_channel_to_response(c) for c in channels],
        total=len(channels),
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific channel."""
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return _channel_to_response(channel)


@router.patch("/{channel_id}", response_model=ChannelResponse)
def update_channel(
    channel_id: uuid.UUID,
    data: ChannelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a channel configuration."""
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    channel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(channel)

    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="channel_update",
        resource_type="channel",
        resource_id=str(channel.id),
        details={"updated_fields": list(update_data.keys())},
    )

    return _channel_to_response(channel)


@router.delete("/{channel_id}", status_code=204)
def delete_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a channel and all its conversations.

    This is a destructive operation and cannot be undone.
    """
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="channel_delete",
        resource_type="channel",
        resource_id=str(channel.id),
        details={"name": channel.name, "type": channel.channel_type},
    )

    db.delete(channel)
    db.commit()

    return None
