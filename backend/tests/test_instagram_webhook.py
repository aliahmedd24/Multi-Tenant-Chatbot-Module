"""Tests for Instagram webhook endpoints."""

import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient


class TestInstagramWebhookVerification:
    """Tests for Instagram webhook verification (GET endpoint)."""

    def test_verify_webhook_success(self, client: TestClient):
        """Test successful webhook verification."""
        response = client.get(
            "/api/v1/webhooks/instagram",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wafaa-verify-token",
                "hub.challenge": "instagram-challenge-456",
            },
        )
        assert response.status_code == 200
        assert response.text == "instagram-challenge-456"

    def test_verify_webhook_wrong_token(self, client: TestClient):
        """Test webhook verification with wrong token."""
        response = client.get(
            "/api/v1/webhooks/instagram",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "test-challenge",
            },
        )
        assert response.status_code == 403


class TestInstagramWebhookReceive:
    """Tests for Instagram message receive (POST endpoint)."""

    def test_receive_empty_payload(self, client: TestClient):
        """Test receiving empty webhook payload."""
        response = client.post(
            "/api/v1/webhooks/instagram",
            json={"entry": []},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestInstagramSignatureVerification:
    """Tests for HMAC signature verification."""

    def test_verify_signature(self):
        """Test signature verification function."""
        from app.services.instagram import verify_webhook_signature

        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(payload, signature, secret) is True


class TestInstagramPayloadParsing:
    """Tests for webhook payload parsing."""

    def test_parse_text_message(self):
        """Test parsing text message from webhook payload."""
        from app.services.instagram import parse_webhook_payload

        payload = {
            "entry": [
                {
                    "id": "page123",
                    "messaging": [
                        {
                            "sender": {"id": "user456"},
                            "recipient": {"id": "page123"},
                            "message": {
                                "mid": "msg789",
                                "text": "Hi there!",
                            },
                            "timestamp": 1234567890,
                        }
                    ],
                }
            ]
        }

        messages = parse_webhook_payload(payload)
        assert len(messages) == 1
        assert messages[0]["sender_id"] == "user456"
        assert messages[0]["text"] == "Hi there!"
        assert messages[0]["message_id"] == "msg789"
        assert messages[0]["page_id"] == "page123"

    def test_parse_empty_payload(self):
        """Test parsing empty payload."""
        from app.services.instagram import parse_webhook_payload

        assert parse_webhook_payload({}) == []
        assert parse_webhook_payload({"entry": []}) == []
