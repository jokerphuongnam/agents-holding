# Case A (plain) — BENCH_DONE

## Summary

Built a local Todo product with:

- **Backend** (`backend/`): Express 5 API, SQLite via `better-sqlite3`, CORS enabled. Endpoints for list/get/create/update/toggle/delete under `/api/todos`. Data persisted in `backend/data/todos.db`.
- **Frontend** (`frontend/`): React + Vite UI that calls the real API through the Vite `/api` proxy (also works with `VITE_API_BASE` / CORS). Supports add, edit, toggle, delete, and error display.
- **Tests**: Backend API tests with Vitest + Supertest (8 passing). Frontend unit + UI tests with Vitest + Testing Library (12 passing).
- **Docs**: `RUN.md` for install/start/test.

## How to run tests

```bash
cd backend && npm test
cd ../frontend && npm test
```

## How to run the app

See `RUN.md`. Short version: `backend` → `npm start` (port 3001); `frontend` → `npm run dev` (port 5173).

## Known gaps vs a full MVP

- No auth / multi-user / sharing.
- No pagination, filters (active/completed), or drag-and-drop reorder.
- No offline/PWA, websockets, or optimistic locking.
- Production UI preview does not include the Vite proxy (use `VITE_API_BASE` or reverse proxy).
- No Docker Compose / single-process monorepo runner.
- Minimal accessibility polish (labels present; no full a11y audit).
- No E2E (Playwright/Cypress) against live API+UI.

## Wall effort (approx.)

- **Start**: 2026-09-05T03:39:55Z
- **End**: 2026-09-05T03:43:30Z
- **Duration**: ~3.5–4 minutes
