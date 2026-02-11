# Contributing to Wafaa AI Concierge

## Development Setup

1. Clone the repository
2. Run `bash scripts/setup.sh`
3. Verify all services are running: `docker compose ps`

## Git Workflow

### Branching Strategy
```
main (production)
  |
  +-- develop (staging)
       |
       +-- feature/phase1-auth-system
       +-- feature/phase2-rag-engine
       +-- feature/phase3-channel-integration
       +-- feature/phase4-admin-dashboard
       +-- fix/tenant-isolation-bug
```

### Branch Naming
- Features: `feature/phase{N}-{description}`
- Bug fixes: `fix/{description}`
- Documentation: `docs/{description}`

### Commit Message Convention
```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore

Scopes: auth, rag, channels, chat, knowledge, analytics,
        agent-analytics, webhooks, dashboard, api, db, models

Examples:
feat(auth): implement JWT refresh token logic
feat(knowledge): add document reprocessing endpoint
feat(channels): add WhatsApp webhook signature verification
feat(analytics): add sentiment distribution endpoint
feat(agent-analytics): add response time trend chart
fix(rag): correct vector search tenant filtering
docs(api): update webhook endpoint documentation
test(auth): add tenant isolation verification tests
test(channels): add WhatsApp webhook payload parsing tests
```

## Code Standards

### Python (Backend)
- **Style**: Ruff for linting and formatting
- **Types**: Full type hints on all functions
- **Docstrings**: Google style on all public functions
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### TypeScript (Dashboard)
- **Style**: Prettier + ESLint
- **Types**: Strict mode, no `any`
- **Components**: Functional components with hooks
- **Naming**: `camelCase` for functions, `PascalCase` for components

## Testing

### Running Tests
```bash
# All backend tests
docker compose run --rm backend pytest -v

# With coverage report
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Specific test files
docker compose run --rm backend pytest tests/test_auth.py -v
docker compose run --rm backend pytest tests/test_rag_engine.py -v
docker compose run --rm backend pytest tests/test_channels_api.py -v
docker compose run --rm backend pytest tests/test_analytics_api.py -v
docker compose run --rm backend pytest tests/test_agent_analytics_api.py -v
```

### Test Modules
| Test File                        | Count | Coverage Area                        |
|----------------------------------|-------|--------------------------------------|
| `test_health.py`                 | 3     | Health check endpoints               |
| `test_auth.py`                   | 12    | Login, refresh, logout, token validation |
| `test_tenants.py`                | 9     | Tenant CRUD, admin management        |
| `test_tenant_isolation.py`       | 5     | Cross-tenant data isolation          |
| `test_knowledge_api.py`          | 15    | Document upload, list, get, delete   |
| `test_document_processor.py`     | 8     | Text extraction (TXT, CSV, JSON)     |
| `test_rag_engine.py`             | 7     | Context retrieval, RAG query         |
| `test_chat_api.py`               | 5     | Chat endpoint, auth, isolation       |
| `test_whatsapp_webhook.py`       | 11    | Webhook verify, signature, parsing   |
| `test_instagram_webhook.py`      | 6     | Webhook verify, signature, parsing   |
| `test_channels_api.py`           | 9     | Channel CRUD, tenant isolation       |
| `test_analytics_api.py`          | 8     | Analytics endpoints                  |
| `test_sentiment_analyzer.py`     | 6     | VADER sentiment analysis             |
| `test_intent_classifier.py`      | 10    | Intent pattern matching              |
| `test_agent_analytics_api.py`    | 13    | Agent analytics endpoints            |

### Coverage Requirements
- Authentication: 95%+
- RAG Engine: 90%+
- Message Routing: 90%+
- API Endpoints: 85%+
- UI Components: 80%+

## Security Checklist

Before submitting any PR, verify:
- [ ] All database queries filter by `tenant_id`
- [ ] Authentication required on protected endpoints
- [ ] Webhook endpoints verify HMAC-SHA256 signatures
- [ ] Input validation on all user inputs
- [ ] No secrets in code or committed files
- [ ] Error messages don't expose internal details

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Ruff linting and formatting (Python)
- Prettier formatting (TypeScript/CSS)
