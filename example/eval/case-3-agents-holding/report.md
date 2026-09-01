# Report — case-3-agents-holding (post-optimize overwrite)

## Meta

- Case: 3 — agents-holding (optimized re-run only)
- Model: **grok-4.5**
- Session: `01a05c70-cbda-77d3-9dc8-24c21044c52a`
- Workspace: `$BENCH_ROOT/case-3-agents-holding` (eval-todo-bench-v2 tree)
- Nested LLM subagents: **0** (ReportedTaskCompletions were bash)
- Wall: ~195s (duration_ms≈195206)

## Token bill (primary + nested LLM)

| Role | Input | Output | Reasoning | Total | costUsdTicks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary | 458,774 | 11,301 | 4,244 | **470,075** | 1,455,473,360 |
| Nested LLM | 0 | 0 | 0 | **0** | 0 |
| **Case total** | 458,774 | 11,301 | 4,244 | **470,075** | 1,455,473,360 |

vs old case 3 (1,189,278 total): **0.40×** (60% reduction)

## EXPECTED

- [x] E0–E2 (Express+React starter edited; curl+persist proven)
- [x] E3 backend unit (pass)
- [x] E4 FE unit/UI (6/6 pass)
- [ ] E5 e2e skipped (budget low policy)

**Pass bar: PASS**

## Rubric (approx)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **40/40** |

## Gaps

- Nested LLM bill N/A (none spawned; not required for this arm)
- Edit title covered; no auth (MVP)

## Efficiency notes

- task_cache show/set used
- hop once; starter edited (no Nest)
