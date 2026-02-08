---
trigger: always_on
---

# AI Agent Development Rules for Wafaa AI Concierge

## Project Context

You are working on **Wafaa AI Concierge**, a multi-tenant B2B SaaS platform that enables brands and restaurants to deploy AI-powered customer service chatbots across social media channels (WhatsApp, Instagram, TikTok, Snapchat). The system uses Retrieval-Augmented Generation (RAG) to provide accurate, contextual responses based on each client's specific knowledge base while maintaining complete data isolation.

**Critical Architecture Principle**: Every feature must respect tenant isolation - no tenant should ever access another tenant's data.

## Mandatory Logging Requirements

### Session Logging Protocol

You **MUST** maintain a `LOG.md` file in the project root directory. Update this file at the **END of EVERY coding session** with the following structure:

```markdown
## Session [YYYY-MM-DD HH:MM] - [Phase X: Feature Name]

### Objective
[What was the goal of this session?]

### Work Completed
- [ ] Task 1 description
- [ ] Task 2 description
- [ ] Task 3 description

### Code Changes
- **Files Modified**: `path/to/file1.py`, `path/to/file2.ts`
- **Files Created**: `path/to/newfile.py`
- **Files Deleted**: `path/to/oldfile.py`

### Tests Added/Modified
- [ ] Test file: `tests/test_feature.py` - Test description
- [ ] Coverage: X% for module Y

### Issues Encountered
1. **Issue**: Description of problem
   - **Solution**: How it was resolved
   - **Decision**: Why this approach was chosen

### Next Steps
1. [ ] Next task to complete
2. [ ] Technical debt to address
3. [ ] Dependencies to resolve

### Notes
- Important observations
- Performance considerations
- Security concerns addressed

---
```

### When to Update LOG.md
- After completing a feature or sub-feature
- Before switching to a different phase/module
- At the end of each coding session
- When encountering and resolving significant issues
- When making architecture decisions

### Log File Location
- **Path**: `/LOG.md` (project root)
- **Format**: Markdown with clear session dividers
- **Retention**: Keep entire project history (do not delete old entries)

## Project Scope Boundaries

### ✅ IN SCOPE - You Should Work On:

1. **Phase 0-5 Implementation**
   - Follow PRD documents exactly as specified
   - Implement features in phase order (0→1→2→3→4→5)
   - Complete all "Definition of Done" criteria before marking phase complete

2. **Core Platform Features**
   - Multi-tenant database architecture with tenant_id isolation
   - JWT authentication and authorization
   - Knowledge base management (upload, process, embed)
   - RAG pipeline (vector search + LLM generation)
   - Channel integrations (WhatsApp, Instagram)
   - Admin dashboard with React/TypeScript
   - Message processing and conversation management
   - Human agent handoff
   - Analytics and reporting

3. **Code Quality Requirements**
   - Write comprehensive unit and integration tests
   - Follow type hints (Python) and strict types (TypeScript)
   - Implement proper error handling
   - Add docstrings and code comments
   - Follow security best practices

4. **Infrastructure Setup**
   - Docker Compose configurations
   - Database migrations with Alembic
   - Celery worker setup
   - Redis caching implementation
   - CI/CD pipeline configuration

### ❌ OUT OF SCOPE - Do Not Implement:

1. **Features Not in PRDs**
   - Do NOT add features beyond Phase 0-5 specifications
   - Do NOT implement Phase 6+ features unless explicitly requested
   - Do NOT add "nice-to-have" features without approval

2. **Alternative Architectures**
   - Do NOT change core architecture decisions (e.g., switching from FastAPI to Flask)
   - Do NOT replace specified tech stack without explicit permission
   - Do NOT implement microservices pattern (keep monolith as designed)

3. **Third-Party Integrations Not Specified**
   - Do NOT add channels beyond WhatsApp/Instagram in Phase 3
   - Do NOT integrate payment systems (out of scope)
   - Do NOT add social login providers not mentioned in PRDs

4. **Advanced AI Features Before Phase 5**
   - Do NOT implement voice recognition in early phases
   - Do NOT add image recognition until explicitly requested
   - Do NOT build custom ML models (use specified APIs)

5. **Enterprise Features Not Specified**
   - Do NOT implement SSO/SAML without explicit request
   - Do NOT add multi-language support beyond configuration
   - Do NOT build white-label features prematurely

## Development Guidelines

### Code Organization

1. **Follow Directory Structure** from PRDs exactly
2. **Naming Conventions**:
   - Python: `snake_case` for functions/variables, `PascalCase` for classes
   - TypeScript: `camelCase` for functions/variables, `PascalCase` for components
   - Files: `kebab-case.ts` or `snake_case.py`

3. **Module Organization**:
   - Keep related code together (models, schemas, services)
   - One class/major function per file (except utilities)
   - Clear separation of concerns (API, business logic, data access)

