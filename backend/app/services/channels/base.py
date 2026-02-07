"""Base channel adapter.

Abstract base class for all channel integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ChannelAdapter(ABC):
    """Abstract base class for channel adapters.

    All channel integrations (WhatsApp, Instagram, etc.) should
    inherit from this class and implement the required methods.
    """

    @abstractmethod
    async def parse_webhook(self, payload: dict) -> Optional[dict]:
        """Parse incoming webhook payload.

        Args:
            payload: Raw webhook payload.

        Returns:
            Normalized message dict with keys:
            - sender_id: str
            - message: str
            - message_type: str (text, image, etc.)
            - timestamp: str
            - metadata: dict
        """
        pass

    @abstractmethod
    async def send_message(
        self,
        to: str,
        message: str,
        config: dict,
    ) -> dict:
        """Send a message to a user.

        Args:
            to: Recipient identifier.
            message: Message text.
            config: Channel-specific configuration.

        Returns:
            Send result with message ID.
        """
        pass

    @abstractmethod
    async def send_template(
        self,
        to: str,
        template_name: str,
        config: dict,
        parameters: Optional[dict] = None,
    ) -> dict:
        """Send a template message.

        Args:
            to: Recipient identifier.
            template_name: Template name.
            config: Channel-specific configuration.
            parameters: Template parameters.

        Returns:
            Send result with message ID.
        """
        pass

    @abstractmethod
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature.

        Args:
            payload: Raw request body.
            signature: Signature from header.
            secret: Shared secret.

        Returns:
            True if signature is valid.
        """
        pass
