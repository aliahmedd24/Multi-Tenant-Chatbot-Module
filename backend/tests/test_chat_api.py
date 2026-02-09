"""Tests for Chat API endpoint."""

import uuid

import pytest

from app.models.knowledge import DocumentStatus, FileType, KnowledgeChunk, KnowledgeDocument
from app.services.embeddings import generate_query_embedding
from app.services.vector_store import upsert_vectors


class TestChatEndpoint:
    """Tests for the /chat endpoint."""

    def test_chat_requires_auth(self, client):
        """Test that chat requires authentication."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 401

    def test_chat_empty_message(self, client, auth_headers_a, user_a):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/v1/chat",
            json={"message": ""},
            headers=auth_headers_a,
        )

        assert response.status_code == 422

    def test_chat_with_empty_knowledge_base(self, client, auth_headers_a, user_a):
        """Test chat with no documents returns appropriate response."""
        response = client.post(
            "/api/v1/chat",
            json={"message": "What are your hours?"},
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["sources"] == []
        assert data["usage"]["context_chunks"] == 0

    def test_chat_with_knowledge(self, client, auth_headers_a, user_a, db):
        """Test chat with knowledge returns response with sources."""
        # Create document and chunk
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_a.tenant_id,
            filename="hours.txt",
            file_type=FileType.txt,
            file_path="/tmp/hours.txt",
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
            content="Our hours are Monday to Friday, 9 AM to 5 PM.",
            token_count=12,
        )
        db.add(chunk)
        db.commit()

        # Add to vector store
        embedding = generate_query_embedding("hours open close")
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

        response = client.post(
            "/api/v1/chat",
            json={"message": "What are your hours?"},
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["filename"] == "hours.txt"


class TestChatTenantIsolation:
    """Tests for tenant isolation in chat."""

    def test_chat_isolated_between_tenants(
        self, client, auth_headers_a, auth_headers_b, user_a, user_b, db
    ):
        """Test that tenant A cannot access tenant B's knowledge via chat."""
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
            content="The secret code is ABC123.",
            token_count=6,
        )
        db.add(chunk)
        db.commit()

        # Add to tenant B's namespace
        embedding = generate_query_embedding("secret code")
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

        # Tenant A queries for secret - should NOT find it
        response = client.post(
            "/api/v1/chat",
            json={"message": "What is the secret code?"},
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have no sources from tenant B
        assert data["sources"] == []
        # Response should not contain the secret
        assert "ABC123" not in data["response"]
