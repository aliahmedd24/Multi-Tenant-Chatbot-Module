---
description: # Wafaa AI Concierge - Technical Specifications
---

## Project Overview

Wafaa AI Concierge is a multi-tenant B2B SaaS platform that enables brands and restaurants to deploy AI-powered customer service chatbots across social media channels (WhatsApp, Instagram, TikTok, Snapchat). The system uses Retrieval-Augmented Generation (RAG) to provide accurate, contextual responses based on each client's specific knowledge base while maintaining complete data isolation.

## Architecture Highlights

### Multi-Tenant Hub Design
The platform operates as a central "hub" managing multiple distinct clients, with strict data isolation ensuring each client's information remains completely separate. The architecture implements:

- **Client Layer**: Multiple social media channels (WhatsApp, Instagram, TikTok, Snapchat)
- **Ingress Layer**: API Gateway for routing and Auth Service for tenant identification
- **Application Layer**: Chat Orchestrator, Tenant Config Service, Message Queue, Observability
- **AI/ML Layer**: LLM Gateway, RAG Engine, NLU Service
- **Data Layer**: PostgreSQL (conversations), Vector Store (embeddings), Knowledge Base (documents), Cache Layer (Redis)

### Key Architectural Principles

1. **Complete Data Isolation**: Every database query filtered by tenant_id at ORM level
2. **Event-Driven Processing**: Webhook → Queue → Async Worker → Response
3. **RAG Pipeline**: User Query → Vector Search (tenant-filtered) → LLM Generation → Response
4. **Scalable Design**: Monolith with clear service boundaries for future microservices extraction

## Development Phases

### [Phase 0: Project Setup & Architecture](./phase0_project_setup_prd.md)
**Objective**: Establish development environment and project foundation

**Key Deliverables:**
- Docker Compose configuration for all services
- Git repository with branching strategy
- Automated setup scripts
- Pre-commit hooks for code quality
- Architecture documentation and ADRs
- Development workflow guidelines

**Prerequisites**: Docker, Python 3.11+, Node 20+, Git

---

### [Phase 1: Foundation & Core Infrastructure](./phase1_foundation_prd.md)
**Duration**: 2 weeks  
**Objective**: Build multi-tenant database architecture and authentication system

**Key Deliverables:**
- PostgreSQL database with tenant isolation
- SQLAlchemy models with tenant_id filtering
- JWT authentication system (access + refresh tokens)
- Tenant management APIs
- Audit logging system
- Health check endpoints

**Tech Stack**: FastAPI, PostgreSQL, SQLAlchemy, JWT, bcrypt

**Definition of Done**: 
- Three test tenants created
- Each tenant admin can authenticate
- Zero data leakage between tenants in 100 test scenarios
- All tests pass with 90%+ coverage

---

### [Phase 2: Knowledge Base & RAG Engine](./phase2_knowledge_base_prd.md)
**Objective**: Implement document upload, processing, and RAG retrieval pipeline

**Key Deliverables:**
- Document upload API (PDF, DOCX, CSV, TXT)
- Async document processing with Celery
- Text chunking and embedding generation
- Vector database integration (Pinecone/Weaviate)
- RAG query pipeline
- Tenant configuration management

**Tech Stack**: Celery, Redis, OpenAI Embeddings, Pinecone, LangChain

**Definition of Done**:
- Tenant can upload PDF menu
- Documents chunked and embedded in vector DB
- RAG query "What vegan dishes do you have?" returns accurate results
- Vector search latency <2s for 95% of queries
- Zero cross-tenant data leakage in vector search

---

### [Phase 3: Channel Integration - WhatsApp & Instagram](./phase3_channel_integration_prd.md)
**Objective**: Connect WhatsApp and Instagram to receive/send messages via chatbot

**Key Deliverables:**
- WhatsApp Business API integration
- Instagram Direct Messages integration
- OAuth flow for channel connection
- Webhook endpoints with signature validation
- Message routing and session management
- Async message processing pipeline
- Conversation and message persistence

**Tech Stack**: Meta Graph API, Twilio (optional), Redis Streams, WebSockets

**Definition of Done**:
- Tenant connects WhatsApp via OAuth
- Customer sends WhatsApp message, receives response <10s
- Response content matches RAG query results
- Multi-turn conversations maintain context
- 99% of webhooks processed successfully

---

### [Phase 4: Admin Dashboard & Analytics](./phase4_admin_dashboard_prd.md)
**Objective**: Build web interface for tenant admins to manage chatbot

**Key Deliverables:**
- React dashboard with TypeScript
- Conversation management UI
- Knowledge base upload interface
- Channel connection wizard
- Bot configuration page
- Analytics charts (messages over time, topics)
- Real-time updates via WebSocket

**Tech Stack**: React, TypeScript, Tailwind CSS, TanStack Query, Recharts, Socket.io

**Definition of Done**:
- User logs in and sees dashboard metrics
- User uploads document successfully
- User connects WhatsApp channel
- User views conversation history
- Dashboard loads <3s on 4G connection
- WCAG 2.1 Level AA accessibility compliance

---

### [Phase 5: Advanced Features & Scale](./phase5_advanced_features_prd.md)
**Objective**: Add human handoff, advanced analytics, and production-ready scalability

**Key Deliverables:**
- Human agent handoff system
- Agent dashboard with live notifications
- Sentiment analysis on messages
- Topic extraction and trending
- Scheduled email reports
- Performance optimizations (caching, connection pooling)
- Prometheus + Grafana monitoring
- Distributed tracing with OpenTelemetry
- Alerting system

**Tech Stack**: Kafka (optional), Redis caching, Prometheus, Grafana, Sentry, SendGrid

