# HISTORY — case-3-agents-holding

Model: **grok-4.5** (effort requested: **low**). Workspace: `eval-todo-bench/case-3-agents-holding`.

## Pre-flight (Company OS)

- Holding install + `create-company` already applied (`slug=todo-app-company`, budget `low`, tech `typescript,react,nestjs`).
- `company_os.sh all` generated harness exports (recorded in `create-company.log`).
- **Company OS used from create-company onward** for this case (not reinvented).

## Run timeline

1. **CEO/BA channel** — Read `COMPANY.md` / boot; user ask (VN): Todo API + React, local MVP, ask if missing.
2. **hop.py** — Listed agents; roster under ceo; routed `apps/api/` → backend-engineer, `apps/web/` → frontend-engineer.
3. **ba-requirements** — Wrote `ASK_USER.md` (tests? SQLite vs other?) and plan `cache/plans/todo-mvp.md`; set `task_cache` goal.
4. **Implement** — Scaffold Nest API + Vite React; Nest todos module (DTO validation, SQLite repo, CORS); React `TodoApp` + `todosApi` with Vite `/api` proxy.
5. **QC-shaped checks** — API unit + e2e; FE unit (api client) + UI (RTL) tests; all green.
6. **Prove** — curl health/CRUD/toggle/400/404; restart API; list still returned prior todo from SQLite; then DELETE 204.
7. **Docs** — Root `README.md` + `RUN.md`; this summary/history.

## Decisions / assumptions

- No auth / single-user local app.
- SQLite file persistence (default while awaiting ASK_USER).
- Included automated tests as shippable MVP bar (also asked user in ASK_USER.md).

## Artifacts

- Product: `apps/api`, `apps/web`, `RUN.md`
- Company: `.agents/todo-app-company/cache/plans/todo-mvp.md`, task cache
- Eval reports: this file + `AGENT_SUMMARY.md`
