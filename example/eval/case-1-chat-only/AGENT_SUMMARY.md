# AGENT_SUMMARY — case-1-chat-only

Shipped a local Todo MVP: Express JSON API + Vite React frontend. Product code lives in `$BENCH_V1/case-1-chat-only`.

## Run instructions

From the product workspace:

```bash
cd $BENCH_V1/case-1-chat-only
npm install
npm run install:all
npm run dev
```

- API: http://localhost:3001
- UI: http://localhost:5173 (Vite proxies `/api` → backend)

Servers were started during this run and verified live:

- API `npm run start:backend` → `Todo API listening on http://localhost:3001`
- UI `npm run dev:frontend` → `http://localhost:5173/`

## API

| Method | Path | Body |
| --- | --- | --- |
| GET | `/api/health` | |
| GET | `/api/todos` | |
| POST | `/api/todos` | `{ "title": "Buy milk" }` |
| PATCH | `/api/todos/:id` | `{ "title"?: string, "completed"?: boolean }` |
| DELETE | `/api/todos/:id` | |

Todos persist in `backend/data/todos.json` (atomic write).

## Curl proof (this session)

Health:

```bash
curl -sS http://localhost:3001/api/health
# {"ok":true,"service":"todo-api"}
```

Create / list / patch / delete:

```bash
curl -sS -X POST http://localhost:3001/api/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Ship MVP"}'
# 201 {"id":"8f7dbcf3-...","title":"Ship MVP","completed":false,...}

curl -sS http://localhost:3001/api/todos
# 200 array

curl -sS -X PATCH http://localhost:3001/api/todos/8f7dbcf3-af40-454f-91b4-329a92a4911e \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
# 200 completed:true

curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  -X DELETE http://localhost:3001/api/todos/8f7dbcf3-af40-454f-91b4-329a92a4911e
# HTTP 204
```

Also verified:

- empty title → `HTTP 400 {"error":"title is required"}`
- unknown id → `HTTP 404 {"error":"todo not found"}`
- file persist after delete: remaining todo `"Write docs"` in `backend/data/todos.json`
- frontend `GET http://localhost:5173/` → `HTTP 200`
- frontend proxy `GET http://localhost:5173/api/todos` returns the same persisted list

## Assumptions

- Vietnamese request, English code/UI labels (standard for a local MVP unless asked otherwise).
- No auth, no multi-user, no due dates, no tags.
- JSON file store instead of SQLite/Postgres — enough for local MVP, survives restart.
- REST shape: UUID ids, `title`, `completed`, `createdAt`, `updatedAt`.
- Title required, max 200 chars; PATCH accepts `title` and/or `completed`.
- Frontend: add, toggle, inline edit (double-click or Edit), delete, filter all/active/done.
- Ports 3001 (API) and 5173 (Vite). CORS limited to those localhost origins; Vite proxy used by the UI.
- No Docker, no tests, no TypeScript.

## Gaps

- No login / per-user isolation.
- File store is not concurrent-safe beyond a single Node process.
- No due dates, priority, lists/projects, search, or undo.
- No automated test suite (manual curl only).
- npm warned that `esbuild` postinstall is not covered by `allowScripts`; Vite still started successfully this session.
- Did not ask the user extra questions; shipped a default MVP.

## Token stats

unknown
