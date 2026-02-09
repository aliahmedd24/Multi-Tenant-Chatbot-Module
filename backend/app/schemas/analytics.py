"""Pydantic schemas for analytics responses."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class OverviewMetrics(BaseModel):
    """High-level tenant metrics."""

    total_conversations: int = Field(..., description="All-time conversation count")
    total_messages: int = Field(..., description="All-time message count")
    active_conversations: int = Field(..., description="Currently active conversations")
    avg_response_time_seconds: float = Field(..., description="Average RAG response time")
    active_channels: int = Field(..., description="Number of active channels")


class DailyMetric(BaseModel):
    """Single day metric point."""

    date: date
    count: int


class ConversationTrends(BaseModel):
    """Conversation trends over time."""

    period_days: int = Field(..., description="Number of days in the period")
    total: int = Field(..., description="Total conversations in period")
    daily: list[DailyMetric] = Field(default_factory=list)


class MessageTrends(BaseModel):
    """Message volume trends."""

    period_days: int
    total_inbound: int
    total_outbound: int
    daily_inbound: list[DailyMetric] = Field(default_factory=list)
    daily_outbound: list[DailyMetric] = Field(default_factory=list)


class ChannelMetrics(BaseModel):
    """Per-channel performance metrics."""

    channel_id: str
    channel_name: str
    channel_type: str
    conversation_count: int
    message_count: int
    last_message_at: Optional[datetime] = None


class ChannelPerformance(BaseModel):
    """All channels performance summary."""

    channels: list[ChannelMetrics]
    total_channels: int
