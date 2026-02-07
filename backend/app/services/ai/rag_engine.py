"""RAG (Retrieval Augmented Generation) Engine.

Orchestrates the RAG pipeline: retrieve → augment → generate.
"""

from typing import Optional
from uuid import UUID

import structlog

from app.services.ai.embedder import Embedder
from app.services.ai.vector_store import VectorStore
from app.services.ai.llm_gateway import LLMGateway
from app.services.ai.prompt_manager import PromptManager


logger = structlog.get_logger()


class RAGEngine:
    """RAG pipeline for knowledge-grounded responses.

    Retrieves relevant context from the knowledge base and uses it
    to augment LLM prompts for accurate, grounded responses.

    Usage:
        rag = RAGEngine()
        response = await rag.generate_response(
            query="What are your hours?",
            client_id=client_uuid,
        )
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        llm: Optional[LLMGateway] = None,
    ):
        """Initialize RAG engine.

        Args:
            embedder: Optional embedder instance.
            llm: Optional LLM gateway instance.
        """
        self.embedder = embedder or Embedder()
        self.llm = llm or LLMGateway()
        self.prompt_manager = PromptManager()

    async def retrieve_context(
        self,
        query: str,
        client_id: UUID,
        top_k: int = 5,
    ) -> list[dict]:
        """Retrieve relevant context from knowledge base.

        Args:
            query: User query.
            client_id: Client/tenant UUID.
            top_k: Number of results to retrieve.

        Returns:
            List of matching documents with text and score.
        """
        logger.info("rag_retrieve_start", client_id=str(client_id), query=query[:50])

        # Generate query embedding
        query_embedding = await self.embedder.embed(query)

        # Search vector store with tenant namespace
        results = await VectorStore.query(
            vector=query_embedding,
            namespace=str(client_id),
            top_k=top_k,
        )

        matches = results.get("matches", [])
        logger.info(
            "rag_retrieve_complete",
            client_id=str(client_id),
            match_count=len(matches),
        )

        return matches

    async def generate_response(
        self,
        query: str,
        client_id: UUID,
        client_name: str = "Business",
        response_tone: str = "professional",
        max_tokens: int = 500,
        history: Optional[list[dict]] = None,
    ) -> str:
        """Generate RAG-powered response.

        Args:
            query: User query.
            client_id: Client/tenant UUID.
            client_name: Business name for personalization.
            response_tone: Tone of response (professional, friendly, etc.).
            max_tokens: Maximum response tokens.
            history: Optional conversation history.

        Returns:
            Generated response grounded in knowledge base.
        """
        logger.info(
            "rag_generate_start",
            client_id=str(client_id),
            query=query[:50],
        )

        # 1. Retrieve relevant context
        matches = await self.retrieve_context(query, client_id, top_k=5)

        # 2. Build context string from matches
        context_texts = []
        for match in matches:
            metadata = match.get("metadata", {})
            text = metadata.get("text", "")
            if text:
                context_texts.append(text)

        context = "\n".join(context_texts) if context_texts else ""

        # 3. Build prompt
        prompt = self.prompt_manager.build_rag_prompt(
            query=query,
            context=context,
            client_name=client_name,
            response_tone=response_tone,
        )

        # 4. Generate response
        if history:
            response = await self.llm.generate_with_history(
                messages=history + [{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
        else:
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=max_tokens,
            )

        logger.info(
            "rag_generate_complete",
            client_id=str(client_id),
            response_length=len(response),
            context_used=bool(context_texts),
        )

        return response

    async def generate_with_fallback(
        self,
        query: str,
        client_id: UUID,
        client_name: str = "Business",
        fallback_message: str = "I don't have information about that. Please contact us directly.",
        **kwargs,
    ) -> str:
        """Generate response with fallback for empty context.

        If no relevant context is found, returns a fallback message
        instead of hallucinating.

        Args:
            query: User query.
            client_id: Client/tenant UUID.
            client_name: Business name.
            fallback_message: Message when no context found.
            **kwargs: Additional arguments for generate_response.

        Returns:
            Generated response or fallback message.
        """
        matches = await self.retrieve_context(query, client_id, top_k=5)

        # Check if any matches have sufficient score
        has_relevant_context = any(
            match.get("score", 0) > 0.7 for match in matches
        )

        if not has_relevant_context:
            logger.info(
                "rag_fallback_used",
                client_id=str(client_id),
                query=query[:50],
            )
            return fallback_message

        return await self.generate_response(
            query=query,
            client_id=client_id,
            client_name=client_name,
            **kwargs,
        )
