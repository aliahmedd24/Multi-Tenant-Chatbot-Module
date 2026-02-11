"""Agent analytics service - query functions for agent-specific metrics.

All queries filter by tenant_id for multi-tenant isolation.
Uses SQLite-compatible functions (func.date, func.avg, func.count).
"""

from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection


def get_sentiment_distribution(db: Session, tenant_id: str, period_days: int) -> dict:
    """Query sentiment counts and compute overall score."""
    start_date = datetime.utcnow() - timedelta(days=period_days)

    # Count by sentiment category
    rows = (
        db.query(
            Message.sentiment,
            func.count(Message.id).label("count"),
        )
        .filter(
            Message.tenant_id == tenant_id,
            Message.direction == MessageDirection.inbound.value,
            Message.sentiment.isnot(None),
            Message.created_at >= start_date,
        )
        .group_by(Message.sentiment)
        .all()
    )

    total = sum(r.count for r in rows)
    distribution = []
    for row in rows:
        distribution.append({
            "sentiment": row.sentiment,
            "count": row.count,
            "percentage": round((row.count / total * 100) if total > 0 else 0, 1),
        })

    # Overall score
    avg_score = (
        db.query(func.avg(Message.sentiment_score))
        .filter(
            Message.tenant_id == tenant_id,
            Message.direction == MessageDirection.inbound.value,
            Message.sentiment_score.isnot(None),
            Message.created_at >= start_date,
        )
        .scalar()
    )
    overall_score = round(avg_score, 4) if avg_score else 0.0

    if overall_score >= 0.05:
        overall_label = "positive"
    elif overall_score <= -0.05:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    # Daily trend
    daily_rows = (
        db.query(
            func.date(Message.created_at).label("date"),
            func.avg(Message.sentiment_score).label("avg_score"),
            func.sum(case((Message.sentiment == "positive", 1), else_=0)).label("positive_count"),
            func.sum(case((Message.sentiment == "negative", 1), else_=0)).label("negative_count"),
            func.sum(case((Message.sentiment == "neutral", 1), else_=0)).label("neutral_count"),
        )
        .filter(
            Message.tenant_id == tenant_id,
            Message.direction == MessageDirection.inbound.value,
            Message.sentiment.isnot(None),
            Message.created_at >= start_date,
        )
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
        .all()
    )

    daily_trend = [
        {
            "date": row.date,
            "avg_score": round(float(row.avg_score), 4) if row.avg_score else 0.0,
            "positive_count": int(row.positive_count or 0),
            "negative_count": int(row.negative_count or 0),
            "neutral_count": int(row.neutral_count or 0),
        }
        for row in daily_rows
    ]

    # Satisfaction rating
    positive_pct = 0
    for d in distribution:
        if d["sentiment"] == "positive":
            positive_pct = d["percentage"]
    if positive_pct >= 60:
        satisfaction = "high"
    elif positive_pct >= 30:
        satisfaction = "moderate"
    else:
        satisfaction = "low"

    return {
        "period_days": period_days,
        "total_analyzed": total,
        "distribution": distribution,
        "overall_score": overall_score,
        "overall_label": overall_label,
        "daily_trend": daily_trend,
        "satisfaction_rating": satisfaction,
    }


def get_response_time_metrics(db: Session, tenant_id: str, period_days: int) -> dict:
    """Compute average response time, trend data, performance rating."""
    start_date = datetime.utcnow() - timedelta(days=period_days)

    base_filter = [
        Message.tenant_id == tenant_id,
        Message.direction == MessageDirection.outbound.value,
        Message.response_time_seconds.isnot(None),
        Message.created_at >= start_date,
    ]

    # Aggregate metrics
    result = (
        db.query(
            func.avg(Message.response_time_seconds).label("avg_rt"),
            func.min(Message.response_time_seconds).label("min_rt"),
            func.max(Message.response_time_seconds).label("max_rt"),
            func.count(Message.id).label("total"),
        )
        .filter(*base_filter)
        .first()
    )

    avg_rt = round(float(result.avg_rt), 2) if result.avg_rt else 0.0
    min_rt = round(float(result.min_rt), 2) if result.min_rt else None
    max_rt = round(float(result.max_rt), 2) if result.max_rt else None
    total = result.total or 0

    if avg_rt < 2.0:
        rating = "excellent"
    elif avg_rt <= 5.0:
        rating = "good"
    else:
        rating = "needs_improvement"

    # Daily trend
    daily_rows = (
        db.query(
            func.date(Message.created_at).label("date"),
            func.avg(Message.response_time_seconds).label("avg_seconds"),
            func.count(Message.id).label("count"),
        )
        .filter(*base_filter)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at))
        .all()
    )

    daily_trend = [
        {
            "date": row.date,
            "avg_seconds": round(float(row.avg_seconds), 2),
            "count": row.count,
        }
        for row in daily_rows
    ]

    return {
        "period_days": period_days,
        "metrics": {
            "avg_response_time_seconds": avg_rt,
            "min_response_time_seconds": min_rt,
            "max_response_time_seconds": max_rt,
            "performance_rating": rating,
            "target_seconds": 2.0,
            "total_responses": total,
        },
        "daily_trend": daily_trend,
    }


