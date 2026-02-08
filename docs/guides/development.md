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
# All backend tests
docker compose run --rm backend pytest -v

# With coverage report
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Specific test file
docker compose run --rm backend pytest tests/test_health.py -v
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

## Project Architecture

See [ARCHITECTURE.md](../../ARCHITECTURE.md) for detailed system design.

## Adding New Features

1. Check the relevant Phase PRD in `.agent/workflows/`
2. Create a feature branch: `git checkout -b feature/phase{N}-{name}`
3. Implement the feature following code standards
4. Write tests meeting coverage requirements
5. Verify tenant isolation
6. Submit for review
