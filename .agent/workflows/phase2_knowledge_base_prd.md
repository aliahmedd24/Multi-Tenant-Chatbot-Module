---
description: # Phase 2: Knowledge Base & RAG Engine | ## Objective Implement the knowledge base management system allowing tenants to upload and manage their business data (menus, FAQs, policies), and build the RAG (Retrieval-Augmented Generation) pipeline for in
---

## Tech Stack
- **Vector Database**: Pinecone (hosted) or Weaviate (self-hosted option)
- **Embedding Model**: OpenAI text-embedding-3-small or sentence-transformers/all-MiniLM-L6-v2
- **LLM Provider**: OpenAI GPT-4o (primary)
- **Document Processing**: PyPDF2, python-docx, pandas (for CSV)
- **Text Chunking**: LangChain TextSplitter or custom chunker
- **File Storage**: Local filesystem (Phase 2), S3-compatible planned for Phase 3
- **Vector Search**: langchain or llamaindex for RAG orchestration
- **Background Jobs**: Celery with Redis (for async document processing)
- **API Framework**: FastAPI (continued from Phase 1)

## User Flow
1. Tenant admin logs in and navigates to Knowledge Base section
2. Admin uploads documents (PDF menu, CSV with hours, FAQ document)
3. System processes documents asynchronously, showing progress indicator
4. Documents are chunked, embedded, and stored in vector database with tenant_id namespace
5. Admin can view list of uploaded documents with status (processing, ready, failed)
6. Admin can preview document content and delete documents
7. Admin configures custom instructions (tone, policies, constraints)
8. System validates knowledge base has minimum required information
9. When complete, tenant's bot status changes to "Ready to Deploy"

## Technical Constraints
- **Data Isolation**: Vector database must namespace embeddings by tenant_id
- **File Size Limits**: Max 10MB per file, max 20 files per tenant (configurable)
- **Supported Formats**: PDF, DOCX, TXT, CSV only (validated on upload)
- **Chunk Size**: Max 512 tokens per chunk (to fit in embedding model context)
- **Processing Time**: Document processing must complete within 5 minutes
- **RAG Performance**: Retrieval latency must be < 2 seconds for 95th percentile
- **Embedding Costs**: Must track and log token usage per tenant
- **No External Storage**: Files stored locally in /data/uploads/{tenant_id}/ for Phase 2

## Data Schema

### Knowledge Documents Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "filename": "String (255) - Original filename",
    "file_type": "Enum (pdf, docx, txt, csv, json)",
    "file_path": "String (512) - Local storage path",
    "file_size_bytes": "Integer",
    "status": "Enum (uploading, processing, ready, failed)",
    "processing_error": "Text - Nullable, error details",
    "uploaded_by": "UUID (Foreign Key to Tenant Admins)",
    "uploaded_at": "Timestamp",
    "processed_at": "Timestamp - Nullable",
    "chunk_count": "Integer - Number of chunks generated",
    "metadata": "JSONB - File-specific metadata"
}
```

### Knowledge Chunks Table
```python
{
    "id": "UUID (Primary Key)",
    "document_id": "UUID (Foreign Key to Knowledge Documents)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "chunk_index": "Integer - Position in document",
    "content": "Text - The actual text chunk",
    "embedding_id": "String (255) - Vector DB reference ID",
    "token_count": "Integer",
    "metadata": "JSONB - Chunk context (page, section, etc.)",
    "created_at": "Timestamp"
}
```

### Tenant Configuration Table (Extension)
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants) - Unique",
    "business_name": "String (255)",
    "business_hours": "JSONB - {day: {open, close}}",
    "address": "Text",
    "phone": "String (50)",
    "email": "String (255)",
    "website": "String (255) - Nullable",
    "custom_instructions": "Text - AI behavior guidelines",
    "tone": "Enum (formal, casual, friendly, professional)",
    "response_language": "String (10) - ISO language code",
    "allowed_topics": "JSONB - List of acceptable query types",
    "blocked_topics": "JSONB - List of topics to refuse",
    "created_at": "Timestamp",
    "updated_at": "Timestamp"
}
```