def get_conversation_analytics(db: Session, tenant_id: str, period_days: int) -> dict:
    """Count messages per conversation, bucket into distribution."""
    start_date = datetime.utcnow() - timedelta(days=period_days)

    # Get conversations in period
    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.created_at >= start_date,
        )
        .all()
    )

    total_conversations = len(conversations)

    # Count messages per conversation
    msg_counts = []
    for conv in conversations:
        count = (
            db.query(func.count(Message.id))
            .filter(Message.conversation_id == conv.id)
            .scalar()
            or 0
        )
        msg_counts.append(count)

    avg_msg = round(sum(msg_counts) / len(msg_counts), 1) if msg_counts else 0.0

    # Bucket distribution
    buckets = {"1-2": 0, "3-5": 0, "6-10": 0, "11-20": 0, "20+": 0}
    for c in msg_counts:
        if c <= 2:
            buckets["1-2"] += 1
        elif c <= 5:
            buckets["3-5"] += 1
        elif c <= 10:
            buckets["6-10"] += 1
        elif c <= 20:
            buckets["11-20"] += 1
        else:
            buckets["20+"] += 1

    length_distribution = [
        {
            "label": label,
            "count": count,
            "percentage": round((count / total_conversations * 100) if total_conversations > 0 else 0, 1),
        }
        for label, count in buckets.items()
    ]

    # Resolution stats
    resolved = sum(1 for conv in conversations if conv.status == ConversationStatus.closed.value)
    handoff = sum(1 for conv in conversations if conv.status == ConversationStatus.handoff.value)

    return {
        "period_days": period_days,
        "total_conversations": total_conversations,
        "avg_message_count": avg_msg,
        "resolved_count": resolved,
        "resolution_rate": round((resolved / total_conversations * 100) if total_conversations > 0 else 0, 1),
        "handoff_count": handoff,
        "handoff_rate": round((handoff / total_conversations * 100) if total_conversations > 0 else 0, 1),
        "length_distribution": length_distribution,
    }


def generate_insights(sentiment_data: dict, response_time_data: dict, conversation_data: dict) -> list[dict]:
    """Generate rule-based insight items from aggregated metrics."""
    insights = []
    metrics = response_time_data.get("metrics", {})

    # Response time insights
    avg_rt = metrics.get("avg_response_time_seconds", 0)
    if avg_rt > 5.0:
        insights.append({
            "category": "response_time",
            "severity": "warning",
            "title": "High Response Time",
            "description": f"Average response time is {avg_rt}s, above the 5s threshold. Consider optimizing your knowledge base for faster retrieval.",
        })
    elif avg_rt > 0 and avg_rt <= 2.0:
        insights.append({
            "category": "response_time",
            "severity": "success",
            "title": "Excellent Response Time",
            "description": f"Average response time is {avg_rt}s, well within the 2s target. Great performance!",
        })

    # Sentiment insights
    dist = {d["sentiment"]: d["percentage"] for d in sentiment_data.get("distribution", [])}
    negative_pct = dist.get("negative", 0)
    positive_pct = dist.get("positive", 0)

    if negative_pct > 20:
        insights.append({
            "category": "sentiment",
            "severity": "warning",
            "title": "Elevated Negative Sentiment",
            "description": f"{negative_pct}% of messages have negative sentiment. Review recent complaints for recurring issues.",
        })
    if positive_pct >= 60:
        insights.append({
            "category": "sentiment",
            "severity": "success",
            "title": "High Customer Satisfaction",
            "description": f"{positive_pct}% positive sentiment. Current knowledge base coverage appears effective.",
        })

    # Conversation insights
    avg_len = conversation_data.get("avg_message_count", 0)
    if avg_len > 10:
        insights.append({
            "category": "engagement",
            "severity": "warning",
            "title": "Long Conversations",
            "description": f"Average conversation length is {avg_len} messages. Consider adding more FAQ entries to reduce back-and-forth.",
        })
    elif avg_len > 0 and avg_len <= 4:
        insights.append({
            "category": "engagement",
            "severity": "success",
            "title": "Efficient Conversations",
            "description": f"Average conversation length is {avg_len} messages. Customers are getting fast answers.",
        })

    resolution_rate = conversation_data.get("resolution_rate", 0)
    if resolution_rate < 50 and conversation_data.get("total_conversations", 0) > 0:
        insights.append({
            "category": "engagement",
            "severity": "info",
            "title": "Low Resolution Rate",
            "description": f"Only {resolution_rate}% of conversations are resolved. Many may still be active or escalated.",
        })

    # Fallback if no insights generated
    if not insights:
        total = sentiment_data.get("total_analyzed", 0)
        if total == 0:
            insights.append({
                "category": "engagement",
                "severity": "info",
                "title": "No Data Yet",
                "description": "Start receiving messages to see AI-generated insights about your chatbot's performance.",
            })
        else:
            insights.append({
                "category": "engagement",
                "severity": "info",
                "title": "Performance On Track",
                "description": "All metrics are within normal ranges. Keep monitoring for changes.",
            })

    return insights
