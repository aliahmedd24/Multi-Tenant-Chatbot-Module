"""WhatsApp Cloud API client service.

Handles sending messages, webhook verification, and signature validation
for the WhatsApp Business Platform.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Client for WhatsApp Cloud API."""

    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        api_version: str | None = None,
    ):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.api_version = api_version or get_settings().whatsapp_api_version

    @property
    def messages_url(self) -> str:
        """Get the URL for sending messages."""
        return f"{self.BASE_URL}/{self.api_version}/{self.phone_number_id}/messages"

    async def send_text_message(
        self,
        to: str,
        message: str,
    ) -> dict:
        """Send a text message to a WhatsApp user.

        Args:
            to: Recipient phone number (E.164 format, e.g., +1234567890)
            message: Text message content

        Returns:
            API response with message ID
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.messages_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {response.text}")
                response.raise_for_status()

            return response.json()

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark a message as read.

        Args:
            message_id: WhatsApp message ID to mark as read

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.messages_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
            return response.json()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify WhatsApp webhook signature (HMAC-SHA256).

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (sha256=...)
        secret: Webhook secret from Meta App

    Returns:
        True if signature is valid
    """
    if not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]  # Remove 'sha256=' prefix
    computed_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_signature, expected_signature)


def parse_webhook_payload(payload: dict) -> list[dict]:
    """Parse WhatsApp webhook payload to extract messages.

    Args:
        payload: Webhook JSON payload

    Returns:
        List of message dicts with keys: from, text, message_id, timestamp
    """
    messages = []

    try:
        entry = payload.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                incoming_messages = value.get("messages", [])

                for msg in incoming_messages:
                    if msg.get("type") == "text":
                        messages.append({
                            "from": msg.get("from"),
                            "text": msg.get("text", {}).get("body", ""),
                            "message_id": msg.get("id"),
                            "timestamp": msg.get("timestamp"),
                            "phone_number_id": value.get("metadata", {}).get(
                                "phone_number_id"
                            ),
                        })
    except Exception as e:
        logger.error(f"Error parsing WhatsApp webhook: {e}")

    return messages


def verify_webhook_challenge(
    mode: str,
    token: str,
    challenge: str,
    verify_token: str,
) -> Optional[str]:
    """Verify webhook subscription challenge.

    Args:
        mode: hub.mode query param
        token: hub.verify_token query param
        challenge: hub.challenge query param
        verify_token: Expected verification token

    Returns:
        Challenge string if valid, None otherwise
    """
    if mode == "subscribe" and token == verify_token:
        return challenge
    return None
