# Setup Guide

## Prerequisites

- **Docker**: Version 20+ with Docker Compose v2
- **Git**: For version control

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd wafaa-platform
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
- Seed initial data
- Start all services

### 3. Verify Services
```bash
docker compose ps
```

All services should show as "running":
- `wafaa-postgres` - PostgreSQL database
- `wafaa-redis` - Redis cache
- `wafaa-backend` - FastAPI API server
- `wafaa-celery` - Celery task worker
- `wafaa-dashboard` - React dashboard

### 4. Access the Application
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:5173
- **Health Check**: http://localhost:8000/health

## Environment Variables

### Backend (`backend/.env`)
Copy from `backend/.env.example` and update:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `DATABASE_URL`: Default works with Docker Compose
- `REDIS_URL`: Default works with Docker Compose

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
