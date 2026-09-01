# HISTORY — case-2-naive-subagents

Chronological log of this run. Real turns only.

1. Workspace `/Users/phuongnampham/Documents/Agents/eval-todo-bench/case-2-naive-subagents` was empty except the bench README. User input: Vietnamese Todo API + React MVP, ask if something is missing. Operator constraints: naive parallel tracks (backend / frontend / docs / tests) **without** a shared API contract first, then merge; do not use agents-holding to build; prove with curl; existing libs; persist todos; write `AGENT_SUMMARY.md` + `HISTORY.md` here when done.
2. This harness has no spawn-subagent tool (only background bash / monitors). Did **not** start agents-holding. Implemented the four tracks as overlapping parallel file writes in one session, with no contract markdown locked first.
3. Independent choices before merge:
   - Backend: Express + CORS + `node:test`, JSON file store, routes under `/api`, field `completed`, extra `POST /todos/:id/toggle`, UUID ids.
   - Frontend: Vite + React 18 + fetch `/api/todos`, loading / empty / error+retry, add / toggle / edit / delete.
   - Docs: root README with run + curl.
   - Tests: backend HTTP tests against a temp file store; frontend RTL + vitest with mocked `fetch`.
4. Merge: kept `/api` prefix + `completed` (not `done`) + toggle POST + PATCH for title/completed. Frontend `api.js` aligned to that. No Nest/SQLite — used Express + `fs`.
5. Installed existing packages (`express`, `cors`, `react`, `vite`, `@testing-library/*`, `vitest`, `jsdom`). Backend tests 7/7 pass. Frontend tests 3/3 pass.
6. Port 3001 already used by case-1 (`node src/server.js` in `eval-todo-bench/case-1-chat-only/backend`). Started **this** API on `PORT=3002` with `TODO_DATA_FILE=backend/data/todos.json`. Vite UI started on `127.0.0.1:5173`.
7. Curl proof on :3002: health, empty list, POST create, GET by id, PATCH title, POST toggle, 400 empty title, 404 missing. Confirmed persist file. Killed API, restarted, list still had `Buy oat milk`. DELETE → 204, list `[]`. Frontend HTML 200.
8. No `ASK_USER.md`. Wrote this file and `AGENT_SUMMARY.md`.
