# Architecture Documentation

## System Overview

Wafaa AI Concierge is a multi-tenant B2B SaaS platform built as a monolith with clear service boundaries designed for future microservices extraction. The platform enables brands and restaurants to deploy AI-powered customer service chatbots across WhatsApp and Instagram, powered by Retrieval-Augmented Generation (RAG).

## Architecture Layers

### 1. Client Layer
External channels and interfaces that connect to the platform:
- **WhatsApp Business API** — via Cloud API webhooks (Phase 3)
- **Instagram Direct Messages** — via Graph API webhooks (Phase 3)
- **Admin Dashboard** — React SPA with JWT authentication (Phase 4)
- **In-App Chat** — dashboard-embedded RAG chat for testing (Phase 2)

### 2. Ingress Layer
- **Nginx**: Reverse proxy, rate limiting, SSL termination
- **Auth Service**: JWT verification (`python-jose`), tenant extraction from token claims
- **Webhook Signature Verification**: HMAC-SHA256 for WhatsApp/Instagram webhooks (no JWT — public endpoints)

### 3. Application Layer
- **Chat Orchestrator** (`api/v1/chat.py`): Session management, conversation persistence, RAG query invocation
- **Channel Manager** (`api/v1/channels.py`): CRUD for WhatsApp/Instagram channel configurations
- **Conversation Manager** (`api/v1/conversations.py`): Conversation listing, status management
- **Knowledge Base Manager** (`api/v1/knowledge.py`): Document upload, processing queue, CRUD
- **Analytics Engine** (`api/v1/analytics.py`): Overview metrics, conversation/message trends, channel performance
- **Agent Analytics** (`api/v1/agent_analytics.py`): Sentiment distribution, response time metrics, AI insights
- **Tenant Config Service** (`api/v1/tenants.py`): Bot settings, admin management
- **Message Queue**: Celery + Redis for async document processing and message handling
- **Audit Logging** (`services/audit.py`): Action logging for compliance and debugging

### 4. AI/ML Layer
- **LLM Gateway** (`services/llm_gateway.py`): Model routing with mock and OpenAI backends, prompt engineering
- **RAG Engine** (`services/rag_engine.py`): Vector search (tenant-filtered) → context injection → LLM generation
- **Embedding Service** (`services/embeddings.py`): Document and query embedding with mock and OpenAI backends
- **Document Processor** (`services/document_processor.py`): Text extraction for PDF, DOCX, TXT, CSV, JSON
- **Sentiment Analyzer** (`services/sentiment_analyzer.py`): VADER-based sentiment scoring (positive/negative/neutral)
- **Intent Classifier** (`services/intent_classifier.py`): Regex-based classification (greeting, complaint, feedback, order_inquiry, question, other)

### 5. Data Layer
- **PostgreSQL**: All relational data with row-level tenant isolation
  - `tenants` — client organizations
  - `users` — tenant admin accounts
  - `audit_logs` — action audit trail
  - `knowledge_documents` — uploaded documents with processing status
  - `knowledge_chunks` — processed text chunks with embedding references
  - `channels` — WhatsApp/Instagram configurations
  - `conversations` — customer conversation sessions
  - `messages` — individual messages with sentiment, intent, response time
- **Vector Store (Pinecone)**: Document embeddings namespaced by `tenant_id`
- **Redis**: Session cache, Celery broker, task result backend
- **File Storage**: Uploaded documents at `uploads/{tenant_id}/{doc_id}/` (tenant-isolated paths)

## Data Flow

### Chat Flow (Dashboard / API)
```
User sends message via POST /api/v1/chat
    |
    v
JWT authentication → extract tenant_id
    |
    v
Get/create conversation for this user+tenant
    |
    v
Store inbound message in PostgreSQL
    |
    v
RAG query: embed query → vector search (filtered by tenant_id) → relevant chunks
    |
    v
LLM generates response using context + system prompt
    |
    v
Store outbound message in PostgreSQL
    |
    v
Return response with source attribution
```

### Channel Webhook Flow (WhatsApp / Instagram)
```
Customer sends message via WhatsApp/Instagram
    |
    v
Webhook received at /api/v1/webhooks/{platform}
    |
    v
HMAC-SHA256 signature verification (no JWT — public endpoint)
    |
    v
Parse webhook payload → extract message, sender, channel info
    |
    v
Identify tenant from channel configuration (phone_number_id or page_id)
    |
    v
Celery task queued: process_inbound_message
    |
    v
RAG query (filtered by tenant_id) → LLM response
    |
    v
Sentiment analysis + intent classification on inbound message
    |
    v
Response sent back via platform API (WhatsApp Cloud API / Instagram Graph API)
    |
    v
Message + response stored in PostgreSQL with analytics metadata
```

