"""Tests for the vector store service."""

import uuid

from app.services.embeddings import generate_embeddings
from app.services.vector_store import (
    _mock_store,
    delete_vectors,
    delete_vectors_by_document,
    query_vectors,
    upsert_vectors,
)


def setup_function():
    """Clear mock store before each test."""
    _mock_store.clear()


def teardown_function():
    """Clear mock store after each test."""
    _mock_store.clear()


TENANT_A = str(uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
TENANT_B = str(uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


def _make_vectors(texts: list[str], doc_id: str, tenant_id: str) -> list[dict]:
    """Helper to create vector dicts from texts."""
    embeddings = generate_embeddings(texts)
    return [
        {
            "id": f"{doc_id}_chunk_{i}",
            "values": emb,
            "metadata": {
                "content": text,
                "document_id": doc_id,
                "chunk_index": i,
            },
        }
        for i, (text, emb) in enumerate(zip(texts, embeddings))
    ]


def test_upsert_and_query():
    doc_id = str(uuid.uuid4())
    vectors = _make_vectors(["vegan burger", "chicken wrap"], doc_id, TENANT_A)
    upsert_vectors(vectors, TENANT_A)

    query_emb = generate_embeddings(["vegan burger"])[0]
    results = query_vectors(query_emb, TENANT_A, top_k=2)

    assert len(results) == 2
    assert results[0]["metadata"]["content"] == "vegan burger"
    assert results[0]["score"] > results[1]["score"]


def test_query_respects_top_k():
    doc_id = str(uuid.uuid4())
    vectors = _make_vectors(
        ["item one", "item two", "item three", "item four"],
        doc_id,
        TENANT_A,
    )
    upsert_vectors(vectors, TENANT_A)

    query_emb = generate_embeddings(["item"])[0]
    results = query_vectors(query_emb, TENANT_A, top_k=2)
    assert len(results) == 2


def test_tenant_isolation():
    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())

    vectors_a = _make_vectors(["tenant A secret data"], doc_a, TENANT_A)
    vectors_b = _make_vectors(["tenant B secret data"], doc_b, TENANT_B)

    upsert_vectors(vectors_a, TENANT_A)
    upsert_vectors(vectors_b, TENANT_B)

    # Query as Tenant A should NOT return Tenant B data
    query_emb = generate_embeddings(["secret data"])[0]
    results_a = query_vectors(query_emb, TENANT_A)

    for r in results_a:
        assert r["metadata"]["tenant_id"] == TENANT_A


def test_delete_vectors():
    doc_id = str(uuid.uuid4())
    vectors = _make_vectors(["to delete"], doc_id, TENANT_A)
    upsert_vectors(vectors, TENANT_A)

    assert len(_mock_store) == 1

    delete_vectors([vectors[0]["id"]], TENANT_A)
    assert len(_mock_store) == 0


def test_delete_vectors_by_document():
    doc_id = str(uuid.uuid4())
    other_doc = str(uuid.uuid4())

    vectors = _make_vectors(["chunk one", "chunk two"], doc_id, TENANT_A)
    other_vectors = _make_vectors(["other chunk"], other_doc, TENANT_A)

    upsert_vectors(vectors, TENANT_A)
    upsert_vectors(other_vectors, TENANT_A)

    assert len(_mock_store) == 3

    delete_vectors_by_document(doc_id, TENANT_A)

    # Only the other document's vectors should remain
    assert len(_mock_store) == 1
    remaining = list(_mock_store.values())[0]
    assert remaining["metadata"]["document_id"] == other_doc


def test_empty_query_returns_empty():
    query_emb = generate_embeddings(["anything"])[0]
    results = query_vectors(query_emb, TENANT_A)
    assert results == []
