"""Intent routing service.

Classifies user intents and routes to appropriate handlers.
"""

from enum import Enum
from typing import Optional

import structlog

from app.services.ai.llm_gateway import LLMGateway
from app.services.ai.prompt_manager import PromptManager


logger = structlog.get_logger()


class Intent(str, Enum):
    """User intent categories."""

    GREETING = "greeting"
    HOURS = "hours"
    MENU = "menu"
    PRICE = "price"
    LOCATION = "location"
    CONTACT = "contact"
    RESERVATION = "reservation"
    COMPLAINT = "complaint"
    OTHER = "other"


class IntentRouter:
    """Classifies intents and routes messages.

    Uses LLM for intent classification with pattern-based fallback.

    Usage:
        router = IntentRouter()
        intent = await router.classify(message)
    """

    # Pattern-based shortcuts (before LLM)
    GREETING_PATTERNS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    HOURS_PATTERNS = {"hours", "open", "close", "when", "time"}
    LOCATION_PATTERNS = {"where", "address", "location", "directions", "find you"}
    CONTACT_PATTERNS = {"phone", "email", "contact", "call", "reach"}

    def __init__(self, llm: Optional[LLMGateway] = None):
        """Initialize intent router.

        Args:
            llm: Optional LLM gateway for classification.
        """
        self.llm = llm or LLMGateway()

    async def classify(self, message: str) -> Intent:
        """Classify user message intent.

        Args:
            message: User message text.

        Returns:
            Classified intent.
        """
        # Normalize message
        normalized = message.lower().strip()

        # Try pattern matching first (faster)
        pattern_intent = self._pattern_match(normalized)
        if pattern_intent:
            logger.debug("intent_pattern_match", intent=pattern_intent.value)
            return pattern_intent

        # Fall back to LLM classification
        return await self._llm_classify(message)

    def _pattern_match(self, message: str) -> Optional[Intent]:
        """Fast pattern-based intent matching.

        Args:
            message: Normalized message text.

        Returns:
            Matched intent or None.
        """
        words = set(message.split())

        # Check for greeting
        if words & self.GREETING_PATTERNS or message in self.GREETING_PATTERNS:
            return Intent.GREETING

        # Check for hours inquiry
        if words & self.HOURS_PATTERNS:
            return Intent.HOURS

        # Check for location inquiry
        if any(p in message for p in self.LOCATION_PATTERNS):
            return Intent.LOCATION

        # Check for contact inquiry
        if words & self.CONTACT_PATTERNS:
            return Intent.CONTACT

        return None

    async def _llm_classify(self, message: str) -> Intent:
        """Classify intent using LLM.

        Args:
            message: User message text.

        Returns:
            Classified intent.
        """
        prompt = PromptManager.build_intent_classification_prompt(message)

        try:
            response = await self.llm.generate(prompt, max_tokens=20, temperature=0)
            intent_str = response.strip().lower()

            # Map response to Intent enum
            try:
                return Intent(intent_str)
            except ValueError:
                logger.warning("unknown_intent", response=intent_str)
                return Intent.OTHER

        except Exception as e:
            logger.error("intent_classification_error", error=str(e))
            return Intent.OTHER

    def get_handler_for_intent(self, intent: Intent) -> str:
        """Get the handler name for an intent.

        Args:
            intent: User intent.

        Returns:
            Handler method name.
        """
        handlers = {
            Intent.GREETING: "handle_greeting",
            Intent.HOURS: "handle_rag_query",
            Intent.MENU: "handle_rag_query",
            Intent.PRICE: "handle_rag_query",
            Intent.LOCATION: "handle_rag_query",
            Intent.CONTACT: "handle_rag_query",
            Intent.RESERVATION: "handle_reservation",
            Intent.COMPLAINT: "handle_complaint",
            Intent.OTHER: "handle_rag_query",
        }
        return handlers.get(intent, "handle_rag_query")
