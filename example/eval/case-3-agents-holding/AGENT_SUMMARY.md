# AGENT_SUMMARY — case-3-agents-holding

## Outcome

Shipped a local Todo MVP under the bench workspace using **agents-holding Company OS** (already created via `create-company` → `company_os.sh all` before this run).

## Product

| Layer | Stack | Path |
| --- | --- | --- |
| API | NestJS + better-sqlite3 | `apps/api/` |
| Web | React + Vite (proxy `/api`) | `apps/web/` |

Features: list / create / get / update / delete / toggle; SQLite persistence; CORS + Vite proxy; loading / error / empty UI; RUN.md.

## Company OS usage (from create-company onward)

1. Pre-run: `create-company` (`budget=low`, `tech=typescript,react,nestjs`) → `.agents/todo-app-company` + `company_os.sh all` (see `create-company.log`).
2. This run: `COMPANY.md` / `COMPANY_BOOT.md` → user channel **ceo + ba**.
3. `hop.py --list` / `--roster ceo` / `--path apps/api/` → **backend-engineer**; `--path apps/web/` → **frontend-engineer**.
4. Customs skills referenced: `nestjs`, `react`, `ba-requirements`.
5. Artifacts: `cache/plans/todo-mvp.md`, `task_cache.py set/patch`, `ASK_USER.md` (clarifications; proceeded with SQLite + tests as sensible MVP).

## Verification

- `apps/api`: `npm test` (8) + `npm run test:e2e` (2) passed.
- `apps/web`: `npm test` (6) passed.
- Live curl against `http://localhost:3000`: health, CRUD, toggle, 400 validation, 404; data survived API restart via `apps/api/data/todos.sqlite`.

## How to run

See workspace `RUN.md`.
