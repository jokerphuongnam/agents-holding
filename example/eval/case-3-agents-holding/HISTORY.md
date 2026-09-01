# HISTORY — case-3-agents-holding-v2

Model: **grok-4.5** (effort requested: **low**). Workspace: `eval-todo-bench-v2/case-3-agents-holding`.

## Pre-flight

- Company `.agents/todo-app-company` already present (budget low, tech typescript,react,express).
- express-react starter already seeded at repo root (`backend/` + `frontend/`).
- **task_cache already seeded** — resume preferred over re-browsing ORG/skills.

## Run timeline

1. **`task_cache.py show`** — cache **hit**; placeholder goal “Company ready — wait for user product ask”; paths `backend/`, `frontend/`.
2. **Hop once** — `hop.py --list` then `--path backend/src/server.js` → backend-engineer / low / grok. No full ORG read; at most marlin-hop SKILL header for script usage.
3. **`task_cache.py set/patch`** — real product goal (Todo MVP CRUD+toggle+persist, React wired, BE unit + FE RTL); AC notes; later phase `done`.
4. **Edit starter in place** (not Nest scaffold):
   - `frontend/src/api.js` — added `updateTodo` (PATCH).
   - `frontend/src/App.jsx` — inline edit + safer toggle/delete error handling.
   - `frontend/src/App.test.jsx` — RTL add / toggle+delete / edit; cleanup between tests.
   - `frontend/src/api.test.js` — API client unit tests.
   - `backend/tests/todos.test.js` — update + validation + persist file assert.
   - Light CSS / README polish.
5. **Tests** — `npm test --prefix backend` and `npm test --prefix frontend` green.
6. **Prove with curl** — health, create, list, get, patch, toggle, 400, 404; restart same data file → todo still listed; delete 204.
7. **Eval artifacts** — this `HISTORY.md` + `AGENT_SUMMARY.md` under `agents-holding/example/eval/case-3-agents-holding-v2/`.

## Decisions / assumptions

- Kept seeded Express + JSON file store (matches company tech seed); no Nest replacement.
- No auth; single-user local MVP.
- No e2e (not requested); unit/UI tests only.
- Inline title edit added so React covers update via API, not only toggle/delete.

## Artifacts

- Product: `backend/`, `frontend/`, `RUN.md`, `README.md`
- Company: task cache under `.agents/todo-app-company/cache/cache/`
- Eval reports: `AGENT_SUMMARY.md`, `HISTORY.md` (this dir)
