# ADR-001: Multi-Tenancy Approach

## Status
Accepted

## Context
Wafaa AI Concierge serves multiple business tenants. Each tenant's data (conversations, knowledge base, configuration) must be completely isolated from other tenants for security and compliance reasons.

We need to choose between:
1. **Separate databases** per tenant
2. **Separate schemas** per tenant
3. **Shared schema with row-level filtering** (tenant_id column)

## Decision
Use shared schema with `tenant_id` column on all data tables, enforced at the ORM level.

## Rationale
- **Simplicity**: Single database, single connection pool, single migration path
- **Scalability**: Supports thousands of tenants without database provisioning overhead
- **Cost**: No per-tenant database infrastructure costs
- **Maintenance**: One schema to maintain, one migration to run

## Consequences

### Positive
- Faster tenant onboarding (just create a row)
- Simpler backup and restore
- Easier cross-tenant analytics (for platform admin)
- Standard PostgreSQL tooling works out of the box

### Negative
- Every query must include `tenant_id` filter (developer discipline required)
- Risk of data leakage if filter is forgotten (mitigated by ORM-level enforcement)
- Noisy neighbor potential (mitigated by connection pooling and query optimization)

### Mitigations
- `TenantModel` base class enforces `tenant_id` column on all models
- Code review checklist includes tenant isolation verification
- Automated tests verify no cross-tenant data access
- Database indexes on `tenant_id` for performance
