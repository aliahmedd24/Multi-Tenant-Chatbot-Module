"""Text embedding service.

Provides text-to-vector embedding using OpenAI's embedding models.
"""

import structlog
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings


logger = structlog.get_logger()


class Embedder:
    """Text embedding service using OpenAI.

    Generates vector embeddings for semantic search.

    Usage:
        embedder = Embedder()
        embedding = await embedder.embed("Hello world")
        embeddings = await embedder.embed_batch(["Hello", "World"])
    """

    def __init__(self, model: str = "text-embedding-ada-002"):
        """Initialize embedder.

        Args:
            model: OpenAI embedding model name.
        """
        self.model = model
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._dimension = 1536  # ada-002 dimension

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        logger.debug("embed_start", text_length=len(text))

        response = await self._client.embeddings.create(
            model=self.model,
            input=text,
        )

        embedding = response.data[0].embedding
        logger.debug("embed_complete", dimension=len(embedding))
        return embedding

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.
            batch_size: Maximum texts per API call.

        Returns:
            List of embedding vectors.
        """
        logger.info("embed_batch_start", count=len(texts))
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._client.embeddings.create(
                model=self.model,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        logger.info("embed_batch_complete", count=len(embeddings))
        return embeddings