**Definition of Done**:
- Bot detects low confidence, triggers handoff
- Agent claims conversation within 10s
- Sentiment analysis runs on all inbound messages
- System handles 10,000 messages/minute
- P95 latency <2s under load
- 99.9% uptime over 30 days

---

## Implementation Roadmap

```
Phase 0: Project Setup
    ↓
Phase 1: Foundation       
    ↓
Phase 2: Knowledge Base        
    ↓
Phase 3: Channel Integration   
    ↓
Phase 4: Admin Dashboard       
    ↓
Phase 5: Advanced Features     
    ↓
Total: ~17 weeks (4 months)
```

## Cross-Phase Dependencies

### Critical Path
1. **Phase 0 → Phase 1**: Project setup must complete before any coding
2. **Phase 1 → Phase 2**: Tenant authentication required for knowledge base management
3. **Phase 2 → Phase 3**: RAG engine required for generating chatbot responses
4. **Phase 3 → Phase 4**: Conversation data required for dashboard displays
5. **Phase 4 → Phase 5**: Basic UI needed for agent handoff features

### Parallel Work Opportunities
- **Phase 2 & Phase 3**: Different teams can work simultaneously (backend RAG vs channel APIs)
- **Phase 4**: Frontend team can start UI once Phase 1 APIs are stable
- **Documentation**: Technical writing can happen throughout all phases

## Success Criteria

### Phase-Level Metrics
- **Phase 0**: New developer onboarded in <30 minutes
- **Phase 1**: Zero data leakage in 1000+ test scenarios
- **Phase 2**: 95% of documents process successfully
- **Phase 3**: 99% of webhooks processed, <10s response time
- **Phase 4**: Dashboard loads <3s, 90%+ user task completion
- **Phase 5**: 99.9% uptime, <2s P95 latency at 10k msgs/min

### Business Metrics (Post-Launch)
- **Customer Satisfaction**: 80%+ positive feedback on bot responses
- **Response Accuracy**: 85%+ of queries answered correctly from knowledge base
- **Automation Rate**: 70%+ of conversations handled without human handoff
- **Scalability**: 100 concurrent tenants, 1M messages/day
- **Reliability**: <1% message delivery failures

## Technology Stack Summary

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Queue**: Celery + Redis Streams (→ Kafka at scale)
- **Vector DB**: Pinecone or Weaviate
- **LLM**: OpenAI

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: TanStack Query
- **Real-time**: Socket.io
- **Charts**: Recharts
- **Build**: Vite

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or Loki
- **APM**: Sentry + OpenTelemetry

### External APIs
- **Messaging**: Meta Graph API (WhatsApp, Instagram)
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI API / Anthropic API
- **Email**: SendGrid or AWS SES

## Getting Started for AI Coding Assistant

### Recommended Order of Implementation

1. **Start with Phase 0**: Run setup script, verify all services start
2. **Implement Phase 1 models**: Create database schema and test data isolation
3. **Build Phase 1 APIs**: Authentication endpoints with proper JWT handling
4. **Phase 2 document processing**: Focus on PDF parsing and chunking first
5. **Phase 2 RAG pipeline**: Integrate vector search with LLM
6. **Phase 3 WhatsApp first**: More established API than Instagram
7. **Phase 4 dashboard skeleton**: Basic layout and routing before features
8. **Phase 5 incrementally**: Add one advanced feature at a time

### Code Quality Standards

- **Testing**: 90%+ coverage for critical paths (auth, RAG, message routing)
- **Type Safety**: Full type hints in Python, strict TypeScript
- **Documentation**: Docstrings for all public functions, README for each module
- **Security**: No hardcoded secrets, SQL injection prevention, CSRF protection
- **Performance**: Database queries optimized with indexes, N+1 queries eliminated
- **Error Handling**: Structured error responses, proper logging

### When to Seek Clarification

- **Ambiguous Requirements**: Ask before implementing divergent behavior
- **Security Concerns**: Verify approach for authentication, data access, encryption
- **Performance Trade-offs**: Confirm acceptable latency/resource usage
- **Third-Party APIs**: Validate API choice and usage limits
- **Architecture Changes**: Discuss before major structural modifications

## Maintenance & Future Phases

### Phase 6: Additional Channels (Planned)
- TikTok Business Messaging
- Snapchat for Business
- Twitter/X Direct Messages
- Telegram Business

### Phase 7: Advanced AI Features (Planned)
- Voice call support (Twilio)
- Image recognition (customer photos)
- Video message transcription
- Proactive messaging (scheduled campaigns)
- A/B testing for bot personalities

### Phase 8: Enterprise Features (Planned)
- SSO / SAML integration
- Advanced RBAC (roles beyond admin)
- White-label customization
- Public API for custom integrations
- Multi-language support (beyond English)

## Appendix

### Glossary
- **RAG**: Retrieval-Augmented Generation - combining vector search with LLM
- **Tenant**: A client business using the platform (e.g., a restaurant)
- **Session**: A conversation thread between a customer and tenant's bot
- **Webhook**: HTTP callback for receiving messages from social platforms
- **JWT**: JSON Web Token for stateless authentication
- **Embedding**: Vector representation of text for semantic search

### Reference Documents
- [System Architecture Diagram](./docs/architecture/system-diagram.png)
- [Data Flow Diagram](./docs/architecture/data-flow.png)
- [RAG Pipeline Diagram](./docs/architecture/rag-pipeline.png)
- [API Documentation](http://localhost:8000/docs) (after Phase 1)

### Support & Resources
- **Project Repository**: [GitHub Link - TBD]
- **Issue Tracker**: GitHub Issues
- **Documentation**: `/docs` folder in repository
- **API Spec**: OpenAPI/Swagger auto-generated

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Target Audience**: AI Coding Assistants (Claude Code), Software Developers, Technical Leads
