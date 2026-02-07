"""Knowledge base management endpoints."""

import tempfile
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.multi_tenant import TenantContext
from app.models.client import Client
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.api.v1.endpoints.auth import get_current_user
from app.services.knowledge.parser import DocumentParser
from app.services.knowledge.indexer import KnowledgeIndexer


router = APIRouter()


async def verify_client_access(
    client_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Client:
    """Verify user has access to client.

    Args:
        client_id: Client UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Client if access granted.

    Raises:
        HTTPException: If access denied or client not found.
    """
    if not current_user.is_superuser and current_user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    TenantContext.set_tenant(client_id)
    return client


@router.post("/upload", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    client_id: UUID,
    file: Annotated[UploadFile, File(...)],
    document_type: Annotated[str, Form(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KnowledgeDocument:
    """Upload and index a knowledge document.

    Args:
        client_id: Client UUID.
        file: Uploaded file (PDF, TXT, DOCX).
        document_type: Type of document (menu, faq, policy, etc.).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Created knowledge document.
    """
    await verify_client_access(client_id, current_user, db)

    # Validate file type
    if not DocumentParser.is_supported(file.filename or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {DocumentParser.SUPPORTED_EXTENSIONS}",
        )

    # Validate document type
    valid_types = {"menu", "faq", "policy", "hours", "general"}
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Valid: {valid_types}",
        )

    # Save file temporarily and process
    content = await file.read()

    try:
        # Parse document
        text = await DocumentParser.parse_bytes(content, file.filename or "document.txt")

        # Index document
        indexer = KnowledgeIndexer()
        result = await indexer.index_text(
            text=text,
            client_id=client_id,
            document_type=document_type,
            metadata={"filename": file.filename},
        )

        # Save to database
        doc = KnowledgeDocument(
            client_id=client_id,
            filename=file.filename or "document",
            document_type=document_type,
            content_hash=result["content_hash"],
            chunk_count=result["chunk_count"],
            vector_ids=result["vector_ids"],
            original_content=text[:10000],  # Store first 10k chars
        )

        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return doc

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_type: str | None = None,
) -> list[KnowledgeDocument]:
    """List knowledge documents for a client.

    Args:
        client_id: Client UUID.
        db: Database session.
        current_user: Authenticated user.
        document_type: Optional filter by type.

    Returns:
        List of knowledge documents.
    """
    await verify_client_access(client_id, current_user, db)

    query = select(KnowledgeDocument).where(KnowledgeDocument.client_id == client_id)
    if document_type:
        query = query.where(KnowledgeDocument.document_type == document_type)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    client_id: UUID,
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KnowledgeDocument:
    """Get a specific knowledge document.

    Args:
        client_id: Client UUID.
        document_id: Document UUID.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Knowledge document.
    """
    await verify_client_access(client_id, current_user, db)

    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.client_id == client_id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    client_id: UUID,
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a knowledge document.

    Args:
        client_id: Client UUID.
        document_id: Document UUID.
        db: Database session.
        current_user: Authenticated user.
    """
    await verify_client_access(client_id, current_user, db)

    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.client_id == client_id,
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete vectors from vector store
    if doc.vector_ids:
        indexer = KnowledgeIndexer()
        await indexer.delete_document(doc.vector_ids, client_id)

    await db.delete(doc)
    await db.commit()
