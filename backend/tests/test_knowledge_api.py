"""Tests for Knowledge API endpoints."""

import io
import uuid

import pytest

from app.models.knowledge import DocumentStatus, FileType, KnowledgeDocument


class TestKnowledgeUpload:
    """Tests for document upload endpoint."""

    def test_upload_txt_document(self, client, auth_headers_a, user_a, db):
        """Test uploading a valid TXT file."""
        content = b"This is test content for the knowledge base."
        file = io.BytesIO(content)

        response = client.post(
            "/api/v1/knowledge/documents",
            files={"file": ("test.txt", file, "text/plain")},
            headers=auth_headers_a,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["file_type"] == "txt"
        assert data["file_size_bytes"] == len(content)
        assert data["status"] == "processing"

    def test_upload_invalid_file_type(self, client, auth_headers_a):
        """Test uploading an unsupported file type."""
        file = io.BytesIO(b"some content")

        response = client.post(
            "/api/v1/knowledge/documents",
            files={"file": ("test.exe", file, "application/octet-stream")},
            headers=auth_headers_a,
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_requires_auth(self, client):
        """Test that upload requires authentication."""
        file = io.BytesIO(b"content")

        response = client.post(
            "/api/v1/knowledge/documents",
            files={"file": ("test.txt", file, "text/plain")},
        )

        assert response.status_code == 401


class TestKnowledgeList:
    """Tests for document listing endpoint."""

    def test_list_empty(self, client, auth_headers_a, user_a):
        """Test listing documents when none exist."""
        response = client.get(
            "/api/v1/knowledge/documents",
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_list_with_documents(self, client, auth_headers_a, user_a, db):
        """Test listing documents returns uploaded documents."""
        # Create a document directly in DB
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_a.tenant_id,
            filename="test.txt",
            file_type=FileType.txt,
            file_path="/tmp/test.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_a.id,
            chunk_count=5,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            "/api/v1/knowledge/documents",
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "test.txt"

    def test_list_pagination(self, client, auth_headers_a, user_a, db):
        """Test document list pagination."""
        # Create multiple documents
        for i in range(5):
            doc = KnowledgeDocument(
                id=uuid.uuid4(),
                tenant_id=user_a.tenant_id,
                filename=f"test{i}.txt",
                file_type=FileType.txt,
                file_path=f"/tmp/test{i}.txt",
                file_size_bytes=100,
                status=DocumentStatus.ready,
                uploaded_by=user_a.id,
                chunk_count=1,
            )
            db.add(doc)
        db.commit()

        response = client.get(
            "/api/v1/knowledge/documents?page=1&page_size=2",
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5
        assert data["has_more"] is True


class TestKnowledgeGet:
    """Tests for getting a specific document."""

    def test_get_document(self, client, auth_headers_a, user_a, db):
        """Test getting a specific document by ID."""
        doc_id = uuid.uuid4()
        doc = KnowledgeDocument(
            id=doc_id,
            tenant_id=user_a.tenant_id,
            filename="test.txt",
            file_type=FileType.txt,
            file_path="/tmp/test.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_a.id,
            chunk_count=3,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"/api/v1/knowledge/documents/{doc_id}",
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(doc_id)
        assert data["filename"] == "test.txt"

    def test_get_document_not_found(self, client, auth_headers_a, user_a):
        """Test getting a non-existent document returns 404."""
        fake_id = uuid.uuid4()

        response = client.get(
            f"/api/v1/knowledge/documents/{fake_id}",
            headers=auth_headers_a,
        )

        assert response.status_code == 404


class TestKnowledgeDelete:
    """Tests for document deletion endpoint."""

    def test_delete_document(self, client, auth_headers_a, user_a, db):
        """Test deleting a document."""
        doc_id = uuid.uuid4()
        doc = KnowledgeDocument(
            id=doc_id,
            tenant_id=user_a.tenant_id,
            filename="test.txt",
            file_type=FileType.txt,
            file_path="/tmp/test.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_a.id,
            chunk_count=0,
        )
        db.add(doc)
        db.commit()

        response = client.delete(
            f"/api/v1/knowledge/documents/{doc_id}",
            headers=auth_headers_a,
        )

        assert response.status_code == 204

        # Verify deleted
        assert db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id
        ).first() is None

    def test_delete_not_found(self, client, auth_headers_a, user_a):
        """Test deleting a non-existent document returns 404."""
        fake_id = uuid.uuid4()

        response = client.delete(
            f"/api/v1/knowledge/documents/{fake_id}",
            headers=auth_headers_a,
        )

        assert response.status_code == 404


class TestKnowledgeTenantIsolation:
    """Tests for tenant isolation in knowledge base."""

    def test_cannot_see_other_tenant_documents(
        self, client, auth_headers_a, auth_headers_b, user_a, user_b, db
    ):
        """Test that tenant A cannot see tenant B's documents."""
        # Create document for tenant B
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            tenant_id=user_b.tenant_id,
            filename="secret.txt",
            file_type=FileType.txt,
            file_path="/tmp/secret.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_b.id,
            chunk_count=1,
        )
        db.add(doc)
        db.commit()

        # Tenant A should not see tenant B's document
        response = client.get(
            "/api/v1/knowledge/documents",
            headers=auth_headers_a,
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_cannot_delete_other_tenant_document(
        self, client, auth_headers_a, user_a, user_b, db
    ):
        """Test that tenant A cannot delete tenant B's document."""
        doc_id = uuid.uuid4()
        doc = KnowledgeDocument(
            id=doc_id,
            tenant_id=user_b.tenant_id,
            filename="secret.txt",
            file_type=FileType.txt,
            file_path="/tmp/secret.txt",
            file_size_bytes=100,
            status=DocumentStatus.ready,
            uploaded_by=user_b.id,
            chunk_count=1,
        )
        db.add(doc)
        db.commit()

        response = client.delete(
            f"/api/v1/knowledge/documents/{doc_id}",
            headers=auth_headers_a,
        )

        assert response.status_code == 404

        # Document should still exist
        assert db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id
        ).first() is not None
