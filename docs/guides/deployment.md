# Deployment Guide

## Production Deployment

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

#### Core Settings
| Variable         | Requirement                                      |
|------------------|--------------------------------------------------|
| `SECRET_KEY`     | Strong random key: `openssl rand -hex 32`        |
| `DEBUG`          | Must be `false`                                  |
| `DATABASE_URL`   | Production PostgreSQL connection string           |
| `REDIS_URL`      | Production Redis connection string                |
| `CORS_ORIGINS`   | Production domain(s) only (comma-separated)       |

#### AI/ML Providers
| Variable              | Requirement                                    |
|-----------------------|------------------------------------------------|
| `LLM_PROVIDER`        | `openai` (or other supported provider)        |
| `OPENAI_API_KEY`       | Valid OpenAI API key                          |
| `EMBEDDING_PROVIDER`   | `openai`                                      |
| `VECTOR_DB_PROVIDER`   | `pinecone`                                    |
| `PINECONE_API_KEY`     | Valid Pinecone API key                        |
| `PINECONE_INDEX_NAME`  | Production index name                         |

#### Channel Webhooks (WhatsApp / Instagram)
| Variable                | Requirement                                   |
|-------------------------|-----------------------------------------------|
| `WEBHOOK_VERIFY_TOKEN`  | Strong random token shared with Meta App      |
| `WHATSAPP_API_VERSION`  | Current Graph API version (e.g., `v18.0`)     |
| `INSTAGRAM_API_VERSION` | Current Graph API version (e.g., `v18.0`)     |

Channel-specific credentials (access tokens, webhook secrets) are stored per-channel in the database via the `/api/v1/channels` endpoints, not in environment variables.

#### Monitoring (Optional)
| Variable              | Requirement                                    |
|-----------------------|------------------------------------------------|
| `SENTRY_DSN`          | Sentry project DSN for error tracking          |
| `PROMETHEUS_ENABLED`  | `true` to enable Prometheus metrics endpoint   |

### Meta App Setup (WhatsApp / Instagram)

1. Create a Meta Developer App at https://developers.facebook.com
2. Add the **WhatsApp** and/or **Instagram** products
3. Configure webhooks:
   - **Callback URL**: `https://yourdomain.com/api/v1/webhooks/whatsapp` (or `/instagram`)
   - **Verify Token**: Must match `WEBHOOK_VERIFY_TOKEN` in your `.env`
   - **Subscribe** to `messages` field
4. Copy the **App Secret** — this is used as the webhook secret for HMAC signature verification
5. Add channels via the dashboard or API with the platform credentials

### Security Checklist for Production
- [ ] All secrets stored in environment variables (not in code)
- [ ] `DEBUG` mode disabled
- [ ] `SECRET_KEY` is a strong random value (≥32 characters)
- [ ] CORS restricted to production domains only
- [ ] Database not exposed on public ports
- [ ] SSL/TLS configured on Nginx (HTTPS only)
- [ ] Rate limiting enabled at Nginx level
- [ ] Webhook verify token is a strong random string
- [ ] Logging configured (no sensitive data in logs)
- [ ] All AI/ML providers set to production backends (not `mock`)
- [ ] Pinecone index created with correct dimensions (1536 for `text-embedding-3-small`)

### Backup

```bash
# Database backup
bash scripts/backup.sh

# Restore from backup
docker compose run --rm postgres pg_restore -U wafaa_user -d wafaa_db /path/to/backup.dump
```
