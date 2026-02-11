"""RAG (Retrieval-Augmented Generation) engine.

Combines vector search with LLM generation for accurate, contextual responses.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.services.embeddings import generate_query_embedding
from app.services.llm_gateway import generate_response
from app.services.vector_store import query_vectors


RAG_SYSTEM_PROMPT = """You are a helpful AI assistant. Answer the user's question using ONLY the provided context from the knowledge base.

When context IS provided below (real document excerpts):
- Use it to answer the question. If the user asks "what is X?" or "tell me about X" and the context describes X (or a related product/topic), answer from the context. For example, "what is Oracle?" when the documents are about Oracle Fusion Cloud should be answered using what the context says about Oracle/Oracle Fusion Cloud.
- Stay concise and only use information from the context. Do not add external knowledge.

When the context says "No relevant information found" (no document excerpts):
- Politely say you can only answer from the uploaded knowledge base and suggest they ask something related to the documents.

Rules:
- Do not make up or assume information not in the context.
- Do not answer questions about unrelated topics (e.g. other products, news, coding) when the context is not about them. Only decline when the provided context truly does not contain the answer.

Context:
{context}
"""


def retrieve_context(
    query: str,
    tenant_id: str | UUID,
    db: Session,
    top_k: int | None = None,
) -> list[dict]:
    """Retrieve relevant context chunks for a query.

    Args:
        query: The user's question
        tenant_id: Tenant ID for isolation
        db: Database session to fetch chunk content
        top_k: Number of chunks to retrieve (default from settings)

    Returns:
        List of dicts with: chunk_id, document_id, filename, content, score
    """
    settings = get_settings()
    top_k = top_k or settings.max_context_chunks

    # Generate query embedding
    query_embedding = generate_query_embedding(query)

    # Query vector store
    results = query_vectors(
        vector=query_embedding,
        tenant_id=str(tenant_id),
        top_k=top_k,
    )

    # Enrich results with chunk content from database
    enriched = []
    for result in results:
        chunk_id = result["metadata"].get("chunk_id")
        if not chunk_id:
            continue

        # Fetch chunk and document info
        chunk = (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.id == chunk_id,
                KnowledgeChunk.tenant_id == str(tenant_id),
            )
            .first()
        )
        if not chunk:
            continue

        document = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.id == chunk.document_id,
                KnowledgeDocument.tenant_id == str(tenant_id),
            )
            .first()
        )

        enriched.append({
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "filename": document.filename if document else "Unknown",
            "content": chunk.content,
            "score": result["score"],
        })

    return enriched


def build_rag_prompt(query: str, context_chunks: list[dict]) -> tuple[str, str]:
    """Build the RAG prompt with context.

    Args:
        query: User's question
        context_chunks: Retrieved context chunks

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    if not context_chunks:
        context_text = "No relevant information found in the knowledge base."
    else:
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk['filename']}]\n{chunk['content']}"
            )
        context_text = "\n\n".join(context_parts)

    system_prompt = RAG_SYSTEM_PROMPT.format(context=context_text)
    return system_prompt, query


# Default reply when no knowledge-base context is available (strict out-of-scope)
OUT_OF_SCOPE_RESPONSE = (
    "I can only answer questions based on the documents in the knowledge base. "
    "Your question doesn't seem to be covered by the uploaded content. "
    "Please ask something related to the documents that have been uploaded."
)


def rag_query(
    query: str,
    tenant_id: str | UUID,
    db: Session,
    top_k: int | None = None,
) -> dict:
    """Execute a full RAG query.

    Args:
        query: The user's question
        tenant_id: Tenant ID for isolation
        db: Database session
        top_k: Number of context chunks to retrieve

    Returns:
        dict with: response, sources, usage
    """
    # Retrieve context
    context_chunks = retrieve_context(query, tenant_id, db, top_k)

    # No relevant context: refuse to answer off-topic without calling the LLM
    if not context_chunks:
        return {
            "response": OUT_OF_SCOPE_RESPONSE,
            "sources": [],
            "usage": {
                "context_chunks": 0,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

    # Build prompt
    system_prompt, user_prompt = build_rag_prompt(query, context_chunks)

    # Generate response
    llm_result = generate_response(
        prompt=user_prompt,
        system_prompt=system_prompt,
    )

    # Format sources
    sources = [
        {
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "chunk_content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            "relevance_score": chunk["score"],
        }
        for chunk in context_chunks
    ]

    return {
        "response": llm_result["response"],
        "sources": sources,
        "usage": {
            "context_chunks": len(context_chunks),
            "prompt_tokens": llm_result.get("prompt_tokens"),
            "completion_tokens": llm_result.get("completion_tokens"),
            "total_tokens": llm_result.get("total_tokens"),
        },
    }
