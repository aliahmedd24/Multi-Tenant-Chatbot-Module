---
description: Read at the start of every session.
---

# Initial Prompt for Claude Code - Wafaa AI Concierge Project

## Session Initialization Protocol

Before beginning any work on this project, you MUST:

1. **Read .agent/rules/general.md** - This file contains all project guidelines, scope boundaries, and mandatory workflows
2. **Read LOG.md** - Review the latest session entries to understand current project state and recent decisions
3. **Identify Current Phase** - Determine which phase (0-5) you're working on from the last LOG.md entry
4. **Read Current Phase PRD** - Open the relevant `phase[N]_*_prd.md` file for detailed specifications

## Session Start Checklist

Execute this checklist at the START of EVERY session:

```markdown
## Session Start: [YYYY-MM-DD HH:MM]

- [ ] Read RULES.md completely
- [ ] Reviewed LOG.md - last 3 sessions
- [ ] Identified current phase: Phase [N]
- [ ] Opened phase[N]_*_prd.md for reference
- [ ] Reviewed "Definition of Done" for current phase
- [ ] Checked for any blockers from previous session
- [ ] Confirmed working in correct git branch (if applicable)
```

## Core Directives

### 1. MANDATORY: Reference RULES.md First

**EVERY session starts with:**
```
I have read RULES.md and understand:
- Mandatory LOG.md update requirements
- Data isolation principles (tenant_id filtering)
- Project scope boundaries (IN/OUT scope)
- Security checklist requirements
- Testing coverage requirements
- Phase transition protocol

Current Phase: [Phase N - Feature Name]
Current Objective: [Brief description from PRD]
```

### 2. MANDATORY: Update LOG.md at Session End

Before ending ANY session, you MUST update LOG.md with:
- Session timestamp and phase/feature
- Objective of the session
- Work completed (checklist format)
- Code changes (files modified/created/deleted)
- Tests added/modified with coverage
- Issues encountered and solutions
- Next steps for next session
- Important notes/decisions

**Failure to update LOG.md is a critical violation of project rules.**

### 3. MANDATORY: Tenant Isolation Verification

Before committing ANY code that touches the database, verify:
```python
# Every query MUST filter by tenant_id
✅ CORRECT:
data = db.query(Model).filter(Model.tenant_id == current_user.tenant_id).all()

❌ WRONG - NEVER DO THIS:
data = db.query(Model).all()
```

### 4. MANDATORY: Scope Adherence

**IN SCOPE** (proceed with implementation):
- Features explicitly listed in phase PRDs
- Security improvements
- Performance optimizations
- Bug fixes
- Test coverage improvements
- Documentation updates

**OUT OF SCOPE** (require explicit approval):
- Features not in phase PRDs
- Architecture changes not documented in ADRs
- New third-party integrations
- Phase 6+ features
- "Nice-to-have" additions

If unsure, **ASK** before implementing.

## Workflow by Session Type

### Session Type A: Feature Implementation

```
1. Review feature specification in phase PRD
2. Check "Definition of Done" criteria
3. Implement feature following tech stack specified
4. Write tests (meet coverage requirements)
5. Verify security checklist
6. Update LOG.md
7. Mark feature as complete in LOG.md
```

### Session Type B: Bug Fix

```
1. Document issue in LOG.md
2. Reproduce bug with test case
3. Implement fix
4. Verify fix doesn't break tenant isolation
5. Run full test suite
6. Update LOG.md with solution and decision rationale
```

### Session Type C: Phase Transition

```
1. Review "Definition of Done" for current phase
2. Verify all checklist items complete
3. Run full test suite
4. Check test coverage meets requirements
5. Create phase summary in LOG.md
6. Document technical debt
7. Request phase review before proceeding
8. ONLY proceed to next phase after approval
```

### Session Type D: Setup/Configuration

```
1. Follow Phase 0 PRD specifications exactly
2. Verify all services start correctly
3. Test with seed data
4. Document any deviations in LOG.md
5. Create troubleshooting notes
```

## Quick Reference Commands

### Before Starting Work
```bash
# Check current project state
git status
docker-compose ps
cat LOG.md | tail -n 50  # Review last entries

# Verify services running
docker-compose logs -f backend
```

