"""Tests for WhatsApp webhook endpoints."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient


class TestWhatsAppWebhookVerification:
    """Tests for WhatsApp webhook verification (GET endpoint)."""

    def test_verify_webhook_success(self, client: TestClient):
        """Test successful webhook verification."""
        response = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wafaa-verify-token",
                "hub.challenge": "test-challenge-123",
            },
        )
        assert response.status_code == 200
        assert response.text == "test-challenge-123"

    def test_verify_webhook_wrong_token(self, client: TestClient):
        """Test webhook verification with wrong token."""
        response = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "test-challenge-123",
            },
        )
        assert response.status_code == 403

    def test_verify_webhook_missing_params(self, client: TestClient):
        """Test webhook verification with missing params."""
        response = client.get("/api/v1/webhooks/whatsapp")
        assert response.status_code == 403


class TestWhatsAppWebhookReceive:
    """Tests for WhatsApp message receive (POST endpoint)."""

    def test_receive_empty_payload(self, client: TestClient):
        """Test receiving empty webhook payload."""
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            json={"entry": []},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_receive_status_update(self, client: TestClient):
        """Test receiving status update (not a message)."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {"status": "delivered", "id": "msg123"}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        response = client.post("/api/v1/webhooks/whatsapp", json=payload)
        assert response.status_code == 200


class TestSignatureVerification:
    """Tests for HMAC signature verification."""

    def test_verify_signature(self):
        """Test signature verification function."""
        from app.services.whatsapp import verify_webhook_signature

        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        from app.services.whatsapp import verify_webhook_signature

        payload = b'{"test": "data"}'
        assert verify_webhook_signature(payload, "sha256=invalid", "secret") is False

    def test_verify_signature_wrong_prefix(self):
        """Test signature verification with wrong prefix."""
        from app.services.whatsapp import verify_webhook_signature

        payload = b'{"test": "data"}'
        assert verify_webhook_signature(payload, "md5=abc123", "secret") is False


class TestPayloadParsing:
    """Tests for webhook payload parsing."""

    def test_parse_text_message(self):
        """Test parsing text message from webhook payload."""
        from app.services.whatsapp import parse_webhook_payload

        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "123456"},
                                "messages": [
                                    {
                                        "from": "+1234567890",
                                        "id": "msg123",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                        "timestamp": "1234567890",
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }

        messages = parse_webhook_payload(payload)
        assert len(messages) == 1
        assert messages[0]["from"] == "+1234567890"
        assert messages[0]["text"] == "Hello"
        assert messages[0]["message_id"] == "msg123"
        assert messages[0]["phone_number_id"] == "123456"

    def test_parse_empty_payload(self):
        """Test parsing empty payload."""
        from app.services.whatsapp import parse_webhook_payload

        assert parse_webhook_payload({}) == []
        assert parse_webhook_payload({"entry": []}) == []
