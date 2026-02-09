"""Tests for RAG engine service."""

import uuid

import pytest

from app.models.knowledge import DocumentStatus, FileType, KnowledgeChunk, KnowledgeDocument
from app.services.embeddings import generate_query_embedding
from app.services.rag_engine import build_rag_prompt, rag_query, retrieve_context
from app.services.vector_store import upsert_vectors


class TestRetrieveContext:
    """Tests for context retrieval."""

    def test_retrieve_empty_knowledge_base(self, db, user_a):
        """Test retrieval returns empty when no documents exist."""
        result = retrieve_context(
            query="What are your hours?",
            tenant_id=user_a.tenant_id,
            db=db,
        )

        assert result == []

    def test_retrieve_with_chunks(self, db, user_a):
        """Test retrieval returns relevant chunks."""
        # Create a document
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_a.tenant_id,
            filename="faq.txt",
            file_type=FileType.txt,
            file_path="/tmp/faq.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_a.id,
            chunk_count=1,
        )
        db.add(doc)
        db.flush()

        # Create a chunk
        chunk_id = uuid.uuid4()
        chunk = KnowledgeChunk(
            id=chunk_id,
            tenant_id=user_a.tenant_id,
            document_id=doc.id,
            chunk_index=0,
            content="Our business hours are Monday to Friday, 9 AM to 5 PM.",
            token_count=12,
        )
        db.add(chunk)
        db.commit()

        # Add to vector store
        embedding = generate_query_embedding("business hours")
        upsert_vectors(
            vectors=[{
                "id": str(chunk_id),
                "values": embedding,
                "metadata": {
                    "tenant_id": str(user_a.tenant_id),
                    "document_id": str(doc.id),
                    "chunk_id": str(chunk_id),
                },
            }],
            tenant_id=str(user_a.tenant_id),
        )

        # Query
        result = retrieve_context(
            query="What are your hours?",
            tenant_id=user_a.tenant_id,
            db=db,
        )

        assert len(result) == 1
        assert "business hours" in result[0]["content"].lower()
        assert result[0]["filename"] == "faq.txt"


class TestBuildRagPrompt:
    """Tests for RAG prompt construction."""

    def test_empty_context(self):
        """Test prompt with no context."""
        system_prompt, user_prompt = build_rag_prompt(
            query="What time do you open?",
            context_chunks=[],
        )

        assert "No relevant information" in system_prompt
        assert user_prompt == "What time do you open?"

    def test_with_context(self):
        """Test prompt with context chunks."""
        context = [
            {
                "chunk_id": "1",
                "document_id": "doc1",
                "filename": "hours.txt",
                "content": "We open at 9 AM daily.",
                "score": 0.9,
            }
        ]

        system_prompt, user_prompt = build_rag_prompt(
            query="What time do you open?",
            context_chunks=context,
        )

        assert "[Source 1: hours.txt]" in system_prompt
        assert "We open at 9 AM daily." in system_prompt
        assert user_prompt == "What time do you open?"


class TestRagQuery:
    """Tests for full RAG query flow."""

    def test_query_empty_knowledge_base(self, db, user_a):
        """Test RAG query with empty knowledge base."""
        result = rag_query(
            query="What are your hours?",
            tenant_id=user_a.tenant_id,
            db=db,
        )

        assert "response" in result
        assert result["sources"] == []
        assert result["usage"]["context_chunks"] == 0

    def test_query_with_knowledge(self, db, user_a):
        """Test RAG query returns response with sources."""
        # Create document and chunk
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_a.tenant_id,
            filename="info.txt",
            file_type=FileType.txt,
            file_path="/tmp/info.txt",
            file_size_bytes=50,
            status=DocumentStatus.ready,
            uploaded_by=user_a.id,
            chunk_count=1,
        )
        db.add(doc)
        db.flush()

        chunk_id = uuid.uuid4()
        chunk = KnowledgeChunk(
            id=chunk_id,
            tenant_id=user_a.tenant_id,
            document_id=doc.id,
            chunk_index=0,
            content="We are located at 123 Main Street.",
            token_count=8,
        )
        db.add(chunk)
        db.commit()

        # Add to vector store
        embedding = generate_query_embedding("location address")
        upsert_vectors(
            vectors=[{
                "id": str(chunk_id),
                "values": embedding,
                "metadata": {
                    "tenant_id": str(user_a.tenant_id),
                    "document_id": str(doc.id),
                    "chunk_id": str(chunk_id),
                },
            }],
            tenant_id=str(user_a.tenant_id),
        )

        result = rag_query(
            query="Where are you located?",
            tenant_id=user_a.tenant_id,
            db=db,
        )

        assert "response" in result
        assert len(result["sources"]) == 1
        assert result["sources"][0]["filename"] == "info.txt"


class TestRagTenantIsolation:
    """Tests for tenant isolation in RAG."""

    def test_cannot_retrieve_other_tenant_chunks(self, db, user_a, user_b):
        """Test that tenant A cannot retrieve tenant B's chunks."""
        # Create document for tenant B
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_b.tenant_id,
            filename="secret.txt",
            file_type=FileType.txt,
            file_path="/tmp/secret.txt",
            file_size_bytes=50,
            status=DocumentStatus.ready,
            uploaded_by=user_b.id,
            chunk_count=1,
        )
        db.add(doc)
        db.flush()

        chunk_id = uuid.uuid4()
        chunk = KnowledgeChunk(
            id=chunk_id,
            tenant_id=user_b.tenant_id,
            document_id=doc.id,
            chunk_index=0,
            content="Secret password is 12345.",
            token_count=5,
        )
        db.add(chunk)
        db.commit()

        # Add to tenant B's namespace
        embedding = generate_query_embedding("secret password")
        upsert_vectors(
            vectors=[{
                "id": str(chunk_id),
                "values": embedding,
                "metadata": {
                    "tenant_id": str(user_b.tenant_id),
                    "document_id": str(doc.id),
                    "chunk_id": str(chunk_id),
                },
            }],
            tenant_id=str(user_b.tenant_id),
        )

        # Tenant A queries - should not find tenant B's data
        result = retrieve_context(
            query="What is the secret password?",
            tenant_id=user_a.tenant_id,
            db=db,
        )

        assert result == []
