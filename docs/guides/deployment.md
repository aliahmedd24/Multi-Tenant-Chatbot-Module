# Deployment Guide

## Production Deployment

> This guide will be expanded as the project progresses through development phases.

### Using Docker Compose (Production)

```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Environment Variables

For production, ensure all variables in `backend/.env.example` are set with production values:
- `SECRET_KEY`: Strong random key (min 32 characters)
- `DEBUG`: Set to `false`
- `DATABASE_URL`: Production database connection string
- `CORS_ORIGINS`: Production domain(s) only

### Security Checklist for Production
- [ ] All secrets stored in environment variables
- [ ] DEBUG mode disabled
- [ ] CORS restricted to production domains
- [ ] Database not exposed on public ports
- [ ] SSL/TLS configured on Nginx
- [ ] Rate limiting enabled
- [ ] Logging configured (no sensitive data in logs)
