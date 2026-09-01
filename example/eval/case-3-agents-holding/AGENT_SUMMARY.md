# AGENT_SUMMARY — case-3-agents-holding-v2

## Outcome

Shipped a local Todo MVP under `eval-todo-bench-v2/case-3-agents-holding` by **editing the seeded express-react starter** (`backend/` + `frontend/`). Did **not** re-scaffold Nest or replace the tree.

## Product

| Layer | Stack | Path |
| --- | --- | --- |
| API | Express + JSON file store | `backend/` |
| Web | React + Vite (proxy `/api`) | `frontend/` |

Features: list / create / get / update (PATCH) / delete / toggle; file persistence (`TODO_DATA_FILE` or `backend/data/todos.json`); CORS + Vite proxy; loading / error / empty / inline edit UI; `RUN.md` + README.

## Company OS / efficiency

1. Pre-seeded: `.agents/todo-app-company` (budget low, tech typescript,react,express) + express-react starter + **task_cache**.
2. **First command:** `task_cache.py show` → **hit** (`goal: Company ready — wait for user product ask`, paths `backend/`, `frontend/`).
3. **Hop once:** `hop.py --list` + `hop.py --path backend/src/server.js` → **backend-engineer** (tier low). Did not re-read whole ORG / skill catalog; no extra SKILL.md load (hop returned `skill: —`).
4. After routing: `task_cache.py set` with real product goal, then `patch` (AC + phase done). Notes record cache hit and in-place starter edit.

## Verification

- Backend: `npm test --prefix backend` — pass (store create/list/update/toggle/delete + validation + file persist).
- Frontend: `npm test --prefix frontend` — pass (api client unit ×3; App RTL add/toggle/delete/edit ×3).
- Live curl on `:3011`: health, CRUD, toggle, 400 validation, 404; **list survived API restart** via same `TODO_DATA_FILE`; DELETE 204 → empty list.

## How to run

See workspace `RUN.md` (API `:3001`, UI `:5173`).
