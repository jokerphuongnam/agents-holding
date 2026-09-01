---
name: python-core
description: >
  Pythonic structure — PEP 8, typing, packaging tooling, exceptions, async
  notes, and pytest habits. Use for Python application/library code. Not
  JS/TS or other stacks.
---

# python-core

## Who / paths

- **You:** Python application, library, CLI, and automation code for this company.
- **Not you:** TypeScript/Go/etc.; rewriting product logic in one-off notebooks without packaging; design UI.
- **Paths:** `**/*.py`, `**/pyproject.toml`, `**/requirements*.txt`, `**/uv.lock`, `**/poetry.lock`
- **Load when:** Brief names Python code changes.

## How

1. **PEP 8 + formatter.** Match Black/Ruff/isort if present. snake_case functions; PascalCase classes.

2. **Type hints.** Annotate public functions/returns. X | None (3.10+) or Optional[X] per version; prefer built-in generics on 3.9+.

3. **Tooling.** Repo standard env manager (uv/poetry/pip-tools/venv). Do not invent a second lockfile ecosystem mid-task.

4. **Exceptions.** Catch specific types; attach context with raise ... from e.

5. **Anti-pattern — bare except:** bare except or except Exception: pass.

6. **Resources.** Context managers for files/locks/sessions; close clients explicitly if needed.

7. **Imports.** Absolute preferred; no wildcard imports. No heavy side effects at import time.

8. **Data models.** dataclass / pydantic / attrs as project standard — do not mix three DTO layers casually.

9. **Async.** No blocking I/O inside async defs without an executor; avoid asyncio.run inside running loops.

10. **Security.** No secrets in source; parameterized DB queries; subprocess with shell=False + arg lists.

11. **Packaging.** Respect src/ layout if present; export public API deliberately.

12. **Logging.** logging module over print in libraries; no secrets in logs.

13. **Tests.** pytest; deterministic; mock network when needed.

## Done-when

- [ ] Public APIs type-hinted; Ruff/Black clean when tooling exists.
- [ ] No bare except; resources closed via context managers.
- [ ] Env/lockfile follows repo standard.
- [ ] Secrets not committed; subprocess/SQL safe.
- [ ] Critical changes covered by pytest when brief requires tests.
- [ ] No new import-time side effects in libraries.

## References (external)

- https://peps.python.org/pep-0008/
- https://peps.python.org/pep-0484/
- https://docs.pytest.org/en/stable/
- https://docs.python.org/3/library/logging.html
- https://github.com/HK-hub/AgentSkills
- https://www.agentskills.io/
