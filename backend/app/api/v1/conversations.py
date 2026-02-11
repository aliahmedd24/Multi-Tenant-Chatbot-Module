"""Conversations list and detail API for the dashboard."""

import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.channel import Channel
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.channel import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations for the tenant (channel and in-app chat).

    Ordered by last_message_at descending.
    """
    tenant_id = current_user.tenant_id

    total = (
        db.query(Conversation)
        .filter(Conversation.tenant_id == tenant_id)
        .count()
    )

    subq = (
        db.query(Message.conversation_id, func.count(Message.id).label("msg_count"))
        .filter(Message.tenant_id == tenant_id)
        .group_by(Message.conversation_id)
        .subquery()
    )

    rows = (
        db.query(Conversation, Channel.name.label("channel_name"), subq.c.msg_count)
        .join(Channel, Conversation.channel_id == Channel.id)
        .outerjoin(subq, Conversation.id == subq.c.conversation_id)
        .filter(Conversation.tenant_id == tenant_id)
        .order_by(Conversation.last_message_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    conversations = []
    for conv, channel_name, msg_count in rows:
        conversations.append(
            ConversationResponse(
                id=conv.id,
                channel_id=conv.channel_id,
                channel_name=channel_name or "Unknown",
                customer_identifier=conv.customer_identifier,
                customer_name=conv.customer_name,
                status=conv.status,
                last_message_at=conv.last_message_at,
                message_count=msg_count or 0,
                created_at=conv.created_at,
            )
        )

    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: uuid_module.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single conversation with all its messages (chronological)."""
    tenant_id = current_user.tenant_id

    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    channel = db.query(Channel).filter(Channel.id == conv.channel_id).first()
    channel_name = channel.name if channel else "Unknown"

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id,
            Message.tenant_id == tenant_id,
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    return ConversationDetailResponse(
        id=conv.id,
        channel_id=conv.channel_id,
        channel_name=channel_name,
        customer_identifier=conv.customer_identifier,
        customer_name=conv.customer_name,
        status=conv.status,
        last_message_at=conv.last_message_at,
        message_count=len(messages),
        created_at=conv.created_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )
