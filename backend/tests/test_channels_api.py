"""Tests for channel management API endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient


class TestChannelCreate:
    """Tests for channel creation."""

    def test_create_whatsapp_channel(self, client: TestClient, auth_headers_a: dict):
        """Test creating a WhatsApp channel."""
        response = client.post(
            "/api/v1/channels",
            json={
                "name": "Test WhatsApp",
                "channel_type": "whatsapp",
                "phone_number_id": "123456789",
                "webhook_secret": "test-secret",
            },
            headers=auth_headers_a,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test WhatsApp"
        assert data["channel_type"] == "whatsapp"
        assert data["phone_number_id"] == "123456789"
        assert data["has_webhook_secret"] is True
        assert data["is_active"] is True

    def test_create_instagram_channel(self, client: TestClient, auth_headers_a: dict):
        """Test creating an Instagram channel."""
        response = client.post(
            "/api/v1/channels",
            json={
                "name": "Test Instagram",
                "channel_type": "instagram",
                "instagram_page_id": "page123",
            },
            headers=auth_headers_a,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Instagram"
        assert data["channel_type"] == "instagram"
        assert data["instagram_page_id"] == "page123"

    def test_create_channel_requires_auth(self, client: TestClient):
        """Test that channel creation requires authentication."""
        response = client.post(
            "/api/v1/channels",
            json={"name": "Test", "channel_type": "whatsapp"},
        )
        assert response.status_code == 401

    def test_create_duplicate_channel_type(self, client: TestClient, auth_headers_a: dict):
        """Test that duplicate channel types are rejected."""
        # Create first channel
        client.post(
            "/api/v1/channels",
            json={"name": "First WhatsApp", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )

        # Try to create second WhatsApp channel
        response = client.post(
            "/api/v1/channels",
            json={"name": "Second WhatsApp", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestChannelList:
    """Tests for channel listing."""

    def test_list_channels(self, client: TestClient, auth_headers_a: dict):
        """Test listing channels."""
        # Create a channel first
        client.post(
            "/api/v1/channels",
            json={"name": "Test Channel", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )

        response = client.get("/api/v1/channels", headers=auth_headers_a)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert "total" in data


class TestChannelUpdate:
    """Tests for channel updates."""

    def test_update_channel(self, client: TestClient, auth_headers_a: dict):
        """Test updating a channel."""
        # Create channel
        create_response = client.post(
            "/api/v1/channels",
            json={"name": "Original Name", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )
        channel_id = create_response.json()["id"]

        # Update it
        response = client.patch(
            f"/api/v1/channels/{channel_id}",
            json={"name": "Updated Name", "is_active": False},
            headers=auth_headers_a,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["is_active"] is False

    def test_update_nonexistent_channel(self, client: TestClient, auth_headers_a: dict):
        """Test updating a non-existent channel."""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/channels/{fake_id}",
            json={"name": "Test"},
            headers=auth_headers_a,
        )
        assert response.status_code == 404


class TestChannelDelete:
    """Tests for channel deletion."""

    def test_delete_channel(self, client: TestClient, auth_headers_a: dict):
        """Test deleting a channel."""
        # Create channel
        create_response = client.post(
            "/api/v1/channels",
            json={"name": "To Delete", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )
        channel_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/channels/{channel_id}",
            headers=auth_headers_a,
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/channels/{channel_id}",
            headers=auth_headers_a,
        )
        assert get_response.status_code == 404


class TestChannelTenantIsolation:
    """Tests for tenant isolation in channels."""

    def test_channel_isolated_between_tenants(
        self,
        client: TestClient,
        auth_headers_a: dict,
        auth_headers_b: dict,
    ):
        """Test that channels are isolated between tenants."""
        # Create channel as first tenant
        create_response = client.post(
            "/api/v1/channels",
            json={"name": "Tenant A Channel", "channel_type": "whatsapp"},
            headers=auth_headers_a,
        )
        channel_id = create_response.json()["id"]

        # Try to access as second tenant
        response = client.get(
            f"/api/v1/channels/{channel_id}",
            headers=auth_headers_b,
        )
        assert response.status_code == 404

