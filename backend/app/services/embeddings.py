"""Embedding generation service with mock and OpenAI backends."""

import hashlib
import struct

from app.config import get_settings

MOCK_EMBEDDING_DIM = 384


def _mock_embedding(text: str) -> list[float]:
    """Generate a deterministic fake embedding from text hash."""
    h = hashlib.sha256(text.encode()).digest()
    # Repeat hash bytes to fill MOCK_EMBEDDING_DIM floats (4 bytes each)
    repeated = h * ((MOCK_EMBEDDING_DIM * 4 // len(h)) + 1)
    values = struct.unpack(f"{MOCK_EMBEDDING_DIM}f", repeated[: MOCK_EMBEDDING_DIM * 4])
    # Normalize to [-1, 1] range
    max_val = max(abs(v) for v in values) or 1.0
    return [v / max_val for v in values]


def generate_embeddings(
    texts: list[str], model: str | None = None
) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Uses mock or OpenAI backend based on settings.embedding_provider.
    """
    settings = get_settings()
    provider = settings.embedding_provider

    if provider == "mock":
        return [_mock_embedding(t) for t in texts]

    if provider == "openai":
        import openai

        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=model or settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    raise ValueError(f"Unknown embedding provider: {provider}")


def generate_query_embedding(text: str, model: str | None = None) -> list[float]:
    """Generate a single embedding for a query string."""
    return generate_embeddings([text], model=model)[0]
