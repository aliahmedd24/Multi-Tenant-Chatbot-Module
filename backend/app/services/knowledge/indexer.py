"""Knowledge indexing service.

Orchestrates the document processing pipeline: parse → chunk → embed → store.
"""

from typing import Optional
from uuid import UUID, uuid4

import structlog

from app.services.knowledge.parser import DocumentParser
from app.services.knowledge.chunker import TextChunker
from app.services.ai.embedder import Embedder
from app.services.ai.vector_store import VectorStore


logger = structlog.get_logger()


class KnowledgeIndexer:
    """Indexes documents into the vector store.

    Handles the complete pipeline from file to searchable vectors.

    Usage:
        indexer = KnowledgeIndexer()
        doc_info = await indexer.index_document(
            file_path="/path/to/menu.pdf",
            client_id=uuid,
            document_type="menu",
        )
    """

    def __init__(
        self,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[Embedder] = None,
    ):
        """Initialize indexer.

        Args:
            chunker: Optional text chunker instance.
            embedder: Optional embedder instance.
        """
        self.chunker = chunker or TextChunker(chunk_size=1000, overlap=200)
        self.embedder = embedder or Embedder()

    async def index_document(
        self,
        file_path: str,
        client_id: UUID,
        document_type: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Index a document file.

        Args:
            file_path: Path to the document file.
            client_id: Client/tenant UUID.
            document_type: Type of document (menu, faq, etc.).
            metadata: Additional metadata.

        Returns:
            Dict with document info and vector IDs.
        """
        logger.info(
            "index_document_start",
            client_id=str(client_id),
            file_path=file_path,
            document_type=document_type,
        )

        # 1. Parse document
        text = await DocumentParser.parse(file_path)
        content_hash = DocumentParser.compute_hash(text)

        # 2. Chunk text
        chunks = self.chunker.chunk(text, metadata=metadata)

        # 3. Embed chunks
        chunk_texts = [c.text for c in chunks]
        embeddings = await self.embedder.embed_batch(chunk_texts)

        # 4. Prepare vectors for storage
        namespace = str(client_id)
        vectors = []
        vector_ids = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{client_id}_{document_type}_{uuid4().hex[:8]}_{i}"
            vector_ids.append(vector_id)

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "client_id": str(client_id),
                    "document_type": document_type,
                    "text": chunk.text,
                    "chunk_index": chunk.index,
                    **(metadata or {}),
                },
            })

        # 5. Upsert to vector store
        await VectorStore.upsert(vectors, namespace=namespace)

        logger.info(
            "index_document_complete",
            client_id=str(client_id),
            chunk_count=len(chunks),
            vector_count=len(vectors),
        )

        return {
            "content_hash": content_hash,
            "chunk_count": len(chunks),
            "vector_ids": vector_ids,
            "text_length": len(text),
        }

    async def index_text(
        self,
        text: str,
        client_id: UUID,
        document_type: str,
        document_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Index raw text content.

        Args:
            text: Text content to index.
            client_id: Client/tenant UUID.
            document_type: Type of document.
            document_id: Optional document ID prefix.
            metadata: Additional metadata.

        Returns:
            Dict with document info and vector IDs.
        """
        logger.info(
            "index_text_start",
            client_id=str(client_id),
            text_length=len(text),
        )

        content_hash = DocumentParser.compute_hash(text)
        chunks = self.chunker.chunk(text, metadata=metadata)
        chunk_texts = [c.text for c in chunks]
        embeddings = await self.embedder.embed_batch(chunk_texts)

        namespace = str(client_id)
        doc_prefix = document_id or uuid4().hex[:8]
        vectors = []
        vector_ids = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"{client_id}_{document_type}_{doc_prefix}_{i}"
            vector_ids.append(vector_id)

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "client_id": str(client_id),
                    "document_type": document_type,
                    "text": chunk.text,
                    "chunk_index": chunk.index,
                    **(metadata or {}),
                },
            })

        await VectorStore.upsert(vectors, namespace=namespace)

        logger.info(
            "index_text_complete",
            client_id=str(client_id),
            chunk_count=len(chunks),
        )

        return {
            "content_hash": content_hash,
            "chunk_count": len(chunks),
            "vector_ids": vector_ids,
        }

    async def delete_document(
        self,
        vector_ids: list[str],
        client_id: UUID,
    ) -> None:
        """Delete a document's vectors from the store.

        Args:
            vector_ids: List of vector IDs to delete.
            client_id: Client/tenant UUID.
        """
        logger.info(
            "delete_document",
            client_id=str(client_id),
            vector_count=len(vector_ids),
        )
        await VectorStore.delete(vector_ids, namespace=str(client_id))