### Document Processing Flow
```
Admin uploads file via POST /api/v1/knowledge
    |
    v
File validated (type, size) → saved to uploads/{tenant_id}/{doc_id}/
    |
    v
KnowledgeDocument record created (status: "uploading")
    |
    v
Celery task queued: process_document
    |
    v
Text extraction (PDF/DOCX/TXT/CSV/JSON) → chunking (400 chars, 50 overlap)
    |
    v
Embeddings generated for each chunk → upserted to vector store (namespaced by tenant_id)
    |
    v
KnowledgeChunk records created → document status updated to "ready"
```

## API Endpoints

| Prefix                      | Module              | Auth     | Description                              |
|-----------------------------|---------------------|----------|------------------------------------------|
| `/api/v1/health`            | `health.py`         | None     | Health checks (basic, database, Redis)   |
| `/api/v1/auth`              | `auth.py`           | None/JWT | Login, refresh, logout, current user     |
| `/api/v1/tenants`           | `tenants.py`        | JWT      | Tenant info, settings, admin management  |
| `/api/v1/knowledge`         | `knowledge.py`      | JWT      | Document upload, list, get, reprocess, delete |
| `/api/v1/chat`              | `chat.py`           | JWT      | RAG-powered chat with source attribution |
| `/api/v1/channels`          | `channels.py`       | JWT      | Channel CRUD (WhatsApp, Instagram)       |
| `/api/v1/conversations`     | `conversations.py`  | JWT      | Conversation listing and management      |
| `/api/v1/analytics`         | `analytics.py`      | JWT      | Overview, trends, channel performance    |
| `/api/v1/analytics/agent`   | `agent_analytics.py`| JWT      | Sentiment, response time, insights       |
| `/api/v1/webhooks/whatsapp` | `webhooks/whatsapp.py` | HMAC  | WhatsApp webhook verify + receive        |
| `/api/v1/webhooks/instagram`| `webhooks/instagram.py`| HMAC  | Instagram webhook verify + receive       |

## Multi-Tenancy Model

### Isolation Strategy: Row-Level Filtering

Every table includes a `tenant_id` column. All queries are filtered at the ORM level via the `TenantModel` base mixin.

```python
# Enforced pattern for all database queries
db.query(Model).filter(Model.tenant_id == current_user.tenant_id)
```

### Isolation Points
- **Database**: `tenant_id` column on all data tables, indexed
- **Vector Store**: Namespace partitioning by `tenant_id`
- **Cache**: Redis key prefix `tenant:{tenant_id}:`
- **File Storage**: Directory isolation `uploads/{tenant_id}/{doc_id}/`
- **API**: Tenant extracted from JWT claims, validated on every request
- **Webhooks**: Channel lookup by platform identifier → tenant resolved from channel record

## Key Architecture Decisions

### ADR-001: Row-Level Multi-Tenancy
- **Decision**: Use `tenant_id` column instead of separate schemas
- **Rationale**: Simpler to implement, scales to thousands of tenants
- **Trade-off**: Slightly more complex queries, but ORM enforces filtering

### ADR-002: Monolith-First
- **Decision**: Start as monolith, design for future extraction
- **Rationale**: Faster development, easier debugging
- **Migration Path**: Service boundaries are clear (auth, chat, RAG, analytics)

### ADR-003: Redis Streams over Kafka
- **Decision**: Use Redis Streams (via Celery) for Phase 1-4
- **Rationale**: Simpler infrastructure, sufficient for initial scale
- **Migration Path**: Switch to Kafka when handling >10K messages/minute

### ADR-004: Mock Providers for Local Development
- **Decision**: All AI/ML services (LLM, embeddings, vector store) have mock backends
- **Rationale**: Enables development and testing without API keys or external services
- **Configuration**: Switch via environment variables (`LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `VECTOR_DB_PROVIDER`)

## Security Architecture

- **Authentication**: JWT tokens (access + refresh) via `python-jose`
- **Password Hashing**: bcrypt (cost factor 12) — direct library, no passlib
- **Webhook Security**: HMAC-SHA256 signature verification for WhatsApp/Instagram
- **CORS**: Configured per environment via `CORS_ORIGINS`
- **Rate Limiting**: At Nginx level
- **Input Validation**: Pydantic schemas on all request bodies
- **Secrets Management**: Environment variables only (no secrets in code)
- **Audit Trail**: All state-changing operations logged to `audit_logs` table
- **Token Blacklist**: In-memory set (single-process); planned Redis migration for multi-worker