### Embedding Usage Log Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "operation": "Enum (embed_document, embed_query)",
    "model": "String (100) - Embedding model name",
    "token_count": "Integer",
    "cost_usd": "Decimal(10,6) - Nullable",
    "created_at": "Timestamp"
}
```

## API Endpoints

### Knowledge Base Management
- `GET /api/v1/knowledge/documents` - List tenant's documents
- `POST /api/v1/knowledge/documents` - Upload new document
- `GET /api/v1/knowledge/documents/{doc_id}` - Get document details
- `DELETE /api/v1/knowledge/documents/{doc_id}` - Delete document
- `GET /api/v1/knowledge/documents/{doc_id}/chunks` - Preview chunks
- `POST /api/v1/knowledge/documents/{doc_id}/reprocess` - Reprocess failed document

### Tenant Configuration
- `GET /api/v1/config` - Get tenant configuration
- `PUT /api/v1/config` - Update tenant configuration
- `POST /api/v1/config/validate` - Validate configuration completeness

### RAG Query (Internal/Testing)
- `POST /api/v1/rag/query` - Test RAG retrieval (auth required)
- `POST /api/v1/rag/generate` - Full RAG + LLM generation (testing only)

### Background Jobs
- `GET /api/v1/jobs/{job_id}` - Check processing job status

## Directory Structure Updates
```
wafaa-backend/
├── app/
│   ├── models/
│   │   ├── knowledge.py (new)
│   │   └── config.py (new)
│   ├── schemas/
│   │   ├── knowledge.py (new)
│   │   └── config.py (new)
│   ├── api/v1/
│   │   ├── knowledge.py (new)
│   │   ├── config.py (new)
│   │   └── rag.py (new)
│   ├── services/
│   │   ├── __init__.py (new)
│   │   ├── document_processor.py (new)
│   │   ├── embeddings.py (new)
│   │   ├── vector_store.py (new)
│   │   └── rag_engine.py (new)
│   ├── workers/
│   │   ├── __init__.py (new)
│   │   └── celery_tasks.py (new)
│   └── utils/
│       ├── file_handler.py (new)
│       └── text_chunker.py (new)
├── data/
│   └── uploads/ (new, gitignored)
├── celery_config.py (new)
└── docker-compose.yml (new - for Redis)
```

## Document Processing Pipeline

### Step 1: File Upload
```python
# Request: POST /api/v1/knowledge/documents
# Headers: Authorization: Bearer {jwt_token}
# Body: multipart/form-data
{
    "file": "<binary file data>",
    "metadata": {
        "category": "menu",  # or "faq", "policy", "hours"
        "description": "Spring 2026 Menu"
    }
}

# Response: 202 Accepted
{
    "document_id": "uuid",
    "job_id": "uuid",
    "status": "processing",
    "message": "Document queued for processing"
}
```

### Step 2: Async Processing (Celery Task)
1. Validate file type and size
2. Save file to `/data/uploads/{tenant_id}/{document_id}.{ext}`
3. Extract text based on file type:
   - PDF: PyPDF2 → raw text
   - DOCX: python-docx → raw text
   - CSV: pandas → structured data → formatted text
   - TXT: direct read
4. Clean and normalize text (remove excess whitespace, special chars)
5. Chunk text using semantic chunking (aim for ~400 tokens, max 512)
6. Generate embeddings for each chunk via OpenAI API
7. Store embeddings in vector database with metadata:
   ```python
   {
       "id": "chunk_uuid",
       "values": [0.123, -0.456, ...],  # embedding vector
       "metadata": {
           "tenant_id": "uuid",
           "document_id": "uuid",
           "chunk_index": 0,
           "content": "chunk text",
           "category": "menu",
           "page": 1  # if applicable
       }
   }
   ```
8. Update database: `status="ready"`, `chunk_count=N`, `processed_at=now()`

### Step 3: RAG Query Pipeline
```python
# Input: User query + tenant_id
query = "What are your vegan options?"
tenant_id = "uuid-from-jwt"

# 1. Embed query
query_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input=query
)

# 2. Vector search with tenant filter
results = vector_db.query(
    vector=query_embedding,
    filter={"tenant_id": tenant_id},
    top_k=5
)

# 3. Extract context chunks
context = "\n\n".join([r.metadata["content"] for r in results])

# 4. Retrieve tenant configuration
config = db.query(TenantConfig).filter(tenant_id=tenant_id).first()

