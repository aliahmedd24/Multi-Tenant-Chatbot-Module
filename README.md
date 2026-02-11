# Wafaa AI Concierge

Multi-tenant B2B SaaS platform that enables brands and restaurants to deploy AI-powered customer service chatbots across social media channels (WhatsApp, Instagram, TikTok, Snapchat).

## Features

- **Multi-Tenant Architecture**: Complete data isolation between tenants via row-level `tenant_id` filtering
- **RAG-Powered Responses**: Retrieval-Augmented Generation for accurate, contextual answers from each tenant's knowledge base
- **Multi-Channel Support**: WhatsApp Business API, Instagram Direct Messaging (live); TikTok, Snapchat (Phase 6+)
- **Knowledge Base Management**: Upload PDFs, DOCX, TXT, CSV, JSON documents — automatic text extraction, chunking, and vector embedding
- **Admin Dashboard**: Real-time analytics, conversation management, channel configuration, knowledge base uploads
- **Agent Analytics**: Sentiment analysis (VADER), intent classification, response time tracking, AI-generated insights
- **Human Agent Handoff**: Seamless escalation from bot to human agents

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ (SQLite for tests)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Cache**: Redis 7
- **Task Queue**: Celery + Redis
- **Vector DB**: Pinecone (mock provider for local dev)
- **LLM**: OpenAI GPT-4o (mock provider for local dev)
- **Embeddings**: OpenAI text-embedding-3-small (mock provider for local dev)
- **NLU**: VADER sentiment analysis, regex-based intent classification

### Frontend (Dashboard)
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Build**: Vite

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana (Phase 5)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/aliahmedd24/Multi-Tenant-Chatbot-Module.git
cd Wafaa-Project

# Run the setup script
bash scripts/setup.sh

# Or manually start services
docker compose up -d
```

### Access Points
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Dashboard**: http://localhost:5173
- **Health Check**: http://localhost:8000/health

### Default Seed Credentials

| Tenant        | Email                   | Password       | Role  |
|---------------|-------------------------|----------------|-------|
| Gourmet Bites | admin@gourmetbites.com  | admin123       | owner |
| StyleHub      | admin@stylehub.com      | admin123       | owner |
| TechSupport   | admin@techsupport.com   | admin123       | owner |

### Useful Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Run backend tests
docker compose run --rm backend pytest -v

# Run backend tests with coverage
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Run migrations
docker compose run --rm backend alembic upgrade head

# Stop services
docker compose down
```

## Project Structure

```
Wafaa-Project/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/             # REST API endpoints
│   │   │   ├── auth.py         #   Authentication (login, refresh, logout)
│   │   │   ├── tenants.py      #   Tenant management
│   │   │   ├── knowledge.py    #   Knowledge base CRUD
│   │   │   ├── chat.py         #   RAG-powered chat
│   │   │   ├── channels.py     #   Channel configuration CRUD
│   │   │   ├── conversations.py#   Conversation management
│   │   │   ├── analytics.py    #   Dashboard analytics
│   │   │   ├── agent_analytics.py # Agent-specific analytics
│   │   │   ├── health.py       #   Health check endpoints
│   │   │   └── webhooks/       #   WhatsApp & Instagram webhooks
│   │   ├── core/               # Auth dependencies, security utilities
│   │   ├── models/             # SQLAlchemy models (Tenant, User, Channel, etc.)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic (RAG, LLM, embeddings, channels)
│   │   ├── workers/            # Celery tasks (message processing, document processing)
│   │   └── utils/              # File handling utilities
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend test suite (143+ tests)
│   └── scripts/                # Seed data, setup verification
├── dashboard/                  # React admin dashboard
│   └── src/
│       ├── api/                # API client with JWT interceptors
│       ├── components/         # Reusable UI components
│       ├── context/            # Auth context provider
│       ├── pages/              # Dashboard, Channels, Knowledge, Analytics, etc.
│       └── types/              # TypeScript interfaces
├── infrastructure/             # Nginx, Postgres, Prometheus configs
├── scripts/                    # Setup, migration, backup, deploy scripts
└── docs/                       # Documentation, ADRs, guides
```

## Development Phases

| Phase | Name                                      | Status     |
|-------|-------------------------------------------|------------|
| 0     | Project Setup & Architecture              | ✅ Complete |
| 1     | Foundation & Core Infrastructure          | ✅ Complete |
| 2     | Knowledge Base & RAG Engine               | ✅ Complete |
| 3     | Channel Integration (WhatsApp/Instagram)  | ✅ Complete |
| 4     | Admin Dashboard & Analytics               | ✅ Complete |
| 5     | Advanced Features & Scale                 | Pending    |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and conventions.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design documentation.

## License

Proprietary - All rights reserved.
