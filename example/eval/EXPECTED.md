# Expected acceptance (evaluator only — NOT in the first user message)

Agents see only `INPUT.md`. Scorers use this checklist after the run.
Mid-flight: if the agent asks, the human may reveal **one missing slice at a time** (same as a real chat) — never dump this whole file.

Product: **Todo** — backend API + **React** frontend calling the real API (no mock-only UI).

## E0 — Repo & run

- [ ] Project is self-contained under the case workspace
- [ ] `RUN.md` (or README section) documents how to start **API** and **React**
- [ ] Fresh machine can follow docs and reach a working UI↔API loop
- [ ] Uses existing libraries/frameworks (Nest/Express/Fastify/etc. + Vite/CRA/Next-as-SPA OK) — no NIH HTTP stack / no hand-rolled React

## E1 — Backend API

- [ ] Create todo (`title` required)
- [ ] List todos
- [ ] Get one by id (or documented equivalent)
- [ ] Update todo (title and/or done)
- [ ] Delete todo
- [ ] Toggle done (dedicated route **or** update — documented)
- [ ] Persistent storage across process restart (sqlite / file / db — not memory-only)
- [ ] Sensible HTTP status + JSON error shape on validation/not-found
- [ ] CORS (or proxy) so the React origin can call the API

## E2 — Frontend (React)

- [ ] List todos from API on load
- [ ] Add todo via API
- [ ] Toggle done via API
- [ ] Edit title via API (inline or form)
- [ ] Delete via API
- [ ] Loading and error UI for failed requests
- [ ] Empty state when there are no todos
- [ ] No “fake” in-memory-only list that never hits the network

## E3 — Backend automated tests

- [ ] Unit/integration tests for todo service or handlers (create/list/update/delete/toggle)
- [ ] At least one not-found / validation failure case
- [ ] Tests runnable via one documented command (e.g. `npm test` / `pnpm test`)
- [ ] Tests pass in CI-less local run

## E4 — Frontend automated tests

- [ ] **Unit** tests for at least one non-trivial module (e.g. API client, todo list state helpers, or component logic) with React Testing Library or equivalent
- [ ] **UI / component** tests: render list, add flow, toggle or delete interaction (mocked fetch OK **only** in unit/UI tests; app itself must still call real API in RUN.md manual path)
- [ ] Documented test command; tests pass locally

## E5 — Optional but scored if present

- [ ] E2E (Playwright/Cypress) against running API+UI — bonus, not required for MVP pass
- [ ] OpenAPI / typed client — bonus

## Pass bar (MVP “ship”)

Must have **E0 + E1 + E2 + E3 + E4** all checked (E5 optional).

## Scoring map

Use `RUBRIC.md` dimensions D1–D8 after mapping failed EXPECTED items into **gaps**.
