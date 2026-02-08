# Phase 1: Foundation & Core Infrastructure

## Objective
Establish the foundational multi-tenant architecture with database schemas, authentication system, and basic tenant management. This phase creates the data isolation layer and core backend structure that all subsequent features will build upon.

## Tech Stack
- **Backend Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Migration Tool**: Alembic
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt
- **Environment Management**: python-dotenv
- **Validation**: Pydantic V2
- **Testing**: pytest, pytest-asyncio
- **API Documentation**: FastAPI built-in Swagger/OpenAPI

## User Flow
1. System administrator initializes the database with migration scripts
2. Admin creates initial tenant accounts through API or seed script
3. Tenant admin receives credentials and authenticates to receive JWT token
4. Tenant admin can view their tenant configuration and basic metadata
5. All subsequent API calls include tenant context via JWT authentication

## Technical Constraints
- **Data Isolation**: All database queries must include tenant_id filtering at ORM level
- **No Shared Resources**: Each tenant's data must be completely isolated in the database
- **Security**: All passwords must be hashed; no plain text storage
- **API Standards**: RESTful conventions with proper HTTP status codes
- **Error Handling**: Structured error responses with consistent format
- **Local Development**: Must run on localhost without external dependencies initially

## Data Schema

### Tenants Table
```python
{
    "id": "UUID (Primary Key)",
    "name": "String (255) - Client business name",
    "slug": "String (100) - URL-safe identifier, unique",
    "created_at": "Timestamp",
    "updated_at": "Timestamp",
    "is_active": "Boolean - Account status",
    "subscription_tier": "Enum (free, basic, premium)",
    "settings": "JSONB - Flexible configuration storage"
}
```

### Tenant Admins Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "email": "String (255) - Unique",
    "password_hash": "String (255)",
    "full_name": "String (255)",
    "role": "Enum (owner, admin, viewer)",
    "created_at": "Timestamp",
    "last_login": "Timestamp - Nullable",
    "is_active": "Boolean"
}
```

### Audit Log Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "user_id": "UUID (Foreign Key to Tenant Admins) - Nullable",
    "action": "String (100) - Action type",
    "resource_type": "String (100) - What was modified",
    "resource_id": "String (255) - Nullable",
    "details": "JSONB - Additional context",
    "ip_address": "String (45) - IPv4/IPv6",
    "created_at": "Timestamp"
}
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Tenant admin login
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - Invalidate token

### Tenant Management
- `GET /api/v1/tenants/me` - Get current tenant details
- `PATCH /api/v1/tenants/me` - Update tenant settings
- `GET /api/v1/tenants/me/admins` - List tenant admins
- `POST /api/v1/tenants/me/admins` - Add new admin

### Health & System
- `GET /health` - System health check
- `GET /api/v1/system/info` - API version and status

## Directory Structure
```
wafaa-backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── admin.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tenant.py
│   │   ├── admin.py
│   │   └── auth.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── tenants.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_tenants.py
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
└── README.md
```

## Environment Variables
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/wafaa_db

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=Wafaa AI Concierge
APP_VERSION=1.0.0
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

## Definition of Done

### Code Requirements
- [ ] All database models created with proper relationships and constraints
- [ ] Alembic migrations run successfully and are reversible
- [ ] JWT authentication system implemented with access and refresh tokens
- [ ] Tenant context middleware ensures data isolation on all queries
- [ ] Password hashing implemented with bcrypt (min cost factor 12)
- [ ] All API endpoints return proper HTTP status codes
- [ ] Pydantic schemas validate all input/output data
- [ ] Structured logging implemented with tenant_id in all logs

### Testing Requirements
- [ ] Unit tests for all models achieve 90%+ coverage
- [ ] Integration tests for authentication flow (login, refresh, logout)
- [ ] Test data isolation: queries with tenant_id A cannot access tenant B data
- [ ] Test invalid JWT tokens are rejected
- [ ] Test expired tokens trigger proper error responses
- [ ] Test concurrent requests from different tenants don't leak data
- [ ] Load test with 100 concurrent tenant authentications completes successfully

### Functional Requirements
- [ ] Can create 3 test tenants via seed script or API
- [ ] Each tenant admin can log in and receive valid JWT
- [ ] Tenant A admin cannot access Tenant B's data via any API call
- [ ] Audit log captures all create/update/delete operations
- [ ] API documentation (Swagger) is accessible at /docs
- [ ] Health endpoint returns 200 with database connection status
- [ ] System runs locally without errors on fresh PostgreSQL installation

### Security Requirements
- [ ] No passwords stored in plain text
- [ ] SQL injection protection verified through parameterized queries
- [ ] CORS configured to block unauthorized origins
- [ ] Rate limiting discussed and planned for Phase 2
- [ ] No sensitive data in error messages or logs
- [ ] Environment variables used for all secrets (no hardcoding)

### Documentation Requirements
- [ ] README.md includes setup instructions
- [ ] Database schema documented with ER diagram or description
- [ ] API endpoints documented in OpenAPI/Swagger
- [ ] .env.example provided with all required variables
- [ ] Code comments explain complex business logic
- [ ] Migration scripts include descriptive comments

## Success Metrics
- Database initialization completes in < 5 seconds
- Authentication endpoint responds in < 200ms
- Zero data leakage between tenants in 100 test scenarios
- All tests pass in CI/CD pipeline
- Code adheres to PEP 8 style guidelines

## Next Phase Dependencies
Phase 2 (Knowledge Base & RAG) requires:
- Tenant UUID structure from this phase
- Authentication middleware for protecting upload endpoints
- Audit logging system for tracking knowledge base changes
