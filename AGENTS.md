# AGENTS.md
# Single source of truth for the coding agent and review agent.
# Automatically read by both GitHub Actions workflows.

---

## Project

Full-stack web application.

## Techstack

<!-- Customize for your project -->
- **Frontend**: React / Vue / Svelte
- **Backend**: Node/Express / FastAPI / Laravel
- **Database**: PostgreSQL / MongoDB
- **Tests**: Vitest / Jest / Pytest
- **Package manager**: npm / pnpm / pip

## Project Structure

```
/
├── frontend/          # Client-side code
├── backend/           # Server-side code
├── shared/            # Shared types and utilities
├── tests/             # Tests
└── .github/
    └── workflows/     # Conductor agent workflows
```

## Test Command

```bash
npm test
```

<!-- Customize: npm test / pnpm test / pytest / etc. -->

---

## Coding Agent Workflow

### Branch

```
feat/GH-{number}-{description}
fix/GH-{number}-{description}
docs/GH-{number}-{description}
test/GH-{number}-{description}
```

### Implementation Order

1. Backend (routes, services, database)
2. Frontend (components, state, UI)
3. Tests
4. Documentation when applicable

### Coding Rules

- Only change files needed for this issue
- Follow existing code style and naming
- Do not add new dependencies without an explicit reason in the issue
- No console.log or debug code
- No refactoring outside the scope of the issue

### Commit Format

```
{type}(GH-{number}): {description}

- What was done (bullet)
- Another bullet if needed
- Closes #{number}
```

Types: `feat` `fix` `refactor` `docs` `test` `chore`

### PR Description Always Includes

- What does this PR do?
- How to test?
- `Closes #{number}`

### Definition Of Done

- [ ] Functionality works as described in the issue
- [ ] All existing tests pass
- [ ] New tests written for new logic
- [ ] No console.log or debug code
- [ ] PR opened and linked to the issue

---

## Review criteria

This section is used by the review agent to decide whether a PR can be merged.

### Blocking Issues (No Auto-Merge)

- Failing tests
- Missing tests for new logic
- Functionality that does not match the issue
- Changes outside the scope of the issue
- Console.log or debug code present
- New dependencies without a reason
- Syntax errors or obvious bugs
- Merge conflicts

### Non-Blocking Remarks (Auto-Merge Allowed)

- Style preference (naming, formatting)
- Suggestions for a better implementation
- Missing documentation for small changes
- Small optimizations

### Auto-Merge Conditions

All of the following must be true:

1. No blocking issues found by the review agent
2. CI checks pass (tests green)
3. Branch has no conflicts with main
4. PR was created by the Conductor coding agent
