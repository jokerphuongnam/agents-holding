# Report — case-2-naive-subagents

## Meta

- Case: 2 — naive parallel subagents
- Model / effort requested: **grok-4.6** / medium / full
- Model / effort actual: grok-4.6 (effort not separately metered)
- Workspace: `$BENCH_ROOT/case-2-naive-subagents`
- Wall clock: ~394s (duration_ms=394326)
- Tokens (billed total): **unknown**
- Token proxies: 55,179 contextTokensUsed; 71 tools; 394s (signals.json) final total. Mid-run host showed ~26K context usage once; tool_calls=71, turns=2
- Subagent: `01a05c59-ec2c-7ad2-83f4-277e9ec47986`

## Input used

See `INPUT.md`.

## Transcript / Q&A history

See `HISTORY.md` + `AGENT_SUMMARY.md`. Documents naive fan-out then merge. No `ASK_USER.md`.

## Artifacts

- API: `backend/` (Express)
- React: `frontend/` (Vite + RTL tests)
- Tests re-run this scoring pass: backend **7/7**, frontend **3/3**

## EXPECTED checklist

### E0

- [x] Self-contained
- [x] Run docs
- [x] Runnable (curl proven; port 3002 when 3001 busy)
- [x] Existing libs

### E1

- [x] CRUD + toggle route
- [x] Persist JSON
- [x] 400 / 404
- [x] CORS / proxy

### E2

- [x] Real API UI flows

### E3

- [x] Backend tests pass (`node --test`)

### E4

- [x] FE unit/UI tests pass (Vitest + RTL, 3 tests)

### Pass bar

**PASS**

## Rubric scores

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 5 | 4 | 5 | 5 | 4 | 2 | 4 | **34/40** |

## Gaps

- Process thrash from intentional naive overlapping subagents (HISTORY)
- FE test count thinner than case 3
- D7 low: more wall time / tools than case 1 for similar product surface
