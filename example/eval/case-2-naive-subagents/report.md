# Report — case-2-naive-subagents (nested LLM overwrite)

## Meta

- Case: 2 — naive parallel **LLM** subagents (real `spawn_subagent`)
- Model: **grok-4.6**
- Launcher: parent chat (`PARENT_SPAWNED`) — case-2 child session cannot call `spawn_subagent`
- Nested LLM sessions: backend + frontend + docs + merge (see `children_ids.json`, `usage.json`)
- Workspace: `$BENCH_ROOT/case-2-naive-subagents`
- Merge wall: ~551s (`01a05c7c-3cdc-7fe1-8826-c3bd84f80267`)

## Token bill (nested LLM only — case total)

| Role | Session | Total | costUsdTicks |
| --- | --- | ---: | ---: |
| Backend | `01a05c79-…156f4a09febf` | 356,468 | 568,616,000 |
| Frontend | `01a05c79-…4cc11c859bb6` | 266,139 | 577,439,000 |
| Docs | `01a05c79-…4cd4d6d86222` | 61,228 | 119,530,400 |
| Merge | `01a05c7c-…c3bd84f80267` | 1,721,259 | 2,403,959,800 |
| **Case total** | 4 agents | **2,405,094** | **3,669,545,200** |

Excluded from case total: abort primary `01a05c75` (1,014,816) and old v1 primary `01a05c59` (1,007,159).

## Product (after merge)

- Express API on **:4000**, routes `/api/todos`, field `done`
- Vite React UI, proxy `/api` → `:4000`
- Tests: backend **13/13**, frontend **7/7**
- Curl + smoke proven in merge session

## EXPECTED checklist

### E0–E2

- [x] Self-contained, run docs, runnable, CRUD+toggle, persist, 400/404, UI↔API

### E3–E4

- [x] Backend tests pass (13/13)
- [x] FE unit/UI tests pass (7/7)

### Pass bar

**PASS**

## Rubric scores (post-merge)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 5 | 5 | 5 | 5 | 5 | 2 | 4 | **36/40** |

## Gaps

- Intentional process thrash (3 conflicting tracks + expensive merge) — D7 stays low
- Docs track invented FastAPI; discarded at merge
- No agents-holding / task_cache (by design for this arm)
