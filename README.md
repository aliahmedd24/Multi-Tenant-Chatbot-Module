# Wafaa AI Concierge

Multi-tenant B2B SaaS platform that enables brands and restaurants to deploy AI-powered customer service chatbots across social media channels (WhatsApp, Instagram, TikTok, Snapchat).

## Features

- **Multi-Tenant Architecture**: Complete data isolation between tenants
- **RAG-Powered Responses**: Retrieval-Augmented Generation for accurate, contextual answers
- **Multi-Channel Support**: WhatsApp, Instagram (Phase 3), TikTok, Snapchat (Phase 6+)
- **Knowledge Base Management**: Upload PDFs, documents, and menus for AI training
- **Admin Dashboard**: Real-time analytics, conversation management, bot configuration
- **Human Agent Handoff**: Seamless escalation from bot to human agents

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Task Queue**: Celery + Redis
- **Vector DB**: Pinecone / Weaviate

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State**: TanStack Query
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
git clone <repository-url>
cd wafaa-platform

# Run the setup script
bash scripts/setup.sh

# Or manually start services
docker compose up -d
```

### Access Points
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Dashboard**: http://localhost:5173

### Useful Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Run backend tests
docker compose run --rm backend pytest -v

# Run migrations
docker compose run --rm backend alembic upgrade head

# Stop services
docker compose down
```

## Project Structure

```
wafaa-platform/
├── backend/          # FastAPI backend application
│   ├── app/          # Application code
│   ├── alembic/      # Database migrations
│   ├── tests/        # Backend tests
│   └── scripts/      # Seed data, setup verification
├── dashboard/        # React admin dashboard
│   └── src/          # Frontend source code
├── infrastructure/   # Nginx, Postgres, Prometheus configs
├── scripts/          # Setup, migration, backup scripts
└── docs/             # Documentation, ADRs, guides
```

## Development Phases

| Phase | Name | Status |
|-------|------|--------|
| 0 | Project Setup & Architecture | Complete |
| 1 | Foundation & Core Infrastructure | Pending |
| 2 | Knowledge Base & RAG Engine | Pending |
| 3 | Channel Integration (WhatsApp/Instagram) | Pending |
| 4 | Admin Dashboard & Analytics | Pending |
| 5 | Advanced Features & Scale | Pending |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and conventions.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design documentation.

## License

Proprietary - All rights reserved.
