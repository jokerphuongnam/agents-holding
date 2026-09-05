# Output / acceptance (evaluator only — NOT in the first user message)

Agents see only `INPUT.md`. Scorers use this after the run.
Mid-flight (vibe-coding simulation): if the agent asks or ships thin, the human may reveal **one missing slice at a time** — never dump this whole file.

Product: **Todo** — realistic small product (API + React + tests + docs), not a toy snippet.

## E0 — Repo & run

- [ ] Self-contained under the case worktree
- [ ] `RUN.md` (or README) starts **API** and **React** (ports documented)
- [ ] Fresh clone path: install → run API → run UI → UI talks to API
- [ ] Idiomatic stack (Express/Nest/Fastify + Vite/CRA/Next-SPA OK) — no NIH HTTP/React

## E1 — Backend API

- [ ] Create todo (`title` required)
- [ ] List todos
- [ ] Get one by id (or documented equivalent)
- [ ] Update todo (title and/or done)
- [ ] Delete todo
- [ ] Toggle done (route or update — documented)
- [ ] Persistent storage across restart (sqlite/file/db — not memory-only)
- [ ] Sensible HTTP status + JSON errors (validation / not-found)
- [ ] CORS or proxy so React origin can call API

## E2 — Frontend (React)

- [ ] List from API on load
- [ ] Add via API
- [ ] Toggle via API
- [ ] Edit title via API
- [ ] Delete via API
- [ ] Loading + error UI
- [ ] Empty state
- [ ] No fake in-memory-only list that never hits the network

## E3 — Backend tests

- [ ] Tests for create/list/update/delete/toggle (or service layer)
- [ ] At least one validation / not-found case
- [ ] One documented command; tests pass locally

## E4 — Frontend tests

- [ ] Unit test for a non-trivial module (API client / helpers / logic)
- [ ] UI/component test: list + add or toggle/delete (mock fetch OK in tests only)
- [ ] Documented command; tests pass locally

## E5 — Bonus (optional)

- [ ] E2E Playwright/Cypress
- [ ] OpenAPI / typed client

## Pass bar

**E0 + E1 + E2 + E3 + E4** all checked. Score with `history/RUBRIC.md` (D1–D8, /40).
