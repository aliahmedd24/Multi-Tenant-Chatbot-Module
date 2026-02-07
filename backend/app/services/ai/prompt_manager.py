"""Prompt management service.

Provides template-based prompt construction for consistent LLM interactions.
"""

from typing import Optional


class PromptManager:
    """Manages prompt templates for LLM interactions.

    Provides consistent, customizable prompts for different use cases.
    """

    # Default RAG system prompt
    RAG_SYSTEM_PROMPT = """You are an AI assistant for {client_name}.

RULES:
1. ONLY use information from the provided CONTEXT
2. If the answer is not in the CONTEXT, say "I don't have that information"
3. NEVER make up information about prices, offers, or availability
4. Use a {response_tone} tone
5. Keep responses concise and helpful
6. Stay on topic"""

    # Default RAG user prompt template
    RAG_PROMPT_TEMPLATE = """CONTEXT:
{context}

QUESTION: {query}

Answer the question using ONLY the information from the context above."""

    # Fallback when no context available
    NO_CONTEXT_PROMPT = """You are an AI assistant for {client_name}.

The user asked: "{query}"

Unfortunately, I don't have specific information to answer this question.
Please provide a polite response explaining that you don't have that information
and suggest they contact the business directly."""

    @staticmethod
    def build_rag_prompt(
        query: str,
        context: str,
        client_name: str = "Business",
        response_tone: str = "professional",
    ) -> str:
        """Build a RAG prompt with context.

        Args:
            query: User query.
            context: Retrieved knowledge context.
            client_name: Name of the business.
            response_tone: Desired response tone.

        Returns:
            Formatted prompt string.
        """
        if not context.strip():
            return PromptManager.NO_CONTEXT_PROMPT.format(
                client_name=client_name,
                query=query,
            )

        system = PromptManager.RAG_SYSTEM_PROMPT.format(
            client_name=client_name,
            response_tone=response_tone,
        )

        user_prompt = PromptManager.RAG_PROMPT_TEMPLATE.format(
            context=context,
            query=query,
        )

        return f"{system}\n\n{user_prompt}"

    @staticmethod
    def build_greeting_prompt(
        client_name: str,
        welcome_message: Optional[str] = None,
    ) -> str:
        """Build a welcome/greeting prompt.

        Args:
            client_name: Name of the business.
            welcome_message: Custom welcome message.

        Returns:
            Greeting prompt.
        """
        if welcome_message:
            return welcome_message

        return f"Hello! Welcome to {client_name}. How can I help you today?"

    @staticmethod
    def build_clarification_prompt(
        query: str,
        client_name: str,
    ) -> str:
        """Build a clarification request prompt.

        Args:
            query: Original user query.
            client_name: Name of the business.

        Returns:
            Clarification request prompt.
        """
        return f"""The user asked: "{query}"

This question is unclear or ambiguous. Generate a polite response
asking for clarification. You represent {client_name}."""

    @staticmethod
    def build_intent_classification_prompt(query: str) -> str:
        """Build a prompt for intent classification.

        Args:
            query: User query to classify.

        Returns:
            Intent classification prompt.
        """
        return f"""Classify the following user message into one of these intents:
- greeting: Hello, hi, hey
- hours: Questions about opening hours
- menu: Questions about products/menu
- price: Questions about pricing
- location: Questions about address/location
- contact: Requests for contact information
- reservation: Booking/reservation requests
- complaint: Complaints or issues
- other: Anything else

Message: "{query}"

Return ONLY the intent name, nothing else."""
