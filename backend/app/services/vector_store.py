"""Vector store service with mock and Pinecone backends."""

import math

from app.config import get_settings

# In-memory mock store - cleared between tests in conftest.py
_mock_store: dict[str, dict] = {}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _check_pinecone_embedding_compat() -> None:
    """Raise a clear error if using Pinecone with mock embeddings (dimension mismatch)."""
    from app.services.embeddings import MOCK_EMBEDDING_DIM

    settings = get_settings()
    if settings.vector_db_provider != "pinecone":
        return
    if settings.embedding_provider == "mock":
        raise ValueError(
            "Pinecone requires real embeddings (1536 dim). Set EMBEDDING_PROVIDER=openai in .env. "
            f"Mock embeddings use {MOCK_EMBEDDING_DIM} dimensions; your index expects 1536."
        )


def upsert_vectors(vectors: list[dict], tenant_id: str) -> None:
    """Store vectors with metadata.

    Each vector dict must have: id, values, metadata.
    """
    settings = get_settings()

    if settings.vector_db_provider == "pinecone":
        _check_pinecone_embedding_compat()

    if settings.vector_db_provider == "mock":
        for v in vectors:
            _mock_store[v["id"]] = {
                "id": v["id"],
                "values": v["values"],
                "metadata": {**v["metadata"], "tenant_id": str(tenant_id)},
            }
        return

    if settings.vector_db_provider == "pinecone":
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        index.upsert(
            vectors=[(v["id"], v["values"], v["metadata"]) for v in vectors],
            namespace=str(tenant_id),
        )
        return

    raise ValueError(f"Unknown vector_db_provider: {settings.vector_db_provider}")


def query_vectors(
    vector: list[float], tenant_id: str, top_k: int = 5
) -> list[dict]:
    """Query vectors by similarity, filtered by tenant_id.

    Returns list of dicts with: id, score, metadata.
    """
    settings = get_settings()

    if settings.vector_db_provider == "pinecone":
        _check_pinecone_embedding_compat()

    if settings.vector_db_provider == "mock":
        scored = []
        for entry in _mock_store.values():
            if entry["metadata"].get("tenant_id") == str(tenant_id):
                score = _cosine_similarity(vector, entry["values"])
                scored.append({
                    "id": entry["id"],
                    "score": score,
                    "metadata": entry["metadata"],
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    if settings.vector_db_provider == "pinecone":
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        results = index.query(
            vector=vector,
            top_k=top_k,
            namespace=str(tenant_id),
            include_metadata=True,
        )
        return [
            {"id": m.id, "score": m.score, "metadata": m.metadata}
            for m in results.matches
        ]

    raise ValueError(f"Unknown vector_db_provider: {settings.vector_db_provider}")


def delete_vectors(ids: list[str], tenant_id: str) -> None:
    """Delete vectors by their IDs."""
    settings = get_settings()

    if settings.vector_db_provider == "mock":
        for vid in ids:
            _mock_store.pop(vid, None)
        return

    if settings.vector_db_provider == "pinecone":
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        index.delete(ids=ids, namespace=str(tenant_id))
        return

    raise ValueError(f"Unknown vector_db_provider: {settings.vector_db_provider}")


def delete_vectors_by_document(document_id: str, tenant_id: str) -> None:
    """Delete all vectors associated with a document."""
    settings = get_settings()

    if settings.vector_db_provider == "mock":
        to_remove = [
            vid
            for vid, entry in _mock_store.items()
            if entry["metadata"].get("document_id") == str(document_id)
            and entry["metadata"].get("tenant_id") == str(tenant_id)
        ]
        for vid in to_remove:
            del _mock_store[vid]
        return

    if settings.vector_db_provider == "pinecone":
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        index.delete(
            filter={"document_id": str(document_id)},
            namespace=str(tenant_id),
        )
        return

    raise ValueError(f"Unknown vector_db_provider: {settings.vector_db_provider}")
