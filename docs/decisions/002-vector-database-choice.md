# ADR-002: Vector Database Choice

## Status
Proposed

## Context
The RAG engine requires a vector database for storing and querying document embeddings. The database must support:
- Tenant-level namespace isolation
- Low-latency similarity search (<2s for 95% of queries)
- Scaling to millions of vectors per tenant
- Integration with Python ecosystem

## Options Considered

### Pinecone (Hosted)
- Fully managed, no infrastructure to maintain
- Native namespace support for tenant isolation
- Fast query performance at scale
- Pay-per-use pricing

### Weaviate (Self-Hosted)
- Open-source, self-hosted option
- Multi-tenancy support
- Rich filtering capabilities
- Full control over infrastructure

### Qdrant
- Open-source, Rust-based
- High performance
- Good Python client
- Payload filtering for tenant isolation

## Decision
Start with **Pinecone** for faster time-to-market. Evaluate **Weaviate** for self-hosting if vendor dependency becomes a concern.

## Rationale
- Pinecone's managed service eliminates operational overhead during early phases
- Native namespace feature maps directly to tenant isolation requirement
- Strong Python SDK with async support
- Clear migration path to Weaviate if needed

## Consequences
- Vendor dependency on Pinecone
- Monthly hosting costs (estimated $70-200/month for initial scale)
- Internet connectivity required for vector operations (no local fallback)
