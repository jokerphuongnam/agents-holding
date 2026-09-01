# Results summary (real runs)

Same **INPUT.md**. Scorers used **EXPECTED.md** (API + React + backend tests + FE unit/UI tests). No fabricated scores.

| Case | Setup | Model | Wall | Tests (re-verified) | Pass bar | Total |
| --- | --- | --- | --- | --- | --- | --- |
| [1](case-1-chat-only/report.md) | Chat only | grok-4.6 | ~174s | none | **FAIL** (no E3/E4) | **25/40** |
| [2](case-2-naive-subagents/report.md) | Naive subagents | grok-4.6 | ~394s | BE 7/7, FE 3/3 | **PASS** | **34/40** |
| [3](case-3-agents-holding/report.md) | agents-holding | grok-4.5 low | ~497s (+ create-company) | API 8/8, FE 6/6 (+ e2e) | **PASS** | **39/40** |

**Token bill (primary + nested LLM subagents):** [TOKENS.md](TOKENS.md).  
Nested LLM subagents billed **0** extra (ReportedTaskCompletions were bash tasks; case 2 never got `spawn_subagent`).  
**Why case 3 was expensive / how to cut:** [OPTIMIZE_HOLDING.md](OPTIMIZE_HOLDING.md).

| Case | Primary total | Nested LLM total | **Case total** | costUsdTicks | Score |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 292,524 | 0 | **292,524** | 1.0× | 25/40 |
| 2 | 1,007,159 | 0 | **1,007,159** | 2.8× | 34/40 |
| 3 | 1,189,278 | 0 | **1,189,278** | 7.6× | 39/40 |
| **Sum of 3 cases** |  |  | **2,488,961** |  |  |

## Takeaway

- Case 1 shipped a working UI↔API fastest but **missed the test bar** in EXPECTED.
- Case 2 met EXPECTED after messy merge; higher time/tools than case 1.
- Case 3 (Company OS from create-company, **grok-4.5 low**) hit the fullest EXPECTED surface (Nest+SQLite+stronger tests).

Workspaces (local, not required inside git clone): `$BENCH_ROOT` = `~/Documents/Agents/eval-todo-bench` on the machine that ran this bench.
