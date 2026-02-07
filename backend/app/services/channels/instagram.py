"""Instagram channel adapter.

Integrates with Meta's Instagram Messaging API.
"""

import hashlib
import hmac
from typing import Optional

import httpx
import structlog

from app.services.channels.base import ChannelAdapter


logger = structlog.get_logger()


class InstagramAdapter(ChannelAdapter):
    """Instagram Messaging API adapter.

    Handles incoming webhooks and outgoing messages via Meta Graph API.
    """

    GRAPH_API_URL = "https://graph.facebook.com/v18.0"

    async def parse_webhook(self, payload: dict) -> Optional[dict]:
        """Parse incoming Instagram webhook.

        Args:
            payload: Raw webhook payload from Meta.

        Returns:
            Normalized message dict or None.
        """
        try:
            entry = payload.get("entry", [])
            if not entry:
                return None

            messaging = entry[0].get("messaging", [])
            if not messaging:
                return None

            event = messaging[0]
            sender_id = event.get("sender", {}).get("id", "")
            timestamp = event.get("timestamp", "")

            message = event.get("message", {})
            if not message:
                return None

            text = message.get("text", "")
            message_type = "text"

            # Check for attachments
            attachments = message.get("attachments", [])
            if attachments:
                message_type = attachments[0].get("type", "unknown")

            logger.info(
                "instagram_message_received",
                sender=sender_id,
                message_type=message_type,
            )

            return {
                "sender_id": sender_id,
                "message": text,
                "message_type": message_type,
                "timestamp": str(timestamp),
                "metadata": {
                    "mid": message.get("mid", ""),
                },
            }

        except Exception as e:
            logger.error("instagram_parse_error", error=str(e))
            return None

    async def send_message(
        self,
        to: str,
        message: str,
        config: dict,
    ) -> dict:
        """Send text message via Instagram.

        Args:
            to: Recipient Instagram-scoped user ID.
            message: Message text.
            config: Instagram config with page_id and access_token.

        Returns:
            API response with message ID.
        """
        page_id = config.get("page_id")
        access_token = config.get("access_token")

        url = f"{self.GRAPH_API_URL}/{page_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "recipient": {"id": to},
            "message": {"text": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info("instagram_message_sent", to=to)
            return response.json()

    async def send_template(
        self,
        to: str,
        template_name: str,
        config: dict,
        parameters: Optional[dict] = None,
    ) -> dict:
        """Send template/generic message via Instagram.

        Instagram uses generic templates differently than WhatsApp.

        Args:
            to: Recipient user ID.
            template_name: Template identifier.
            config: Instagram config.
            parameters: Template parameters.

        Returns:
            API response.
        """
        # Instagram templates are handled as generic messages
        page_id = config.get("page_id")
        access_token = config.get("access_token")

        url = f"{self.GRAPH_API_URL}/{page_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Build generic template
        payload = {
            "recipient": {"id": to},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": parameters.get("elements", []) if parameters else [],
                    },
                }
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info("instagram_template_sent", to=to)
            return response.json()

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify Instagram webhook signature.

        Args:
            payload: Raw request body bytes.
            signature: X-Hub-Signature-256 header value.
            secret: App secret.

        Returns:
            True if signature is valid.
        """
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected, signature)
