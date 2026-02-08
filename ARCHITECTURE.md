# Architecture Documentation

## System Overview

Wafaa AI Concierge is a multi-tenant B2B SaaS platform built as a monolith with clear service boundaries designed for future microservices extraction.

## Architecture Layers

### 1. Client Layer
External channels that connect to the platform:
- WhatsApp Business API
- Instagram Direct Messages
- Admin Dashboard (React SPA)

### 2. Ingress Layer
- **Nginx**: Reverse proxy, rate limiting, SSL termination
- **Auth Service**: JWT verification, tenant identification

### 3. Application Layer
- **Chat Orchestrator**: Session management, intent routing, context handling
- **Tenant Config Service**: Bot settings, custom prompts, rate limits
- **Message Queue**: Redis Streams for async processing
- **Observability**: Logging, metrics, tracing

### 4. AI/ML Layer
- **LLM Gateway**: Model routing, prompt engineering, token management
- **RAG Engine**: Vector search (tenant-filtered), context injection
- **NLU Service**: Intent classification, entity extraction, sentiment analysis

### 5. Data Layer
- **PostgreSQL**: Conversations, users, tenants, configuration
- **Vector Store (Pinecone)**: Document embeddings (namespaced by tenant)
- **Redis**: Session cache, response cache, rate limiting
- **File Storage**: Uploaded documents (tenant-isolated paths)

## Data Flow

```
Customer sends message via WhatsApp/Instagram
    |
    v
Webhook received at API Gateway
    |
    v
Auth Service identifies tenant from webhook signature
    |
    v
Message queued in Redis Stream
    |
    v
Celery Worker picks up message
    |
    v
Retrieve conversation context from PostgreSQL
    |
    v
RAG query: vector search (filtered by tenant_id) -> relevant chunks
    |
    v
LLM generates response using context + chunks + system prompt
    |
    v
Response sent back via channel API
    |
    v
Message + response stored in PostgreSQL
    |
    v
Analytics metrics updated
```

## Multi-Tenancy Model

### Isolation Strategy: Row-Level Filtering

Every table includes a `tenant_id` column. All queries are filtered at the ORM level.

```python
# Enforced pattern for all database queries
db.query(Model).filter(Model.tenant_id == current_user.tenant_id)
```

### Isolation Points
- **Database**: `tenant_id` column on all data tables, indexed
- **Vector Store**: Namespace partitioning by `tenant_id`
- **Cache**: Redis key prefix `tenant:{tenant_id}:`
- **File Storage**: Directory isolation `/data/uploads/{tenant_id}/`
- **API**: Tenant extracted from JWT, validated on every request

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
- **Decision**: Use Redis Streams for Phase 1-4
- **Rationale**: Simpler infrastructure, sufficient for initial scale
- **Migration Path**: Switch to Kafka when handling >10K messages/minute

## Security Architecture

- JWT tokens (access + refresh) for authentication
- bcrypt for password hashing
- CORS configured per environment
- Rate limiting at Nginx level
- Input validation via Pydantic schemas
- No secrets in code (environment variables only)
- Webhook signature verification for channel integrations
