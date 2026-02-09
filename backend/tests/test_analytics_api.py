"""Tests for analytics API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAnalyticsOverview:
    """Tests for /analytics/overview endpoint."""

    def test_get_overview_success(self, client: TestClient, auth_headers_a: dict):
        """Test getting analytics overview."""
        response = client.get("/api/v1/analytics/overview", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "total_messages" in data
        assert "active_conversations" in data
        assert "avg_response_time_seconds" in data
        assert "active_channels" in data

    def test_get_overview_requires_auth(self, client: TestClient):
        """Test that overview requires authentication."""
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code == 401


class TestAnalyticsConversations:
    """Tests for /analytics/conversations endpoint."""

    def test_get_conversation_trends(self, client: TestClient, auth_headers_a: dict):
        """Test getting conversation trends."""
        response = client.get(
            "/api/v1/analytics/conversations",
            params={"period_days": 30},
            headers=auth_headers_a,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert "total" in data
        assert "daily" in data

    def test_get_conversation_trends_custom_period(
        self, client: TestClient, auth_headers_a: dict
    ):
        """Test trends with custom period."""
        response = client.get(
            "/api/v1/analytics/conversations",
            params={"period_days": 7},
            headers=auth_headers_a,
        )
        assert response.status_code == 200
        assert response.json()["period_days"] == 7

    def test_get_conversation_trends_invalid_period(
        self, client: TestClient, auth_headers_a: dict
    ):
        """Test trends with invalid period (too short)."""
        response = client.get(
            "/api/v1/analytics/conversations",
            params={"period_days": 3},
            headers=auth_headers_a,
        )
        assert response.status_code == 422  # Validation error


class TestAnalyticsMessages:
    """Tests for /analytics/messages endpoint."""

    def test_get_message_trends(self, client: TestClient, auth_headers_a: dict):
        """Test getting message volume trends."""
        response = client.get(
            "/api/v1/analytics/messages",
            params={"period_days": 30},
            headers=auth_headers_a,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_inbound" in data
        assert "total_outbound" in data
        assert "daily_inbound" in data
        assert "daily_outbound" in data


class TestAnalyticsChannels:
    """Tests for /analytics/channels endpoint."""

    def test_get_channel_performance(self, client: TestClient, auth_headers_a: dict):
        """Test getting channel performance metrics."""
        response = client.get("/api/v1/analytics/channels", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert "total_channels" in data


class TestAnalyticsTenantIsolation:
    """Tests for tenant isolation in analytics."""

    def test_analytics_tenant_isolated(
        self, client: TestClient, auth_headers_a: dict, auth_headers_b: dict
    ):
        """Test that analytics are isolated between tenants."""
        # Both tenants get their own data (should not error)
        response_a = client.get("/api/v1/analytics/overview", headers=auth_headers_a)
        response_b = client.get("/api/v1/analytics/overview", headers=auth_headers_b)

        assert response_a.status_code == 200
        assert response_b.status_code == 200

        # Tenant B should have 0 data if nothing created
        data_b = response_b.json()
        assert data_b["total_conversations"] == 0
        assert data_b["total_messages"] == 0
