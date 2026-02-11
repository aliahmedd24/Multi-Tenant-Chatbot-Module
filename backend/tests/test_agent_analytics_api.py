"""Tests for agent analytics API endpoints."""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message, MessageDirection, MessageStatus


# Helper to create test data
def _create_channel(db: Session, tenant_id, name="Test Channel"):
    channel = Channel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=name,
        channel_type="whatsapp",
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def _create_conversation(db: Session, tenant_id, channel_id, status="active"):
    conv = Conversation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        channel_id=channel_id,
        customer_identifier="+1234567890",
        status=status,
        last_message_at=datetime.utcnow(),
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _create_message(
    db: Session,
    tenant_id,
    conversation_id,
    direction="inbound",
    content="test message",
    sentiment=None,
    sentiment_score=None,
    intent=None,
    response_time_seconds=None,
):
    msg = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        direction=direction,
        content=content,
        status=MessageStatus.delivered.value,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        intent=intent,
        response_time_seconds=response_time_seconds,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


class TestSentimentEndpoint:
    """Tests for /analytics/agent/sentiment endpoint."""

    def test_get_sentiment_success(self, client: TestClient, auth_headers_a: dict):
        response = client.get("/api/v1/analytics/agent/sentiment", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "total_analyzed" in data
        assert "distribution" in data
        assert "overall_score" in data
        assert "overall_label" in data
        assert "satisfaction_rating" in data

    def test_get_sentiment_with_data(
        self, client: TestClient, auth_headers_a: dict, db: Session, tenant_a
    ):
        channel = _create_channel(db, tenant_a.id)
        conv = _create_conversation(db, tenant_a.id, channel.id)

        _create_message(db, tenant_a.id, conv.id, sentiment="positive", sentiment_score=0.8)
        _create_message(db, tenant_a.id, conv.id, sentiment="positive", sentiment_score=0.6)
        _create_message(db, tenant_a.id, conv.id, sentiment="neutral", sentiment_score=0.0)
        _create_message(db, tenant_a.id, conv.id, sentiment="negative", sentiment_score=-0.5)

        response = client.get("/api/v1/analytics/agent/sentiment", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] == 4
        assert len(data["distribution"]) == 3

    def test_get_sentiment_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/analytics/agent/sentiment")
        assert response.status_code == 401

    def test_get_sentiment_custom_period(self, client: TestClient, auth_headers_a: dict):
        response = client.get(
            "/api/v1/analytics/agent/sentiment",
            params={"period_days": 7},
            headers=auth_headers_a,
        )
        assert response.status_code == 200
        assert response.json()["period_days"] == 7


class TestResponseTimeEndpoint:
    """Tests for /analytics/agent/response-time endpoint."""

    def test_get_response_time_success(self, client: TestClient, auth_headers_a: dict):
        response = client.get("/api/v1/analytics/agent/response-time", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "daily_trend" in data
        assert "avg_response_time_seconds" in data["metrics"]
        assert "performance_rating" in data["metrics"]

    def test_get_response_time_with_data(
        self, client: TestClient, auth_headers_a: dict, db: Session, tenant_a
    ):
        channel = _create_channel(db, tenant_a.id)
        conv = _create_conversation(db, tenant_a.id, channel.id)

        _create_message(
            db, tenant_a.id, conv.id,
            direction="outbound", response_time_seconds=1.5,
        )
        _create_message(
            db, tenant_a.id, conv.id,
            direction="outbound", response_time_seconds=3.0,
        )

        response = client.get("/api/v1/analytics/agent/response-time", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["total_responses"] == 2
        assert data["metrics"]["avg_response_time_seconds"] == 2.25

    def test_get_response_time_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/analytics/agent/response-time")
        assert response.status_code == 401


class TestConversationEndpoint:
    """Tests for /analytics/agent/conversations endpoint."""

    def test_get_conversations_success(self, client: TestClient, auth_headers_a: dict):
        response = client.get("/api/v1/analytics/agent/conversations", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "avg_message_count" in data
        assert "resolved_count" in data
        assert "resolution_rate" in data
        assert "length_distribution" in data

    def test_get_conversations_with_data(
        self, client: TestClient, auth_headers_a: dict, db: Session, tenant_a
    ):
        channel = _create_channel(db, tenant_a.id)
        conv1 = _create_conversation(db, tenant_a.id, channel.id, status=ConversationStatus.closed.value)
        conv2 = _create_conversation(db, tenant_a.id, channel.id, status=ConversationStatus.active.value)

        # 3 messages in conv1, 1 in conv2
        for _ in range(3):
            _create_message(db, tenant_a.id, conv1.id)
        _create_message(db, tenant_a.id, conv2.id)

        response = client.get("/api/v1/analytics/agent/conversations", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert data["total_conversations"] == 2
        assert data["resolved_count"] == 1
        assert data["resolution_rate"] == 50.0

    def test_get_conversations_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/analytics/agent/conversations")
        assert response.status_code == 401


class TestInsightsEndpoint:
    """Tests for /analytics/agent/insights endpoint."""

    def test_get_insights_success(self, client: TestClient, auth_headers_a: dict):
        response = client.get("/api/v1/analytics/agent/insights", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "generated_at" in data
        assert len(data["insights"]) > 0

    def test_get_insights_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/analytics/agent/insights")
        assert response.status_code == 401


class TestAgentAnalyticsTenantIsolation:
    """Tests for tenant isolation in agent analytics."""

    def test_sentiment_tenant_isolated(
        self,
        client: TestClient,
        auth_headers_a: dict,
        auth_headers_b: dict,
        db: Session,
        tenant_a,
        tenant_b,
    ):
        # Create data for Tenant A only
        channel = _create_channel(db, tenant_a.id)
        conv = _create_conversation(db, tenant_a.id, channel.id)
        _create_message(db, tenant_a.id, conv.id, sentiment="positive", sentiment_score=0.9)

        # Tenant A should see data
        response_a = client.get("/api/v1/analytics/agent/sentiment", headers=auth_headers_a)
        assert response_a.status_code == 200
        assert response_a.json()["total_analyzed"] == 1

        # Tenant B should see no data
        response_b = client.get("/api/v1/analytics/agent/sentiment", headers=auth_headers_b)
        assert response_b.status_code == 200
        assert response_b.json()["total_analyzed"] == 0