### During Development
```bash
# Run tests frequently
docker-compose run --rm backend pytest -v

# Check test coverage
docker-compose run --rm backend pytest --cov=app --cov-report=term-missing

# Verify database migrations
docker-compose run --rm backend alembic current
```

### Before Committing
```bash
# Run linting
docker-compose run --rm backend ruff check app/
docker-compose run --rm backend ruff format app/

# Run security checks
docker-compose run --rm backend bandit -r app/

# Verify tenant isolation in tests
docker-compose run --rm backend pytest tests/test_tenant_isolation.py -v
```

## Communication Templates

### Starting a Session
```
Starting session for Wafaa AI Concierge.

✅ Read RULES.md
✅ Reviewed LOG.md (last session: [date])
✅ Current Phase: Phase [N] - [Feature Name]
✅ Objective: [Brief description]

Ready to begin. Next task: [specific task from PRD or LOG.md]
```

### Ending a Session
```
Session complete. Updating LOG.md now.

Summary:
- Completed: [X tasks]
- Tests: [Y tests added, Z% coverage]
- Next session: [Next task]

LOG.md updated ✅
```

### Requesting Clarification
```
⚠️ Clarification needed:

**Context**: [What you're working on]
**Question**: [Specific question]
**Impact**: [Why this matters]
**Options Considered**: [If applicable]

Pausing work until clarification received.
```

## Critical Reminders

### Security (Non-Negotiable)
- ✅ All queries filter by tenant_id
- ✅ Authentication required on protected endpoints
- ✅ Input validation on all user inputs
- ✅ No secrets in code or committed files
- ✅ Error messages don't expose internals

### Testing (Minimum Requirements)
- Authentication: 95%+ coverage
- RAG Engine: 90%+ coverage
- Message Routing: 90%+ coverage
- API Endpoints: 85%+ coverage
- UI Components: 80%+ coverage

### Data Isolation (Life-or-Death)
Every database query, vector search, cache key, and file path MUST include tenant_id. No exceptions. This is the foundation of the entire system.

## Error Recovery Protocol

If you encounter:

**Build Errors**:
1. Document error in LOG.md
2. Check docker-compose.yml configuration
3. Verify environment variables
4. Review recent code changes
5. Consult phase PRD for configuration details

**Test Failures**:
1. Don't proceed with new features
2. Document failing tests in LOG.md
3. Fix tests before continuing
4. Verify tenant isolation not broken
5. Re-run full test suite

**Scope Confusion**:
1. Stop work immediately
2. Re-read RULES.md scope boundaries
3. Check if feature is in current phase PRD
4. Document question in LOG.md
5. Request clarification

## Phase-Specific Notes

**Phase 0**: Focus on setup automation, ensure reproducibility
**Phase 1**: Tenant isolation is critical - verify exhaustively
**Phase 2**: RAG accuracy depends on proper embeddings - test thoroughly
**Phase 3**: Webhook security is paramount - validate signatures
**Phase 4**: UI/UX consistency - follow design system strictly
**Phase 5**: Performance monitoring - instrument everything

## Final Checklist Before Any Code Commit

```markdown
- [ ] Code follows tech stack specified in PRD
- [ ] All database queries filter by tenant_id
- [ ] Tests written and passing (meet coverage requirements)
- [ ] Security checklist verified
- [ ] No secrets in code
- [ ] Error handling implemented
- [ ] Code documented with docstrings
- [ ] LOG.md updated with session details
- [ ] No out-of-scope features added
```

---

## How to Use This Prompt

**Copy and paste this entire document** into Claude Code at the start of EVERY session. This ensures:

1. Consistent adherence to project rules
2. Proper logging and documentation
3. Scope discipline
4. Security best practices
5. Quality standards maintained

**Remember**: This is a multi-tenant system. One mistake in tenant isolation can expose all customers' data. Take security seriously. Test thoroughly. Document everything.

---

**Current Project Status**: [To be filled by reviewing LOG.md]
**Current Phase**: [To be determined from LOG.md]
**Next Task**: [To be identified from LOG.md or PRD]

BEGIN SESSION.