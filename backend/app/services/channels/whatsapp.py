"""WhatsApp channel adapter.

Integrates with Meta's WhatsApp Business API.
"""

import hashlib
import hmac
from typing import Optional

import httpx
import structlog

from app.services.channels.base import ChannelAdapter


logger = structlog.get_logger()


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp Business API adapter.

    Handles incoming webhooks and outgoing messages via Meta Graph API.

    Usage:
        adapter = WhatsAppAdapter()
        message = await adapter.parse_webhook(payload)
        await adapter.send_message(to, text, config)
    """

    GRAPH_API_URL = "https://graph.facebook.com/v18.0"

    async def parse_webhook(self, payload: dict) -> Optional[dict]:
        """Parse incoming WhatsApp webhook.

        Args:
            payload: Raw webhook payload from Meta.

        Returns:
            Normalized message dict or None if not a message event.
        """
        try:
            entry = payload.get("entry", [])
            if not entry:
                return None

            changes = entry[0].get("changes", [])
            if not changes:
                return None

            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None

            message = messages[0]
            sender = message.get("from", "")
            timestamp = message.get("timestamp", "")
            message_type = message.get("type", "text")

            # Extract text content
            text = ""
            if message_type == "text":
                text = message.get("text", {}).get("body", "")
            elif message_type == "interactive":
                interactive = message.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    text = interactive.get("button_reply", {}).get("title", "")
                elif interactive.get("type") == "list_reply":
                    text = interactive.get("list_reply", {}).get("title", "")

            # Get contact info
            contacts = value.get("contacts", [])
            contact_name = contacts[0].get("profile", {}).get("name", "") if contacts else ""

            logger.info(
                "whatsapp_message_received",
                sender=sender,
                message_type=message_type,
            )

            return {
                "sender_id": sender,
                "message": text,
                "message_type": message_type,
                "timestamp": timestamp,
                "metadata": {
                    "contact_name": contact_name,
                    "raw_message": message,
                },
            }

        except Exception as e:
            logger.error("whatsapp_parse_error", error=str(e))
            return None

    async def send_message(
        self,
        to: str,
        message: str,
        config: dict,
    ) -> dict:
        """Send text message via WhatsApp.

        Args:
            to: Recipient phone number.
            message: Message text.
            config: WhatsApp config with phone_number_id and access_token.

        Returns:
            API response with message ID.
        """
        phone_number_id = config.get("phone_number_id")
        access_token = config.get("access_token")

        url = f"{self.GRAPH_API_URL}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info("whatsapp_message_sent", to=to)
            return response.json()

    async def send_template(
        self,
        to: str,
        template_name: str,
        config: dict,
        parameters: Optional[dict] = None,
    ) -> dict:
        """Send template message via WhatsApp.

        Args:
            to: Recipient phone number.
            template_name: Approved template name.
            config: WhatsApp config.
            parameters: Template parameters.

        Returns:
            API response with message ID.
        """
        phone_number_id = config.get("phone_number_id")
        access_token = config.get("access_token")
        language = config.get("language", "en")

        url = f"{self.GRAPH_API_URL}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}

        template_payload = {
            "name": template_name,
            "language": {"code": language},
        }

        if parameters:
            components = []
            for component_type, params in parameters.items():
                component = {"type": component_type, "parameters": params}
                components.append(component)
            template_payload["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_payload,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info("whatsapp_template_sent", to=to, template=template_name)
            return response.json()

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify WhatsApp webhook signature.

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

        # Handle sha256= prefix
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected, signature)

    async def mark_as_read(
        self,
        message_id: str,
        config: dict,
    ) -> None:
        """Mark a message as read.

        Args:
            message_id: WhatsApp message ID.
            config: WhatsApp config.
        """
        phone_number_id = config.get("phone_number_id")
        access_token = config.get("access_token")

        url = f"{self.GRAPH_API_URL}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)
