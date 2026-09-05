# Token bill — primary agent + nested LLM subagents

Source: final cumulative `usage` in each session’s `updates.jsonl`
(`inputTokens`, `outputTokens`, `totalTokens`, `costUsdTicks`).

## Per case (product agents)

| Case | Role | Agents with LLM bill | Input | Output | Reasoning | **Total** | costUsdTicks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Primary | 1 | 282,649 | 9,875 | 3,775 | **292,524** | 466,704,400 |
| 1 | Nested LLM subagents | **0** | 0 | 0 | 0 | **0** | 0 |
| 1 | **Case total** | 1 | 282,649 | 9,875 | 3,775 | **292,524** | 466,704,400 |
| 2 | Nested LLM (BE+FE+docs+merge) | **4** | 2,353,282 | 51,812 | 29,101 | **2,405,094** | 3,669,545,200 |
| 2 | **Case total** | 4 | 2,353,282 | 51,812 | 29,101 | **2,405,094** | 3,669,545,200 |
| 3 | Primary (optimized) | 1 | 458,774 | 11,301 | 4,244 | **470,075** | 1,455,473,360 |
| 3 | Nested LLM subagents | **0** | 0 | 0 | 0 | **0** | 0 |
| 3 | **Case total** | 1 | 458,774 | 11,301 | 4,244 | **470,075** | 1,455,473,360 |

### Case totals side-by-side

| Case | **Total tokens** | vs case 1 | costUsdTicks | vs case 1 |
| --- | ---: | ---: | ---: | ---: |
| 1 chat-only | **292,524** | 1.0× | 466,704,400 | 1.0× |
| 2 naive nested LLM | **2,405,094** | 8.2× | 3,669,545,200 | 7.9× |
| 3 agents-holding (optimized) | **470,075** | 1.6× | 1,455,473,360 | 3.1× |

## Case 2 nested breakdown

| Role | Session | Total |
| --- | --- | ---: |
| Backend | `01a05c79-96a0-7203-b26d-156f4a09febf` | 356,468 |
| Frontend | `01a05c79-96bb-7182-8270-4cc11c859bb6` | 266,139 |
| Docs | `01a05c79-96bb-7182-8270-4cd4d6d86222` | 61,228 |
| Merge | `01a05c7c-3cdc-7fe1-8826-c3bd84f80267` | 1,721,259 |
| **Sum** | | **2,405,094** |

**Methodology:** a case-2 product child cannot call `spawn_subagent`, so the parent chat spawned the three tracks + merge. Case total = those four LLM sessions only.  
**Excluded:** abort primary `01a05c75` (1,014,816) and old v1 primary `01a05c59` (1,007,159, bash-only “kids”).

## Case 3 note

Post `task_cache` + Express starter optimize. Old case-3 primary was 1,189,278 → now **470,075** (~0.40×). Nested LLM still 0 (bash task completions only).

## Orchestrator (parent) session — separate

Parent chat that designed the bench, launched cases, spawned case-2 kids, and scored:

| Session | **Total** (snapshot; grows) | Note |
| --- | ---: | --- |
| Parent `01a049a0-…` | not fixed into case totals | Spans whole operator conversation |

Parent bill is **not** part of any single case’s product total.

### Sum of three case agents (current fair bills)

| Bucket | Total tokens |
| --- | ---: |
| Case 1 | 292,524 |
| Case 2 (nested LLM) | 2,405,094 |
| Case 3 (optimized) | 470,075 |
| **Sum of 3 cases** | **3,167,693** |

## How this was computed

1. Case 1: primary `01a05c59-…276c2a0e5f48` final usage.
2. Case 2: export each of the four nested sessions’ `updates.jsonl` → sum (`usage.json`).
3. Case 3: primary `01a05c70-cbda-77d3-9dc8-24c21044c52a` → `usage.json`.
4. Bash/monitor task IDs under `ReportedTaskCompletions` have no LLM usage — ignored.
