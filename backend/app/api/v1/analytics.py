"""Analytics API endpoints.

Provides aggregated metrics for tenant dashboards including:
- Overview metrics (totals, averages)
- Conversation trends over time
- Message volume trends
- Channel-specific performance
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.channel import Channel
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection
from app.models.user import User
from app.schemas.analytics import (
    ChannelMetrics,
    ChannelPerformance,
    ConversationTrends,
    DailyMetric,
    MessageTrends,
    OverviewMetrics,
)

router = APIRouter()


@router.get("/overview", response_model=OverviewMetrics)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get high-level metrics overview for the tenant."""
    tenant_id = current_user.tenant_id

    # Total conversations
    total_conversations = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.tenant_id == tenant_id)
        .scalar()
        or 0
    )

    # Total messages
    total_messages = (
        db.query(func.count(Message.id))
        .filter(Message.tenant_id == tenant_id)
        .scalar()
        or 0
    )

    # Active conversations
    active_conversations = (
        db.query(func.count(Conversation.id))
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.status == ConversationStatus.active.value,
        )
        .scalar()
        or 0
    )

    # Active channels
    active_channels = (
        db.query(func.count(Channel.id))
        .filter(Channel.tenant_id == tenant_id, Channel.is_active == True)
        .scalar()
        or 0
    )

    # Average response time from actual outbound message data
    avg_rt = (
        db.query(func.avg(Message.response_time_seconds))
        .filter(
            Message.tenant_id == tenant_id,
            Message.response_time_seconds.isnot(None),
        )
        .scalar()
    )
    avg_response_time_seconds = round(avg_rt, 2) if avg_rt else 0.0

    return OverviewMetrics(
        total_conversations=total_conversations,
        total_messages=total_messages,
        active_conversations=active_conversations,
        avg_response_time_seconds=avg_response_time_seconds,
        active_channels=active_channels,
    )


@router.get("/conversations", response_model=ConversationTrends)
def get_conversation_trends(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation trends over specified period."""
    tenant_id = current_user.tenant_id
    start_date = datetime.utcnow() - timedelta(days=period_days)

    # Total conversations in period
    total = (
        db.query(func.count(Conversation.id))
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= start_date,
        )
        .scalar()
        or 0
    )

    # Daily breakdown
    daily_data = (
        db.query(
            func.date(Conversation.created_at).label("date"),
            func.count(Conversation.id).label("count"),
        )
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= start_date,
        )
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
        .all()
    )

    daily = [DailyMetric(date=row.date, count=row.count) for row in daily_data]

    return ConversationTrends(
        period_days=period_days,
        total=total,
        daily=daily,
    )


@router.get("/messages", response_model=MessageTrends)
def get_message_trends(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get message volume trends over specified period."""
    tenant_id = current_user.tenant_id
    start_date = datetime.utcnow() - timedelta(days=period_days)

    # Total by direction
    total_inbound = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.created_at >= start_date,
            Message.direction == MessageDirection.inbound.value,
        )
        .scalar()
        or 0
    )

    total_outbound = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.created_at >= start_date,
            Message.direction == MessageDirection.outbound.value,
        )
        .scalar()
        or 0
    )

    # Daily inbound
    inbound_data = (
        db.query(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("count"),
        )
        .filter(
            Message.tenant_id == tenant_id,
            Message.created_at >= start_date,
            Message.direction == MessageDirection.inbound.value,
        )
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
        .all()
    )

    # Daily outbound
    outbound_data = (
        db.query(
            func.date(Message.created_at).label("date"),
            func.count(Message.id).label("count"),
        )
        .filter(
            Message.tenant_id == tenant_id,
            Message.created_at >= start_date,
            Message.direction == MessageDirection.outbound.value,
        )
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
        .all()
    )

    return MessageTrends(
        period_days=period_days,
        total_inbound=total_inbound,
        total_outbound=total_outbound,
        daily_inbound=[DailyMetric(date=r.date, count=r.count) for r in inbound_data],
        daily_outbound=[DailyMetric(date=r.date, count=r.count) for r in outbound_data],
    )


@router.get("/channels", response_model=ChannelPerformance)
def get_channel_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get per-channel performance metrics."""
    tenant_id = current_user.tenant_id

    # Get all channels with conversation and message counts
    channels = (
        db.query(Channel)
        .filter(Channel.tenant_id == tenant_id)
        .all()
    )

    channel_metrics = []
    for channel in channels:
        conv_count = (
            db.query(func.count(Conversation.id))
            .filter(Conversation.channel_id == channel.id)
            .scalar()
            or 0
        )

        msg_count = (
            db.query(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .filter(Conversation.channel_id == channel.id)
            .scalar()
            or 0
        )

        last_msg = (
            db.query(func.max(Message.created_at))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .filter(Conversation.channel_id == channel.id)
            .scalar()
        )

        channel_metrics.append(
            ChannelMetrics(
                channel_id=str(channel.id),
                channel_name=channel.name,
                channel_type=channel.channel_type,
                conversation_count=conv_count,
                message_count=msg_count,
                last_message_at=last_msg,
            )
        )

    return ChannelPerformance(
        channels=channel_metrics,
        total_channels=len(channel_metrics),
    )
