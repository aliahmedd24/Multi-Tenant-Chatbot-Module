# Setup Guide

## Prerequisites

- **Docker**: Version 20+ with Docker Compose v2
- **Git**: For version control
- **Python 3.11+**: For local development without Docker (optional)
- **Node.js 18+**: For dashboard development (optional)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/aliahmedd24/Multi-Tenant-Chatbot-Module.git
cd Wafaa-Project
```

### 2. Run Setup Script
```bash
bash scripts/setup.sh
```

This will:
- Check prerequisites
- Create `.env` files from templates
- Start PostgreSQL and Redis
- Run database migrations
- Seed initial data (3 tenants, 3 admin users)
- Start all services

### 3. Verify Services
```bash
docker compose ps
```

All services should show as "running":
- `wafaa-postgres` — PostgreSQL database
- `wafaa-redis` — Redis cache
- `wafaa-backend` — FastAPI API server
- `wafaa-celery` — Celery task worker
- `wafaa-dashboard` — React dashboard

### 4. Access the Application
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Dashboard**: http://localhost:5173
- **Health Check**: http://localhost:8000/health

## Environment Variables

### Backend (`backend/.env`)
Copy from `backend/.env.example` and update:

#### Core Settings
| Variable                   | Description                          | Default                                    |
|----------------------------|--------------------------------------|--------------------------------------------|
| `SECRET_KEY`               | JWT signing key                      | `dev-secret-key-change-in-production`      |
| `DATABASE_URL`             | PostgreSQL connection string         | `postgresql://wafaa_user:dev_password@...`  |
| `REDIS_URL`                | Redis connection string              | `redis://localhost:6379/0`                 |
| `DEBUG`                    | Enable debug mode                    | `false`                                    |
| `CORS_ORIGINS`             | Allowed CORS origins (comma-sep)     | `http://localhost:5173`                    |

#### AI/ML Providers
| Variable                   | Description                          | Default     |
|----------------------------|--------------------------------------|-------------|
| `LLM_PROVIDER`             | LLM backend (`mock` or `openai`)     | `mock`      |
| `LLM_MODEL`                | OpenAI model name                    | `gpt-4o`    |
| `EMBEDDING_PROVIDER`       | Embedding backend (`mock` or `openai`)| `mock`     |
| `EMBEDDING_MODEL`          | OpenAI embedding model               | `text-embedding-3-small` |
| `VECTOR_DB_PROVIDER`       | Vector DB backend (`mock` or `pinecone`)| `mock`   |
| `OPENAI_API_KEY`           | OpenAI API key (required if not mock)| *(empty)*   |
| `PINECONE_API_KEY`         | Pinecone API key (required if not mock)| *(empty)* |
| `PINECONE_INDEX_NAME`      | Pinecone index name                  | `wafaa-knowledge` |

#### Channel Webhooks
| Variable                   | Description                          | Default                |
|----------------------------|--------------------------------------|------------------------|
| `WEBHOOK_VERIFY_TOKEN`     | Meta webhook verification token      | `wafaa-verify-token`   |
| `WHATSAPP_API_VERSION`     | WhatsApp Cloud API version           | `v18.0`                |
| `INSTAGRAM_API_VERSION`    | Instagram Graph API version          | `v18.0`                |

> **Note**: For local development, all AI/ML providers default to `mock` mode. No API keys are required. Set providers to `openai`/`pinecone` and supply API keys when you want to use real services.

### Dashboard (`dashboard/.env`)
Copy from `dashboard/.env.example`. Defaults work for local development.

## Troubleshooting

### Port Conflicts
If ports are already in use, modify `docker-compose.yml`:
- Backend: Change `8000:8000`
- Dashboard: Change `5173:5173`
- PostgreSQL: Change `5432:5432`
- Redis: Change `6379:6379`

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# Reset database completely
docker compose down -v  # WARNING: Deletes all data
docker compose up -d
```

### Container Build Failures
```bash
# Rebuild without cache
docker compose build --no-cache

# Check specific service logs
docker compose logs -f backend
```

### Mock vs Real Providers
If you see errors about API keys or vector dimensions:
1. Ensure `LLM_PROVIDER=mock` in `backend/.env` for local development
2. If using Pinecone, you **must** also use real embeddings (`EMBEDDING_PROVIDER=openai`) since mock embeddings (384 dim) don't match Pinecone's expected dimensions (1536)
