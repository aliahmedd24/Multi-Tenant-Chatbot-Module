"""Knowledge base management API endpoints.

All endpoints enforce tenant isolation via get_current_user dependency.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.knowledge import DocumentStatus, FileType, KnowledgeChunk, KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.audit import log_action
from app.services.vector_store import delete_vectors_by_document
from app.utils.file_handler import delete_file, save_upload, validate_file

router = APIRouter()


@router.post("/documents", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document to the knowledge base.

    The document will be validated, saved, and queued for processing.
    Processing happens asynchronously via Celery worker.
    """
    settings = get_settings()

    # Validate file
    file_data = await file.read()
    file_size = len(file_data)
    ext = validate_file(file.filename or "file", file_size, settings)

    # Check document count limit
    doc_count = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.tenant_id == current_user.tenant_id)
        .count()
    )
    if doc_count >= settings.max_files_per_tenant:
        raise HTTPException(
            status_code=400,
            detail=f"Document limit reached ({settings.max_files_per_tenant} documents per tenant)",
        )

    # Generate document ID and save file first
    doc_id = uuid.uuid4()
    file_path = save_upload(
        tenant_id=str(current_user.tenant_id),
        document_id=str(doc_id),
        filename=file.filename or "file",
        file_data=file_data,
        upload_dir=settings.upload_dir,
    )

    # Create document record with file_path
    document = KnowledgeDocument(
        id=doc_id,
        tenant_id=current_user.tenant_id,
        filename=file.filename or "uploaded_file",
        file_type=FileType(ext),
        file_path=file_path,
        file_size_bytes=file_size,
        status=DocumentStatus.processing,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow(),
        chunk_count=0,
    )
    db.add(document)
    db.commit()

    # Log the action
    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="document_upload",
        resource_type="knowledge_document",
        resource_id=str(doc_id),
        details={"filename": file.filename, "file_size": file_size},
    )

    # Queue for processing (Celery task), or process synchronously if Celery unavailable
    try:
        from app.workers.document_tasks import process_document_task

        process_document_task.delay(str(doc_id), str(current_user.tenant_id))
        message = "Document uploaded and queued for processing"
    except Exception:
        # Celery/Redis not running: run same task synchronously so documents are usable
        try:
            from app.workers.document_tasks import process_document_task

            process_document_task.apply(args=(str(doc_id), str(current_user.tenant_id)))
        except Exception as sync_err:
            try:
                from app.workers.document_tasks import process_document_sync

                process_document_sync(str(doc_id), str(current_user.tenant_id))
            except Exception as e:
                db.refresh(document)
                err_msg = getattr(document, "processing_error", None) or str(e)
                raise HTTPException(
                    status_code=422,
                    detail=f"Document processing failed: {err_msg[:300]}",
                ) from e
        db.refresh(document)
        message = "Document uploaded and processed"

    return DocumentUploadResponse(
        id=doc_id,
        filename=document.filename,
        file_type=document.file_type,
        file_size_bytes=file_size,
        status=document.status,
        message=message,
    )


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents in the tenant's knowledge base."""
    query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.tenant_id == current_user.tenant_id
    )

    total = query.count()
    documents = (
        query.order_by(KnowledgeDocument.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific document."""
    document = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.model_validate(document)


@router.post("/documents/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run processing for a document (e.g. stuck in processing or previously failed)."""
    document = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.file_path:
        raise HTTPException(status_code=400, detail="Document has no file path")

    # Remove existing chunks and vectors so we don't duplicate
    try:
        delete_vectors_by_document(str(document_id), str(current_user.tenant_id))
    except Exception:
        pass
    db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == document_id,
        KnowledgeChunk.tenant_id == current_user.tenant_id,
    ).delete()
    document.status = DocumentStatus.processing
    document.processing_error = None
    document.chunk_count = 0
    document.processed_at = None
    db.commit()
    db.refresh(document)

    try:
        from app.workers.document_tasks import process_document_task

        process_document_task.delay(str(document_id), str(current_user.tenant_id))
    except Exception:
        try:
            from app.workers.document_tasks import process_document_task

            process_document_task.apply(args=(str(document_id), str(current_user.tenant_id)))
        except Exception as e:
            try:
                from app.workers.document_tasks import process_document_sync

                process_document_sync(str(document_id), str(current_user.tenant_id))
            except Exception as sync_e:
                db.refresh(document)
                err_msg = getattr(document, "processing_error", None) or str(sync_e)
                raise HTTPException(
                    status_code=422,
                    detail=f"Reprocessing failed: {err_msg[:300]}",
                ) from sync_e
    db.refresh(document)
    return DocumentResponse.model_validate(document)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and all its chunks and vectors.

    This operation is irreversible. The file will be removed from disk,
    chunks deleted from the database, and vectors removed from the vector store.
    """
    document = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete vectors from vector store
    try:
        delete_vectors_by_document(str(document_id), str(current_user.tenant_id))
    except Exception:
        pass  # Vector store deletion is best-effort

    # Delete file from disk
    if document.file_path:
        delete_file(document.file_path)

    # Delete chunks (cascades from relationship)
    db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == document_id,
        KnowledgeChunk.tenant_id == current_user.tenant_id,
    ).delete()

    # Delete document
    db.delete(document)
    db.commit()

    # Log the action
    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="document_delete",
        resource_type="knowledge_document",
        resource_id=str(document_id),
        details={"filename": document.filename},
    )

    return None
