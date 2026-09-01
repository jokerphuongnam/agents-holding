# Report — case-3-agents-holding

## Meta

- Case: 3 — agents-holding Company OS end-to-end
- Model / effort requested: **grok-4.5** / **low**
- Model / effort actual: grok-4.5 (effort not separately metered)
- Workspace: `$BENCH_ROOT/case-3-agents-holding`
- Wall clock: ~497s (duration_ms=497459) **plus** pre-step `create-company` + `company_os` (~1s logged)
- Tokens: **unknown** final total. Mid-run host showed ~40K context once; tool_calls=96, turns=2
- Subagent: `01a05c59-ec2c-7ad2-83f4-278f29d974b2`
- Pre-step: `create-company.log` (`budget=low`, `tech=typescript,react,nestjs`)

## Input used

See `INPUT.md`.

## Transcript / Q&A history

See `HISTORY.md` + `AGENT_SUMMARY.md`. Agent wrote `ASK_USER.md` (clarifications on tests/persistence) then proceeded with SQLite + tests as MVP defaults.

## Artifacts

- API: `apps/api/` NestJS + SQLite
- React: `apps/web/` Vite
- Company OS: `.agents/todo-app-company/`
- Tests re-run this scoring pass: API jest **8/8**; web vitest **6/6** (agent also reported e2e 2)

## EXPECTED checklist

### E0–E2

- [x] All (RUN.md, Nest+React, real proxy, persist SQLite, CORS, full UI flows)

### E3

- [x] Service unit tests + not-found/validation; pass

### E4

- [x] API client unit + TodoApp UI tests (RTL); pass

### E5 bonus

- [x] API e2e suite present (`test/app.e2e-spec.ts`) per agent report

### Pass bar

**PASS** (+ E2E bonus)

## Rubric scores

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 5 | 5 | 5 | 5 | 5 | 4 | 5 | **39/40** |

## Gaps

- Final token totals still not exposed by host (same limitation as other cases)
- `ASK_USER.md` in the **bench workspace** briefly used Vietnamese in headings (workspace artifact; not part of agents-holding SoT after English purge)
- D7: more tool calls than case 1, but delivered full EXPECTED under **low** model setting
