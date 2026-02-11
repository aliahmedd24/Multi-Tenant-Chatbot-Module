"""Pydantic schemas for agent-specific analytics responses."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SentimentCount(BaseModel):
    """Count of messages by sentiment category."""

    sentiment: str
    count: int
    percentage: float


class SentimentTrendPoint(BaseModel):
    """Daily sentiment score trend point."""

    date: date
    avg_score: float
    positive_count: int
    negative_count: int
    neutral_count: int


class SentimentAnalytics(BaseModel):
    """Full sentiment analysis response."""

    period_days: int
    total_analyzed: int
    distribution: list[SentimentCount] = Field(default_factory=list)
    overall_score: float = Field(..., description="Average sentiment score (-1.0 to 1.0)")
    overall_label: str = Field(..., description="Overall sentiment label")
    daily_trend: list[SentimentTrendPoint] = Field(default_factory=list)
    satisfaction_rating: str = Field(..., description="high, moderate, or low")


class ResponseTimeMetrics(BaseModel):
    """Response time summary metrics."""

    avg_response_time_seconds: float
    min_response_time_seconds: Optional[float] = None
    max_response_time_seconds: Optional[float] = None
    performance_rating: str = Field(..., description="excellent, good, or needs_improvement")
    target_seconds: float = 2.0
    total_responses: int


class ResponseTimeTrendPoint(BaseModel):
    """Daily response time trend."""

    date: date
    avg_seconds: float
    count: int


class ResponseTimeAnalytics(BaseModel):
    """Full response time analytics response."""

    period_days: int
    metrics: ResponseTimeMetrics
    daily_trend: list[ResponseTimeTrendPoint] = Field(default_factory=list)


class ConversationLengthBucket(BaseModel):
    """Conversation length distribution bucket."""

    label: str
    count: int
    percentage: float


class ConversationAnalytics(BaseModel):
    """Conversation length and resolution analytics."""

    period_days: int
    total_conversations: int
    avg_message_count: float
    resolved_count: int
    resolution_rate: float
    handoff_count: int
    handoff_rate: float
    length_distribution: list[ConversationLengthBucket] = Field(default_factory=list)


class InsightItem(BaseModel):
    """Single AI-generated insight."""

    category: str
    severity: str = Field(..., description="info, warning, or success")
    title: str
    description: str


class AgentInsights(BaseModel):
    """Collection of AI-generated insights."""

    insights: list[InsightItem] = Field(default_factory=list)
    generated_at: str
