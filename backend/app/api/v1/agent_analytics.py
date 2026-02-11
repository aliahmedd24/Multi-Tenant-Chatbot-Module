"""Agent-specific analytics API endpoints.

Provides chatbot performance metrics including:
- Sentiment analysis distribution and trends
- Response time metrics and trends
- Conversation length distribution and resolution stats
- AI-generated performance insights
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.agent_analytics import (
    AgentInsights,
    ConversationAnalytics,
    ResponseTimeAnalytics,
    SentimentAnalytics,
)
from app.services.agent_analytics import (
    generate_insights,
    get_conversation_analytics,
    get_response_time_metrics,
    get_sentiment_distribution,
)

router = APIRouter()


@router.get("/sentiment", response_model=SentimentAnalytics)
def get_sentiment(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get sentiment analysis distribution and trends."""
    return get_sentiment_distribution(db, str(current_user.tenant_id), period_days)


@router.get("/response-time", response_model=ResponseTimeAnalytics)
def get_response_time(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get response time metrics and trends."""
    return get_response_time_metrics(db, str(current_user.tenant_id), period_days)


@router.get("/conversations", response_model=ConversationAnalytics)
def get_conversations(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation length distribution and resolution stats."""
    return get_conversation_analytics(db, str(current_user.tenant_id), period_days)


@router.get("/insights", response_model=AgentInsights)
def get_insights(
    period_days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-generated performance insights."""
    tenant_id = str(current_user.tenant_id)

    sentiment_data = get_sentiment_distribution(db, tenant_id, period_days)
    response_time_data = get_response_time_metrics(db, tenant_id, period_days)
    conversation_data = get_conversation_analytics(db, tenant_id, period_days)

    insights = generate_insights(sentiment_data, response_time_data, conversation_data)

    return AgentInsights(
        insights=insights,
        generated_at=datetime.utcnow().isoformat(),
    )