### Data Isolation Rules

**CRITICAL**: Every database query and vector search **MUST** filter by `tenant_id`. This is non-negotiable.

```python
# ✅ CORRECT - Always filter by tenant_id
conversations = db.query(Conversation).filter(
    Conversation.tenant_id == current_user.tenant_id
).all()

# ❌ WRONG - Never query without tenant filter
conversations = db.query(Conversation).all()  # NEVER DO THIS
```

### Security Checklist

Before marking any feature complete, verify:
- [ ] All database queries filter by tenant_id
- [ ] Authentication required on protected endpoints
- [ ] Input validation on all user inputs
- [ ] No secrets in code or logs
- [ ] SQL injection prevented (use parameterized queries)
- [ ] XSS prevented (sanitize user content)
- [ ] CSRF tokens on state-changing requests
- [ ] Rate limiting implemented on public endpoints

### Testing Requirements

Minimum test coverage by module:
- **Authentication**: 95%+ (critical path)
- **RAG Engine**: 90%+ (core functionality)
- **Message Routing**: 90%+ (business critical)
- **API Endpoints**: 85%+
- **UI Components**: 80%+

### Error Handling Standards

```python
# ✅ CORRECT - Structured error handling
try:
    result = some_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", extra={"tenant_id": tenant_id})
    raise HTTPException(status_code=500, detail="Operation failed")

# ❌ WRONG - Bare except or exposing internal details
try:
    result = some_operation()
except:  # Too broad
    return {"error": str(e)}  # Exposes internal details
```

### Performance Considerations

Always implement:
1. **Database Indexes**: On tenant_id, timestamps, foreign keys
2. **Query Optimization**: Use pagination, limit results
3. **Caching**: Cache frequently accessed data (Redis)
4. **Async Operations**: Use async/await for I/O operations
5. **Connection Pooling**: Configure appropriate pool sizes

## Communication Protocol

### When to Ask for Clarification

**ASK** when:
- Requirements in PRD are ambiguous or conflicting
- Security implications are unclear
- Performance trade-offs need business decision
- Architecture changes would impact multiple phases
- Third-party API limits or costs are concerning

**DO NOT ASK** for:
- Formatting preferences (follow PRD)
- Variable naming (use conventions above)
- File organization (follow directory structure)
- Testing approaches (follow coverage requirements)

### Progress Reporting Format

When providing updates:
```markdown
## Progress Update: [Feature Name]

**Status**: [In Progress / Completed / Blocked]

**Completed**:
- [x] Subtask 1
- [x] Subtask 2

**In Progress**:
- [ ] Subtask 3 (70% done)

**Blocked**:
- [ ] Subtask 4 - Waiting for: [reason]

**Next Steps**:
1. Complete subtask 3
2. Begin subtask 5

**Estimated Completion**: [Date]
```

## Phase Transition Protocol

Before moving to next phase:

1. **Complete Definition of Done**
   - Review checklist in phase PRD
   - Verify all tests pass
   - Run security checks

2. **Update LOG.md**
   - Summarize phase completion
   - Document any deviations from PRD
   - List technical debt

3. **Create Phase Summary**
   - Lines of code added
   - Test coverage achieved
   - Performance benchmarks met
   - Known issues/limitations

4. **Request Phase Review**
   - Present summary
   - Highlight critical decisions
   - Propose next phase start

## Quick Reference

### Essential Files to Always Check
1. **master_prd_index.md** - Project overview
2. **phase[N]_*_prd.md** - Current phase specifications
3. **LOG.md** - Project history and decisions
4. **ARCHITECTURE.md** - System design (when created)
5. **.env.example** - Required environment variables

### Tech Stack by Layer
- **API**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy
- **Cache**: Redis 7
- **Queue**: Celery + Redis Streams
- **Vector DB**: Pinecone or Weaviate
- **LLM**: OpenAI GPT-4o / Anthropic Claude 3.5 Sonnet
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Container**: Docker + Docker Compose

### Key Commands
```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose run --rm backend alembic upgrade head

# Run tests
docker-compose run --rm backend pytest

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Enforcement

These rules are **mandatory**. Non-compliance includes:
- Not updating LOG.md after sessions
- Implementing out-of-scope features
- Skipping tests
- Violating data isolation principles
- Ignoring security checklist

If you encounter situations where these rules conflict with project needs, **document the conflict in LOG.md** and seek clarification before proceeding.

---

**Remember**: Quality over speed. Complete each phase properly before moving forward. The multi-tenant architecture requires rigorous attention to data isolation - shortcuts here can cause catastrophic security breaches.

**Current Phase**: Phase 0 (setup) unless explicitly told otherwise.

**Log File Status**: Create LOG.md in project root on first commit if it doesn't exist.