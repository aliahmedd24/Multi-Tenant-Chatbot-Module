"""Celery tasks for async document processing."""

import uuid
from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.knowledge import DocumentStatus, KnowledgeChunk, KnowledgeDocument
from app.services.document_processor import extract_text
from app.services.embeddings import generate_embeddings
from app.services.vector_store import upsert_vectors
from app.utils.text_chunker import chunk_text


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str, tenant_id: str) -> dict:
    """Process a document: extract text, chunk, embed, and store vectors.

    Args:
        document_id: UUID of the document to process
        tenant_id: Tenant UUID for isolation

    Returns:
        dict with processing result
    """
    db: Session = SessionLocal()
    settings = get_settings()

    try:
        # Fetch document
        document = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.tenant_id == tenant_id,
            )
            .first()
        )

        if not document:
            return {"status": "error", "message": "Document not found"}

        # Update status to processing
        document.status = DocumentStatus.processing
        db.commit()

        # Extract text from file
        text = extract_text(document.file_path, document.file_type)

        if not text.strip():
            document.status = DocumentStatus.failed
            document.processing_error = "No text content extracted from document"
            db.commit()
            return {"status": "error", "message": "No text content"}

        # Chunk the text
        chunks = chunk_text(
            text=text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        if not chunks:
            document.status = DocumentStatus.failed
            document.processing_error = "Failed to create text chunks"
            db.commit()
            return {"status": "error", "message": "No chunks created"}

        # Generate embeddings for all chunks
        chunk_texts = [c["content"] for c in chunks]
        embeddings = generate_embeddings(chunk_texts)

        # Create chunk records and vector entries
        vectors = []
        for chunk_data, embedding in zip(chunks, embeddings):
            chunk_id = uuid.uuid4()

            # Create database record
            chunk = KnowledgeChunk(
                id=chunk_id,
                tenant_id=tenant_id,
                document_id=document.id,
                chunk_index=chunk_data["index"],
                content=chunk_data["content"],
                token_count=chunk_data["token_count"],
            )
            db.add(chunk)

            # Prepare vector for storage
            vectors.append({
                "id": str(chunk_id),
                "values": embedding,
                "metadata": {
                    "tenant_id": tenant_id,
                    "document_id": str(document_id),
                    "chunk_id": str(chunk_id),
                    "chunk_index": chunk_data["index"],
                },
            })

        # Store vectors in vector store
        upsert_vectors(vectors, tenant_id)

        # Update document status
        document.status = DocumentStatus.ready
        document.processed_at = datetime.utcnow()
        document.chunk_count = len(chunks)
        db.commit()

        return {
            "status": "success",
            "document_id": document_id,
            "chunk_count": len(chunks),
        }

    except Exception as e:
        db.rollback()

        # Update document with error
        try:
            document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == document_id
            ).first()
            if document:
                document.status = DocumentStatus.failed
                document.processing_error = str(e)[:500]
                db.commit()
        except Exception:
            pass

        # Retry on transient errors
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


def process_document_sync(document_id: str, tenant_id: str) -> dict:
    """Synchronous version of document processing for testing.

    Used when Celery is not available.
    """
    # Create a fake task context
    class FakeTask:
        def retry(self, exc, countdown):
            raise exc

    fake_task = FakeTask()
    return process_document_task.__wrapped__(fake_task, document_id, tenant_id)
