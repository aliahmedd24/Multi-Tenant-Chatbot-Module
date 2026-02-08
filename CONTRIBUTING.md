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
Scopes: auth, rag, channels, dashboard, api, db

Examples:
feat(auth): implement JWT refresh token logic
fix(rag): correct vector search tenant filtering
docs(api): update webhook endpoint documentation
test(auth): add tenant isolation verification tests
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
# Backend tests
docker compose run --rm backend pytest -v

# Backend tests with coverage
docker compose run --rm backend pytest --cov=app --cov-report=term-missing

# Specific test file
docker compose run --rm backend pytest tests/test_health.py -v
```

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
