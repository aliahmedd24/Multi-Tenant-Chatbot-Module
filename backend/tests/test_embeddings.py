"""Tests for the embedding generation service."""

from app.services.embeddings import (
    MOCK_EMBEDDING_DIM,
    generate_embeddings,
    generate_query_embedding,
)


def test_mock_embedding_returns_correct_dimensions():
    result = generate_embeddings(["hello world"])
    assert len(result) == 1
    assert len(result[0]) == MOCK_EMBEDDING_DIM


def test_mock_embedding_batch():
    texts = ["hello", "world", "test"]
    result = generate_embeddings(texts)
    assert len(result) == 3
    for emb in result:
        assert len(emb) == MOCK_EMBEDDING_DIM


def test_mock_embedding_deterministic():
    text = "the same text"
    emb1 = generate_embeddings([text])[0]
    emb2 = generate_embeddings([text])[0]
    assert emb1 == emb2


def test_mock_embedding_different_texts_differ():
    emb1 = generate_embeddings(["text one"])[0]
    emb2 = generate_embeddings(["text two"])[0]
    assert emb1 != emb2


def test_mock_embedding_values_normalized():
    result = generate_embeddings(["some text"])[0]
    for val in result:
        assert -1.0 <= val <= 1.0


def test_query_embedding_convenience():
    result = generate_query_embedding("test query")
    assert len(result) == MOCK_EMBEDDING_DIM
    assert isinstance(result, list)
