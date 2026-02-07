"""Knowledge retrieval service.

Provides semantic search over the knowledge base.
"""

from typing import Optional
from uuid import UUID

import structlog

from app.services.ai.embedder import Embedder
from app.services.ai.vector_store import VectorStore


logger = structlog.get_logger()


class KnowledgeRetriever:
    """Retrieves relevant knowledge from the vector store.

    Provides semantic search with tenant isolation.

    Usage:
        retriever = KnowledgeRetriever()
        results = await retriever.search(
            query="What are your hours?",
            client_id=uuid,
        )
    """

    def __init__(self, embedder: Optional[Embedder] = None):
        """Initialize retriever.

        Args:
            embedder: Optional embedder instance.
        """
        self.embedder = embedder or Embedder()

    async def search(
        self,
        query: str,
        client_id: UUID,
        top_k: int = 5,
        document_type: Optional[str] = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Search for relevant knowledge.

        Args:
            query: Search query.
            client_id: Client/tenant UUID.
            top_k: Maximum results to return.
            document_type: Optional filter by document type.
            min_score: Minimum similarity score threshold.

        Returns:
            List of matching results with text, score, and metadata.
        """
        logger.info(
            "knowledge_search_start",
            client_id=str(client_id),
            query=query[:50],
            top_k=top_k,
        )

        # Generate query embedding
        query_embedding = await self.embedder.embed(query)

        # Build filter
        filter_dict = None
        if document_type:
            filter_dict = {"document_type": document_type}

        # Search vector store
        results = await VectorStore.query(
            vector=query_embedding,
            namespace=str(client_id),
            top_k=top_k,
            filter=filter_dict,
        )

        # Process and filter results
        matches = []
        for match in results.get("matches", []):
            score = match.get("score", 0)
            if score >= min_score:
                metadata = match.get("metadata", {})
                matches.append({
                    "id": match.get("id"),
                    "text": metadata.get("text", ""),
                    "score": score,
                    "document_type": metadata.get("document_type"),
                    "metadata": metadata,
                })

        logger.info(
            "knowledge_search_complete",
            client_id=str(client_id),
            result_count=len(matches),
        )

        return matches

    async def get_context(
        self,
        query: str,
        client_id: UUID,
        top_k: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """Get formatted context for RAG.

        Retrieves relevant chunks and formats them as context string.

        Args:
            query: Search query.
            client_id: Client/tenant UUID.
            top_k: Maximum results.
            max_tokens: Approximate max token limit for context.

        Returns:
            Formatted context string.
        """
        matches = await self.search(query, client_id, top_k=top_k)

        context_parts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Approximate chars per token

        for match in matches:
            text = match.get("text", "")
            if total_chars + len(text) > char_limit:
                break
            context_parts.append(text)
            total_chars += len(text)

        return "\n\n".join(context_parts)

    async def search_by_type(
        self,
        client_id: UUID,
        document_type: str,
        top_k: int = 10,
    ) -> list[dict]:
        """Get all knowledge of a specific type.

        Useful for listing menu items, FAQs, etc.

        Args:
            client_id: Client/tenant UUID.
            document_type: Document type to retrieve.
            top_k: Maximum results.

        Returns:
            List of matching results.
        """
        # Use a generic query to get all items of this type
        return await self.search(
            query=document_type,
            client_id=client_id,
            top_k=top_k,
            document_type=document_type,
        )
