# Token bill — primary agent + subagents

Source: final cumulative `usage` in each session’s `updates.jsonl`
(`inputTokens`, `outputTokens`, `totalTokens`, `costUsdTicks`).

## Per case (product agent)

| Case | Role | Agents with LLM bill | Input | Output | Reasoning | **Total** | costUsdTicks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Primary | 1 | 282,649 | 9,875 | 3,775 | **292,524** | 466,704,400 |
| 1 | Nested LLM subagents | **0** | 0 | 0 | 0 | **0** | 0 |
| 1 | **Case total** | 1 | 282,649 | 9,875 | 3,775 | **292,524** | 466,704,400 |
| 2 | Primary | 1 | 985,816 | 21,343 | 11,344 | **1,007,159** | 1,320,577,000 |
| 2 | Nested LLM subagents | **0** | 0 | 0 | 0 | **0** | 0 |
| 2 | **Case total** | 1 | 985,816 | 21,343 | 11,344 | **1,007,159** | 1,320,577,000 |
| 3 | Primary | 1 | 1,169,969 | 19,309 | 17,013 | **1,189,278** | 3,536,293,760 |
| 3 | Nested LLM subagents | **0** | 0 | 0 | 0 | **0** | 0 |
| 3 | **Case total** | 1 | 1,169,969 | 19,309 | 17,013 | **1,189,278** | 3,536,293,760 |

### Case totals side-by-side

| Case | **Total tokens** | vs case 1 | costUsdTicks | vs case 1 |
| --- | ---: | ---: | ---: | ---: |
| 1 chat-only | **292,524** | 1.0× | 466,704,400 | 1.0× |
| 2 naive subagents | **1,007,159** | 3.4× | 1,320,577,000 | 2.8× |
| 3 agents-holding | **1,189,278** | 4.1× | 3,536,293,760 | 7.6× |

## Important: nested “kids” were not billed LLM agents

Each primary session lists IDs under `ReportedTaskCompletions` (case1: 3, case2: 12, case3: 20). Those IDs are **background bash/monitor tasks** (dev servers, `npm test`, etc.), **not** separate Grok subagent sessions.

- No `updates.jsonl` / `usage` exists for those IDs.
- Case 2 HISTORY states explicitly: the child harness **had no `spawn_subagent` tool**, so “naive parallel tracks” were overlapping writes **inside the same primary session** — token bill stays on the primary.

So for this bench: **case total = primary total**.

## Orchestrator (parent) session — separate

The parent chat that designed the bench, launched the three cases, fixed docs, and scored them:

| Session | Input | Output | Reasoning | **Total** | costUsdTicks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parent `01a049a0-…` | 1,534,239 | 6,261 | 4,539 | **1,540,500** | 7,001,992,640 |

This is **not** part of any single case’s product bill; it spans the whole operator conversation.

### If you want “everything spent on this bench day”

| Bucket | Total tokens |
| --- | ---: |
| Case 1 | 292,524 |
| Case 2 | 1,007,159 |
| Case 3 | 1,189,278 |
| **Sum of 3 case agents** | **2,488,961** |
| Parent orchestrator | 1,540,500 |
| **Grand total (cases + parent)** | **4,029,461** |

`costUsdTicks` is the host internal cost unit (relative only; USD scale not documented here).

## How this was computed

1. Take each case primary session id from `RUN_META.md`.
2. Read final `usage` with `costUsdTicks` + `inputTokens` from `updates.jsonl`.
3. Collect child IDs from `resources_state.json` → `ReportedTaskCompletions` and from parent `subagents/*/meta.json` where `parent_session_id` matches.
4. Attempt to load each child’s `updates.jsonl` — **none** had LLM usage (bash tasks only).
5. Case total = primary (+ 0 nested LLM).
