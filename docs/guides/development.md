# Development Guide

## Daily Workflow

### Starting Your Day
```bash
# Pull latest changes
git pull origin develop

# Start services
docker compose up -d

# Check service health
curl http://localhost:8000/health
```

### During Development

The backend and dashboard both support **hot-reloading**:
- Backend: Save a `.py` file and uvicorn restarts automatically
- Dashboard: Save a `.tsx` file and Vite refreshes the browser

### Running Tests
```bash
# All backend tests (143+ tests)
docker compose run --rm backend pytest -v

# With coverage report
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Specific test file
docker compose run --rm backend pytest tests/test_auth.py -v
docker compose run --rm backend pytest tests/test_rag_engine.py -v
docker compose run --rm backend pytest tests/test_channels_api.py -v
docker compose run --rm backend pytest tests/test_agent_analytics_api.py -v

# Run only fast unit tests (skip integration)
docker compose run --rm backend pytest -v -k "not integration"
```

### Database Migrations

```bash
# Create a new migration
bash scripts/migrate.sh "description of changes"

# Apply pending migrations
docker compose run --rm backend alembic upgrade head

# Check current migration
docker compose run --rm backend alembic current

# Rollback one migration
docker compose run --rm backend alembic downgrade -1
```

### Code Quality

```bash
# Python linting
docker compose run --rm backend ruff check app/

# Python formatting
docker compose run --rm backend ruff format app/

# Security scan
docker compose run --rm backend bandit -r app/
```

## API Endpoint Reference

All endpoints are prefixed with `/api/v1/`. Full interactive docs at http://localhost:8000/docs.

| Prefix              | Module              | Auth     | Description                              |
|---------------------|---------------------|----------|------------------------------------------|
| `/health`           | `health.py`         | None     | Health checks (basic, database, Redis)   |
| `/auth`             | `auth.py`           | None/JWT | Login, refresh, logout, current user     |
| `/tenants`          | `tenants.py`        | JWT      | Tenant info, settings, admin CRUD        |
| `/knowledge`        | `knowledge.py`      | JWT      | Document upload, list, get, reprocess, delete |
| `/chat`             | `chat.py`           | JWT      | RAG-powered chat with source attribution |
| `/channels`         | `channels.py`       | JWT      | Channel CRUD (WhatsApp, Instagram)       |
| `/conversations`    | `conversations.py`  | JWT      | Conversation listing and management      |
| `/analytics`        | `analytics.py`      | JWT      | Overview, trends, channel performance    |
| `/analytics/agent`  | `agent_analytics.py`| JWT      | Sentiment, response time, insights       |
| `/webhooks/whatsapp`| `webhooks/whatsapp.py` | HMAC  | WhatsApp webhook verify + receive        |
| `/webhooks/instagram`| `webhooks/instagram.py`| HMAC | Instagram webhook verify + receive       |

## Switching AI/ML Providers

By default, all AI/ML services use **mock** backends (no API keys needed).

To switch to real providers, update `backend/.env`:

```bash
# Use real OpenAI for LLM and embeddings
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai

# Use Pinecone for vector storage (requires real embeddings)
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=wafaa-knowledge
```

> **Important**: If using Pinecone, you **must** also set `EMBEDDING_PROVIDER=openai`. Mock embeddings (384 dim) are incompatible with Pinecone indexes (1536 dim).

## Project Architecture

See [ARCHITECTURE.md](../../ARCHITECTURE.md) for detailed system design.

## Adding New Features

1. Check the relevant Phase PRD in `.agent/workflows/`
2. Create a feature branch: `git checkout -b feature/phase{N}-{name}`
3. Implement the feature following code standards
4. Write tests meeting coverage requirements
5. Verify tenant isolation (`tenant_id` filtering on all queries)
6. Update `LOG.md` with session details
7. Submit for review
