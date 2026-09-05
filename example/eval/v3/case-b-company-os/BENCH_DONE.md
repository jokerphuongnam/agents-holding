# BENCH_DONE — Case B (Company OS)

## Ship

Local Todo MVP: Express API (`backend/`) + React/Vite UI (`frontend/`) calling real `/api` via proxy. File-backed persist, CRUD + toggle, CORS on API.

## Company OS process (conceptual cascade)

1. **ceo** — product ask received (vi); hop roster → **product-lead** first (not ba/po direct).
2. **product-lead** — ask clear enough for MVP; skipped **ba-user**; routed **po-new**.
3. **po-new** — plan at `cache/plans/todo-mvp.md` (AC + eng slices); ## Result up with `plan_dir` + read loci.
4. **ceo** — parallel handoff (slim brief) to eng via **tech-lead** ownership:
   - **backend-engineer** — store + routes + HTTP/store tests
   - **frontend-engineer** — App/api client + RTL smoke + Vite proxy
5. **qc-lead** — ran both test suites; smoke curl health + create + proxied list.
6. Docs: `RUN.md` + this file. `task_cache` / `task_memory resolve` used for resume briefs.

Roles used: ceo → product-lead → po-new → tech-lead / backend-engineer + frontend-engineer → qc-lead.  
Not used (unnecessary for clear MVP): ba-user, ba-workflow, design-lead, cto (seed already Express+React).

## Test commands

```bash
npm test --prefix backend
npm test --prefix frontend
```

Verified locally (pass):

- backend: store unit + HTTP API CRUD/toggle/health
- frontend: Vitest RTL load/add/toggle/delete (mocked fetch)

Smoke: `npm run start --prefix backend` + `npm run dev --prefix frontend`; `GET /api/health`, `POST /api/todos`, `GET localhost:5173/api/todos` via proxy.

## Gaps / non-goals

- No auth, multi-user, or e2e (budget **low** per CTO seed).
- Vite may bind IPv6 `localhost` only; use `http://localhost:5173` (not bare `127.0.0.1` if refused).
- No Nest/extra stack; starter completed in-place.
