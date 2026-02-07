---
trigger: always_on
---

# Wafaa AI Concierge - Rules

## Architecture (6 Layers)
1. **CLIENT**: Multi-tenant (Tenant A/B/C) via Web/Mobile/Teams
2. **INGRESS**: API Gateway (rate limit, SSL, routing) + Auth (OAuth 2.0, tenant ID)
3. **APPLICATION**: Chat Orchestrator (session, context, intent) + Tenant Config + Message Queue (Kafka)
4. **AI/ML**: LLM Gateway (GPT-4/Claude/Llama) + RAG Engine (vector search) + NLU Service
5. **DATA**: Conversation DB (PostgreSQL) + Vector Store (Pinecone/Weaviate) + Knowledge Base + Cache (Redis)
6. **ISOLATION**: Row-level security, namespace partition, encryption at rest

## Tech Stack
- **Backend**: Python 3.11+, FastAPI
- **DB**: PostgreSQL 15+ (multi-tenant RLS), Pinecone/Weaviate (vectors), Redis 7+ (cache)
- **AI**: GPT-4o/Claude 3.5/Llama 3, text-embedding-ada-002
- **Channels**: Meta Business API (WhatsApp/Instagram), TikTok/Snapchat APIs

## Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/  # clients, webhooks, chat, knowledge, admin
│   ├── core/              # config, security, multi_tenant
│   ├── models/            # client, conversation, knowledge_base, channel_config
│   ├── services/
│   │   ├── orchestrator/  # chat_orchestrator, session_manager, intent_router
│   │   ├── ai/            # llm_gateway, rag_engine, prompt_manager, nlu_service
│   │   ├── channels/      # base, whatsapp, instagram, tiktok, snapchat
│   │   ├── knowledge/     # indexer, retriever, embedder
│   │   └── queue/         # producer, consumer
│   ├── schemas/           # Pydantic models
│   └── utils/             # tenant_context, validators
├── tests/
└── main.py
```

## Multi-Tenancy Rules

### Database Schema
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    slug VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    content TEXT,
    metadata JSONB,
    vector_id VARCHAR(255)
);

ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON knowledge_documents
    USING (client_id = current_setting('app.current_tenant_id')::UUID);
```

### Tenant Context
```python
from contextvars import ContextVar
current_tenant_id: ContextVar[Optional[UUID]] = ContextVar('current_tenant_id', default=None)

class TenantContext:
    @staticmethod
    def set_tenant(tenant_id: UUID): current_tenant_id.set(tenant_id)
    @staticmethod
    def get_tenant() -> Optional[UUID]: return current_tenant_id.get()
```

## RAG Implementation

### Retrieval Pipeline
```python
async def retrieve_context(query: str, client_id: UUID, top_k: int = 5):
    # 1. Generate embedding
    query_embedding = await embedder.embed(query)
    # 2. Vector search with client filter
    results = await vector_store.similarity_search(
        embedding=query_embedding,
        filter={"client_id": str(client_id)},
        namespace=str(client_id),
        top_k=top_k
    )
    return results
```

### Prompt Template
```python
PROMPT = """You are AI for {client_name}.
RULES:
1. ONLY use provided context
2. No context? Say "I don't have that info"
3. Never invent offers/prices
4. Use {tone} tone
5. Stay on topic

CONTEXT: {knowledge_context}
QUERY: {user_query}"""
```

## Channel Integration

### Webhook Pattern
```python
@router.post("/webhook/whatsapp/{client_slug}")
async def whatsapp_webhook(client_slug: str, request: Request):
    # 1. Verify signature
    if not verify_signature(request): raise HTTPException(403)
    # 2. Parse payload
    payload = await request.json()
    # 3. Get client & set context
    client = await get_client_by_slug(client_slug)
    TenantContext.set_tenant(client.id)
    # 4. Process message
    response = await orchestrator.process_message(...)
    # 5. Send response
    await send_whatsapp_message(...)
    return {"status": "ok"}
```

## Security Checklist
- ✓ All endpoints require auth
- ✓ Tenant ID from verified token, not request
- ✓ DB queries filtered by tenant_id
- ✓ File uploads validated
- ✓ Rate limiting per tenant
- ✓ Webhook signatures verified
- ✓ Secrets in env vars
- ✓ HTTPS in production
- ✓ Use ORM (prevent SQL injection)

## Coding Standards
- Type hints on all functions
- Async/await for I/O
- Pydantic for validation
- Google-style docstrings
- Black (100 char lines)
- pytest (80% coverage min)

## DO ✅
- Validate tenant_id before DB ops
- Use async/await consistently
- Implement circuit breakers
- Cache expensive operations
- Log with tenant_id
- Use dependency injection

## DON'T ❌
- Trust client-provided tenant_id
- Mix sync/async incorrectly
- Hardcode business logic in routes
- Return raw exceptions
- Skip input validation
- Use global state for tenant data

## Common Patterns

### Tenant-Safe Query
```python
async def get_documents(client_id: UUID):
    current = TenantContext.get_tenant()
    assert current == client_id, "Tenant mismatch"
    return await db.query(Doc).filter(Doc.client_id == client_id).all()
```

### RAG Generation
```python
async def generate_response(query: str, client_id: UUID):
    # 1. Retrieve context
    docs = await retrieve_context(query, client_id, top_k=5)
    # 2. Build prompt
    prompt = build_prompt(query, docs, client_id)
    # 3. Generate
    response = await llm_generate(prompt, client_id)
    return response
```

### Document Indexing
```python
async def index_document(file_path: str, client_id: UUID):
    # 1. Parse & chunk
    chunks = await chunk_text(parse_file(file_path))
    # 2. Embed
    embeddings = await embedder.embed_batch([c.text for c in chunks])
    # 3. Upsert to vector DB (with namespace)
    await vector_store.upsert(embeddings, namespace=str(client_id))
```

## Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://localhost:6379
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=xxx
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
META_APP_ID=xxx
META_APP_SECRET=xxx
JWT_SECRET_KEY=xxx
```

## Performance
- Session cache (Redis, 1hr TTL)
- Response cache (30min TTL)
- Batch vector operations
- DB connection pooling (20 size, 10 overflow)
- Async processing for non-critical ops

## Monitoring
```python
logger.info("message_processed", 
    client_id=client_id, 
    channel="whatsapp",
    response_time_ms=125)
```

Track: messages/tenant, response time, token usage, vector latency, cache hit rate, errors/tenant

---
v1.0 | 2026-02-06