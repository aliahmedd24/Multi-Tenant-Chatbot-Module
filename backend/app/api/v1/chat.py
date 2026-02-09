"""Chat API endpoint for RAG-powered conversations."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, SourceDocument, UsageMetrics
from app.services.rag_engine import rag_query

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a RAG-powered response.

    The response is generated using the tenant's knowledge base.
    Sources used to generate the response are included.
    """
    result = rag_query(
        query=request.message,
        tenant_id=current_user.tenant_id,
        db=db,
    )

    return ChatResponse(
        response=result["response"],
        sources=[
            SourceDocument(
                document_id=source["document_id"],
                filename=source["filename"],
                chunk_content=source["chunk_content"],
                relevance_score=source["relevance_score"],
            )
            for source in result["sources"]
        ],
        usage=UsageMetrics(
            context_chunks=result["usage"]["context_chunks"],
            prompt_tokens=result["usage"]["prompt_tokens"],
            completion_tokens=result["usage"]["completion_tokens"],
            total_tokens=result["usage"]["total_tokens"],
        ),
    )
