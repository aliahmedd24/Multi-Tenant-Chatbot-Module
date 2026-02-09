"""Instagram Messaging API client service.

Handles sending messages, webhook verification, and signature validation
for Instagram Direct Messaging via the Graph API.
"""

import hashlib
import hmac
import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class InstagramClient:
    """Client for Instagram Graph API messaging."""

    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        page_id: str,
        access_token: str,
        api_version: str | None = None,
    ):
        self.page_id = page_id
        self.access_token = access_token
        self.api_version = api_version or get_settings().instagram_api_version

    @property
    def messages_url(self) -> str:
        """Get the URL for sending messages."""
        return f"{self.BASE_URL}/{self.api_version}/{self.page_id}/messages"

    async def send_text_message(
        self,
        recipient_id: str,
        message: str,
    ) -> dict:
        """Send a text message to an Instagram user.

        Args:
            recipient_id: Instagram-scoped user ID (IGSID)
            message: Text message content

        Returns:
            API response with message ID
        """
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
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
                logger.error(f"Instagram API error: {response.text}")
                response.raise_for_status()

            return response.json()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify Instagram webhook signature (HMAC-SHA256).

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (sha256=...)
        secret: App secret from Meta App

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
    """Parse Instagram webhook payload to extract messages.

    Args:
        payload: Webhook JSON payload

    Returns:
        List of message dicts with keys: sender_id, text, message_id, timestamp
    """
    messages = []

    try:
        entry = payload.get("entry", [])
        for e in entry:
            messaging = e.get("messaging", [])

            for event in messaging:
                message = event.get("message", {})
                if message and "text" in message:
                    messages.append({
                        "sender_id": event.get("sender", {}).get("id"),
                        "recipient_id": event.get("recipient", {}).get("id"),
                        "text": message.get("text", ""),
                        "message_id": message.get("mid"),
                        "timestamp": event.get("timestamp"),
                        "page_id": e.get("id"),  # Instagram page ID
                    })
    except Exception as e:
        logger.error(f"Error parsing Instagram webhook: {e}")

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
