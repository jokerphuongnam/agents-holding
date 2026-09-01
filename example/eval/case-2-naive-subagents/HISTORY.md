# HISTORY — case-2-naive-subagents (merge)

Chronological log of the merge run. Real work only.

1. User input (product): merge three naive tracks into one working Todo API + React UI; align routes/ports; keep Express; field `done` OK; tests + curl proof; fix README; overwrite eval artifacts. Operator overlay: `children_ids.json` must list the three nested LLM ids exactly; `primary` = `PARENT_SPAWNED`.
2. This merge session id: `01a05c7c-3cdc-7fe1-8826-c3bd84f80267`. Workspace: `$BENCH_V1/case-2-naive-subagents`.
3. Read the three TRACK files:
   - Backend: Express `/todos`, `done`, port 4000.
   - Frontend: Vite `/api/todos`, `done`, proxy to 3001.
   - Docs: imagined FastAPI on 8000; root README described that fiction.
4. Merge decision: keep Express + `done`; move API routes to `/api/todos`; keep API port **4000**; retarget Vite proxy 3001 → 4000 (3001 was already bound by case-1-chat-only).
5. Code: `backend/src/app.js` routes `/api/todos` (+ `/health` and `/api/health`); `backend/src/server.js` default `PORT=4000`; `frontend/vite.config.js` proxy target `http://localhost:4000`. Backend tests updated to `/api/todos`. Frontend RTL tests cover list/empty, add, toggle, delete; API client unit tests added. `handleAdd` guarded against double-submit.
6. Docs: root `README.md` rewritten to the real Express + Vite product. `backend/TRACK.md`, `frontend/TRACK.md`, `docs/TRACK.md` record original assumptions vs merged contract. `scripts/smoke.sh` curls health + CRUD on port 4000. Root `package.json` added (`concurrently` + `install:all` / `dev` / `test`).
7. Tests: backend **13/13** pass; frontend **7/7** pass.
8. Live servers: `cd backend && node src/server.js` → `http://localhost:4000`; `cd frontend && npx vite --host 127.0.0.1 --port 5173`. Curl proved health, POST 201, PATCH `done`, 400, 404, DELETE 204, UI 200, Vite proxy `/api/health`. `./scripts/smoke.sh` ok.
9. Overwrote eval artifacts under `agents-holding/example/eval/case-2-naive-subagents/`.

## Child subagent_id list (exact ids)

- `01a05c79-96a0-7203-b26d-156f4a09febf`
- `01a05c79-96bb-7182-8270-4cc11c859bb6`
- `01a05c79-96bb-7182-8270-4cd4d6d86222`

## Primary / this session

- primary: `PARENT_SPAWNED`
- merge session: `01a05c7c-3cdc-7fe1-8826-c3bd84f80267`
- merge_agent: Grok Build MERGE subagent for naive case-2
