"""Vector store abstraction.

Provides unified interface for Pinecone and Weaviate vector databases.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

import structlog

from app.core.config import settings


logger = structlog.get_logger()


class VectorStoreBase(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    async def upsert(
        self,
        vectors: list[dict],
        namespace: str,
    ) -> None:
        """Insert or update vectors."""
        pass

    @abstractmethod
    async def query(
        self,
        vector: list[float],
        namespace: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> dict:
        """Query similar vectors."""
        pass

    @abstractmethod
    async def delete(
        self,
        ids: list[str],
        namespace: str,
    ) -> None:
        """Delete vectors by ID."""
        pass

    @abstractmethod
    async def create_namespace(self, namespace: str) -> None:
        """Create a new namespace/collection."""
        pass


class PineconeStore(VectorStoreBase):
    """Pinecone vector store implementation."""

    def __init__(self):
        """Initialize Pinecone client."""
        from pinecone import Pinecone

        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._pc.Index(settings.pinecone_index_name)

    async def upsert(
        self,
        vectors: list[dict],
        namespace: str,
    ) -> None:
        """Insert or update vectors in Pinecone.

        Args:
            vectors: List of dicts with 'id', 'values', 'metadata'.
            namespace: Namespace for tenant isolation.
        """
        logger.info("pinecone_upsert", count=len(vectors), namespace=namespace)
        self._index.upsert(vectors=vectors, namespace=namespace)

    async def query(
        self,
        vector: list[float],
        namespace: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> dict:
        """Query similar vectors from Pinecone.

        Args:
            vector: Query vector.
            namespace: Namespace to search in.
            top_k: Number of results.
            filter: Metadata filter.

        Returns:
            Query results with matches.
        """
        logger.info("pinecone_query", namespace=namespace, top_k=top_k)
        results = self._index.query(
            vector=vector,
            namespace=namespace,
            top_k=top_k,
            filter=filter,
            include_metadata=True,
        )
        return results.to_dict()

    async def delete(
        self,
        ids: list[str],
        namespace: str,
    ) -> None:
        """Delete vectors from Pinecone."""
        logger.info("pinecone_delete", count=len(ids), namespace=namespace)
        self._index.delete(ids=ids, namespace=namespace)

    async def create_namespace(self, namespace: str) -> None:
        """Namespaces are created automatically in Pinecone."""
        logger.info("pinecone_namespace_created", namespace=namespace)


class WeaviateStore(VectorStoreBase):
    """Weaviate vector store implementation."""

    def __init__(self):
        """Initialize Weaviate client."""
        import weaviate

        self._client = weaviate.connect_to_local(
            host=settings.weaviate_url.replace("http://", "").split(":")[0],
            port=int(settings.weaviate_url.split(":")[-1]),
        )

    async def upsert(
        self,
        vectors: list[dict],
        namespace: str,
    ) -> None:
        """Insert or update vectors in Weaviate."""
        logger.info("weaviate_upsert", count=len(vectors), namespace=namespace)
        collection = self._client.collections.get(namespace)

        with collection.batch.dynamic() as batch:
            for v in vectors:
                batch.add_object(
                    properties=v.get("metadata", {}),
                    vector=v["values"],
                    uuid=v["id"],
                )

    async def query(
        self,
        vector: list[float],
        namespace: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> dict:
        """Query similar vectors from Weaviate."""
        logger.info("weaviate_query", namespace=namespace, top_k=top_k)
        collection = self._client.collections.get(namespace)

        results = collection.query.near_vector(
            near_vector=vector,
            limit=top_k,
            return_metadata=["distance"],
        )

        matches = [
            {
                "id": str(obj.uuid),
                "score": 1 - (obj.metadata.distance or 0),
                "metadata": obj.properties,
            }
            for obj in results.objects
        ]

        return {"matches": matches}

    async def delete(
        self,
        ids: list[str],
        namespace: str,
    ) -> None:
        """Delete vectors from Weaviate."""
        logger.info("weaviate_delete", count=len(ids), namespace=namespace)
        collection = self._client.collections.get(namespace)
        for id_ in ids:
            collection.data.delete_by_id(id_)

    async def create_namespace(self, namespace: str) -> None:
        """Create a new collection in Weaviate."""
        logger.info("weaviate_create_collection", namespace=namespace)
        try:
            self._client.collections.create(name=namespace)
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise


class VectorStore:
    """Factory for vector store implementations.

    Automatically selects the appropriate backend based on settings.
    """

    _instance: Optional[VectorStoreBase] = None

    @classmethod
    def get_store(cls) -> VectorStoreBase:
        """Get or create vector store instance."""
        if cls._instance is None:
            if settings.vector_db_provider == "pinecone":
                cls._instance = PineconeStore()
            elif settings.vector_db_provider == "weaviate":
                cls._instance = WeaviateStore()
            else:
                raise ValueError(f"Unknown provider: {settings.vector_db_provider}")
        return cls._instance

    @classmethod
    async def upsert(cls, vectors: list[dict], namespace: str) -> None:
        """Insert or update vectors."""
        store = cls.get_store()
        await store.upsert(vectors, namespace)

    @classmethod
    async def query(
        cls,
        vector: list[float],
        namespace: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> dict:
        """Query similar vectors."""
        store = cls.get_store()
        return await store.query(vector, namespace, top_k, filter)

    @classmethod
    async def delete(cls, ids: list[str], namespace: str) -> None:
        """Delete vectors."""
        store = cls.get_store()
        await store.delete(ids, namespace)

    @classmethod
    async def create_namespace(cls, namespace: str) -> None:
        """Create namespace."""
        store = cls.get_store()
        await store.create_namespace(namespace)