# 5. Build prompt
system_prompt = f"""
You are a customer service assistant for {config.business_name}.
Tone: {config.tone}
Instructions: {config.custom_instructions}

Use the following information to answer the customer's question:
{context}

Important constraints:
- Only answer based on the provided information
- If information is not available, say so politely
- Never make up information
- Do not answer questions about: {config.blocked_topics}
"""

# 6. Call LLM
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
)

return response.choices[0].message.content
```

## Environment Variables (Additional)
```
# Vector Database
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=wafaa-knowledge

# OR for Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=optional-key

# Embedding Provider
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small

# LLM Provider
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4o
ANTHROPIC_API_KEY=your-anthropic-key

# File Storage
UPLOAD_DIR=/data/uploads
MAX_FILE_SIZE_MB=10
MAX_FILES_PER_TENANT=20

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# RAG Settings
CHUNK_SIZE=400
CHUNK_OVERLAP=50
MAX_CONTEXT_CHUNKS=5
```

## Definition of Done

### Code Requirements
- [ ] Document upload API accepts PDF, DOCX, TXT, CSV files
- [ ] File validation rejects oversized or unsupported formats
- [ ] Celery worker processes documents asynchronously
- [ ] Text chunking creates semantically coherent chunks (400-512 tokens)
- [ ] Embeddings generated and stored in vector database
- [ ] Vector search filters by tenant_id to ensure data isolation
- [ ] RAG pipeline retrieves top-K relevant chunks per query
- [ ] LLM prompt includes system instructions and tenant config
- [ ] Tenant configuration CRUD operations implemented
- [ ] Error handling for embedding API failures (retry logic)

### Testing Requirements
- [ ] Unit tests for document parsers (PDF, DOCX, CSV extraction)
- [ ] Unit tests for text chunking (validates chunk size constraints)
- [ ] Integration test: upload document → verify chunks in database
- [ ] Integration test: RAG query returns relevant results for sample menu
- [ ] Test data isolation: Tenant A query cannot retrieve Tenant B chunks
- [ ] Test embedding API failure triggers retry (3 attempts)
- [ ] Test document deletion removes all chunks and embeddings
- [ ] Load test: 10 concurrent document uploads process successfully
- [ ] Test vector search performance: <2s retrieval time for 95% of queries

### Functional Requirements
- [ ] Tenant can upload a 3-page PDF menu
- [ ] System chunks menu into 10-15 chunks (visible in DB)
- [ ] Vector database shows embeddings with tenant_id metadata
- [ ] RAG test query "What vegan dishes do you have?" returns menu items
- [ ] RAG test query with no relevant data returns "I don't have that info"
- [ ] Tenant can update custom instructions (e.g., "Be formal")
- [ ] Updated instructions reflected in next LLM response
- [ ] Tenant can delete document; chunks and embeddings removed
- [ ] Processing job status endpoint shows progress (processing → ready)
- [ ] Failed document processing logs error in database

### Performance Requirements
- [ ] Document processing completes within 5 minutes for 10MB file
- [ ] Embedding generation: <10s per chunk
- [ ] Vector search: <500ms for 90% of queries
- [ ] RAG pipeline end-to-end: <3s for query to response
- [ ] System handles 100 simultaneous RAG queries without degradation

### Security Requirements
- [ ] Uploaded files stored in tenant-specific directories
- [ ] File paths include random UUID to prevent enumeration
- [ ] Vector database credentials stored as environment variables
- [ ] Embedding API keys not exposed in logs or responses
- [ ] Tenant cannot access other tenant's vector embeddings
- [ ] Document deletion audit logged with user_id

### Documentation Requirements
- [ ] README updated with vector database setup instructions
- [ ] API documentation includes file upload examples
- [ ] Document processing pipeline flowchart added to docs
- [ ] RAG query examples with sample responses documented
- [ ] Celery worker setup instructions provided
- [ ] Troubleshooting guide for common processing errors

## Success Metrics
- 95% of uploaded documents process successfully on first attempt
- Vector search retrieval accuracy: 80%+ relevance for test queries
- Zero cross-tenant data leakage in 1000 test scenarios
- LLM response uses context from knowledge base in 90%+ of queries
- Processing queue clears within 10 minutes under normal load

## Next Phase Dependencies
Phase 3 (Channel Integration) requires:
- RAG engine from this phase for generating responses
- Tenant configuration for customizing bot behavior per channel
- Knowledge base validation to ensure tenant has minimum required data
