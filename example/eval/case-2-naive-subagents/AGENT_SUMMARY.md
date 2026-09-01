# AGENT_SUMMARY — case-2-naive-subagents (merge)

**Status: SHIPPED.** Naive parallel tracks merged into one working Todo MVP.

This session (`01a05c7c-3cdc-7fe1-8826-c3bd84f80267`) is the **MERGE** agent. Three nested LLM subagents had already written conflicting contracts. Merge kept the Express backend, aligned routes/ports with the Vite UI, fixed docs, and proved tests + curl.

## Conflicts resolved

| Track | Original assumption | Merge |
| --- | --- | --- |
| Backend | Express `/todos`, field `done`, port **4000** | Kept Express + `done` + port **4000**; routes moved to `/api/todos` |
| Frontend | Vite `/api/todos`, field `done`, proxy to **3001** | Kept `/api/todos` + `done`; proxy retargeted to **4000** |
| Docs | Imagined FastAPI on **8000** | Discarded. README/smoke describe the real Express + Vite product |

Port 3001 was occupied on this machine by case-1 (`completed` field). Merge chose **4000** so this product can run beside it.

## Run instructions

From `$BENCH_V1/case-2-naive-subagents`:

```bash
npm install
npm run install:all
npm run dev
```

- API: http://localhost:4000
- UI: http://localhost:5173 (Vite proxies `/api` → `http://localhost:4000`)

## API

| Method | Path | Body |
| --- | --- | --- |
| GET | `/health` | |
| GET | `/api/health` | |
| GET | `/api/todos` | |
| GET | `/api/todos/:id` | |
| POST | `/api/todos` | `{ "title": "Buy milk" }` |
| PATCH | `/api/todos/:id` | `{ "title"?: string, "done"?: boolean }` |
| DELETE | `/api/todos/:id` | |

Todos persist in `backend/data/todos.json`. Toggle is `PATCH` `{ "done": true }`.

## Tests (this session)

```
cd backend && npm test   # 13/13 pass (node:test + supertest)
cd frontend && npm test  # 7/7 pass (Vitest + RTL)
```

## Curl proof (this session)

Servers started:

- API `cd backend && node src/server.js` → `Todo API listening on http://localhost:4000`
- UI `cd frontend && npx vite --host 127.0.0.1 --port 5173` → `http://127.0.0.1:5173/`

```bash
curl -sS http://127.0.0.1:4000/health
# {"ok":true,"service":"todo-api"}

curl -sS -X POST http://127.0.0.1:4000/api/todos \
  -H 'Content-Type: application/json' -d '{"title":"Ship MVP"}'
# 201 {"id":"d49b433a-7d1b-4167-bfbd-17c074efec16","title":"Ship MVP","done":false,...}

curl -sS -X PATCH http://127.0.0.1:4000/api/todos/d49b433a-7d1b-4167-bfbd-17c074efec16 \
  -H 'Content-Type: application/json' -d '{"done":true}'
# 200 done:true

curl -sS -X POST http://127.0.0.1:4000/api/todos -H 'Content-Type: application/json' -d '{}'
# 400 {"error":"title is required"}

curl -sS -X PATCH http://127.0.0.1:4000/api/todos/not-a-real-id \
  -H 'Content-Type: application/json' -d '{"done":true}'
# 404 {"error":"todo not found"}

curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  -X DELETE http://127.0.0.1:4000/api/todos/d49b433a-7d1b-4167-bfbd-17c074efec16
# HTTP 204

curl -sS -o /dev/null -w "GET / HTTP %{http_code}\n" http://127.0.0.1:5173/
# GET / HTTP 200

curl -sS http://127.0.0.1:5173/api/health
# {"ok":true,"service":"todo-api"}  (Vite proxy)
```

`./scripts/smoke.sh` → `smoke: ok (backend http://127.0.0.1:4000, frontend http://127.0.0.1:5173)`

## Child subagent ids

- `01a05c79-96a0-7203-b26d-156f4a09febf`
- `01a05c79-96bb-7182-8270-4cc11c859bb6`
- `01a05c79-96bb-7182-8270-4cd4d6d86222`

Primary launcher was parent (`PARENT_SPAWNED`). Merge session: `01a05c7c-3cdc-7fe1-8826-c3bd84f80267`.

## Token stats

unknown
