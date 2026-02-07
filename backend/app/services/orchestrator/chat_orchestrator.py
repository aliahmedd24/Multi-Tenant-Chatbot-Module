"""Chat orchestrator service.

Main orchestration layer that coordinates all chat components.
"""

from typing import Optional
from uuid import UUID

import structlog

from app.services.orchestrator.session_manager import SessionManager
from app.services.orchestrator.intent_router import IntentRouter, Intent
from app.services.ai.rag_engine import RAGEngine
from app.services.ai.prompt_manager import PromptManager


logger = structlog.get_logger()


class ChatOrchestrator:
    """Main chat orchestration service.

    Coordinates session management, intent routing, and response generation.

    Usage:
        orchestrator = ChatOrchestrator()
        response = await orchestrator.process_message(
            message="What time do you open?",
            sender_id="user123",
            channel="whatsapp",
            client_id=uuid,
            client_name="Pizza Palace",
        )
    """

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        intent_router: Optional[IntentRouter] = None,
        rag_engine: Optional[RAGEngine] = None,
    ):
        """Initialize chat orchestrator.

        Args:
            session_manager: Optional session manager.
            intent_router: Optional intent router.
            rag_engine: Optional RAG engine.
        """
        self.session_manager = session_manager or SessionManager()
        self.intent_router = intent_router or IntentRouter()
        self.rag_engine = rag_engine or RAGEngine()
        self.prompt_manager = PromptManager()

    async def process_message(
        self,
        message: str,
        sender_id: str,
        channel: str,
        client_id: UUID,
        client_name: str = "Business",
        conversation_id: Optional[UUID] = None,
        response_tone: str = "professional",
        max_tokens: int = 500,
    ) -> dict:
        """Process an incoming message and generate response.

        Args:
            message: User message text.
            sender_id: External sender identifier.
            channel: Communication channel.
            client_id: Client/tenant UUID.
            client_name: Business name.
            conversation_id: Optional existing conversation ID.
            response_tone: Desired response tone.
            max_tokens: Maximum response tokens.

        Returns:
            Dict with response, conversation_id, and metadata.
        """
        logger.info(
            "process_message_start",
            client_id=str(client_id),
            channel=channel,
            message_preview=message[:50],
        )

        # 1. Get or create session context
        context = None
        if conversation_id:
            context = await self.session_manager.get_context(conversation_id)

        # 2. Classify intent
        intent = await self.intent_router.classify(message)
        logger.info("intent_classified", intent=intent.value)

        # 3. Get conversation history
        history = []
        if conversation_id:
            history = await self.session_manager.get_history(conversation_id)

        # 4. Generate response based on intent
        if intent == Intent.GREETING:
            response = await self._handle_greeting(client_name)
        else:
            response = await self._handle_rag_query(
                message=message,
                client_id=client_id,
                client_name=client_name,
                response_tone=response_tone,
                max_tokens=max_tokens,
                history=history,
            )

        # 5. Save to session
        if conversation_id:
            await self.session_manager.add_message(conversation_id, "user", message)
            await self.session_manager.add_message(conversation_id, "assistant", response)

        logger.info(
            "process_message_complete",
            client_id=str(client_id),
            intent=intent.value,
            response_length=len(response),
        )

        return {
            "response": response,
            "conversation_id": conversation_id,
            "intent": intent.value,
            "metadata": {
                "channel": channel,
                "sender_id": sender_id,
            },
        }

    async def _handle_greeting(self, client_name: str) -> str:
        """Handle greeting intent.

        Args:
            client_name: Business name.

        Returns:
            Greeting response.
        """
        return self.prompt_manager.build_greeting_prompt(client_name)

    async def _handle_rag_query(
        self,
        message: str,
        client_id: UUID,
        client_name: str,
        response_tone: str,
        max_tokens: int,
        history: Optional[list[dict]] = None,
    ) -> str:
        """Handle RAG-based query.

        Args:
            message: User message.
            client_id: Client UUID.
            client_name: Business name.
            response_tone: Response tone.
            max_tokens: Max response tokens.
            history: Conversation history.

        Returns:
            RAG-generated response.
        """
        return await self.rag_engine.generate_response(
            query=message,
            client_id=client_id,
            client_name=client_name,
            response_tone=response_tone,
            max_tokens=max_tokens,
            history=history,
        )

    async def start_conversation(
        self,
        sender_id: str,
        channel: str,
        client_id: UUID,
        client_name: str,
    ) -> dict:
        """Start a new conversation with greeting.

        Args:
            sender_id: External sender identifier.
            channel: Communication channel.
            client_id: Client UUID.
            client_name: Business name.

        Returns:
            Dict with greeting and conversation info.
        """
        greeting = await self._handle_greeting(client_name)

        return {
            "response": greeting,
            "intent": Intent.GREETING.value,
            "metadata": {
                "channel": channel,
                "sender_id": sender_id,
                "is_new_conversation": True,
            },
        }

    async def close(self) -> None:
        """Close orchestrator resources."""
        await self.session_manager.close()
