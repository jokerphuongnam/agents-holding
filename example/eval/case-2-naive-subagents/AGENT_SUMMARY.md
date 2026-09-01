# AGENT_SUMMARY — case-2-naive-subagents

Shipped a local Todo MVP: Express JSON API + Vite React frontend. Product code lives in `$BENCH_ROOT/case-2-naive-subagents`.

Process: naive overlapping tracks (backend / frontend / docs / tests) without a locked API contract, then merge. Did **not** use agents-holding to build the product.

## Run instructions

From the product workspace:

```bash
cd $BENCH_ROOT/case-2-naive-subagents
npm --prefix backend install
npm --prefix frontend install

# terminal 1
npm --prefix backend start

# terminal 2
npm --prefix frontend start
```

- API: http://localhost:3001 (this run used **3002** because case-1 already held 3001)
- UI: http://localhost:5173 (Vite proxies `/api` → `http://localhost:3001`)

## API (merged contract)

| Method | Path | Body |
| --- | --- | --- |
| GET | `/api/health` | |
| GET | `/api/todos` | |
| GET | `/api/todos/:id` | |
| POST | `/api/todos` | `{ "title": "Buy milk" }` |
| PATCH | `/api/todos/:id` | `{ "title"?: string, "completed"?: boolean }` |
| POST | `/api/todos/:id/toggle` | |
| DELETE | `/api/todos/:id` | |

Todo: `{ id, title, completed, createdAt, updatedAt }`. Persist file: `backend/data/todos.json`.

## Tests (this session)

```bash
npm --prefix backend test   # 7 passed
npm --prefix frontend test  # 3 passed (RTL: empty, error/retry, create/toggle/edit/delete)
```

## Curl proof (this session, API on :3002)

```bash
curl -sS http://127.0.0.1:3002/api/health
# {"ok":true}

curl -sS -X POST http://127.0.0.1:3002/api/todos \
  -H 'Content-Type: application/json' -d '{"title":"Buy milk"}'
# 201 {"id":"f8efaf8b-391e-4be5-b254-ba6ac4b3f897","title":"Buy milk","completed":false,...}

curl -sS -X PATCH http://127.0.0.1:3002/api/todos/f8efaf8b-391e-4be5-b254-ba6ac4b3f897 \
  -H 'Content-Type: application/json' -d '{"title":"Buy oat milk"}'

curl -sS -X POST http://127.0.0.1:3002/api/todos/f8efaf8b-391e-4be5-b254-ba6ac4b3f897/toggle
# completed:true

# killed API, restarted on 3002, list still had Buy oat milk
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  -X DELETE http://127.0.0.1:3002/api/todos/f8efaf8b-391e-4be5-b254-ba6ac4b3f897
# HTTP 204
```

Also: empty title → `400 {"error":"title is required"}`; missing id → `404 {"error":"Todo not found"}`; frontend `GET http://127.0.0.1:5173/` → `200`.

## Assumptions

- Vietnamese request, English UI labels.
- No auth / multi-user / due dates.
- JSON file store (existing Node `fs`), Express, Vite, React — no NIH.
- `completed` boolean (not `done`); toggle is a dedicated POST.
- Ports 3001 / 5173 by default.

## Gaps

- No login or per-user isolation.
- File store is single-process.
- Frontend Vite proxy still points at 3001; this bench machine already had case-1 on 3001, so live UI proxy was not the case-2 process.
- No Playwright/Cypress E2E.
- No `ASK_USER.md` — shipped a default MVP.

## Token stats

unknown
