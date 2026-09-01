# Results summary (real runs)

Same **INPUT.md**. Scorers used **EXPECTED.md** (API + React + backend tests + FE unit/UI tests). No fabricated scores.

| Case | Setup | Model | Tests (re-verified) | Pass bar | Score | **Case total tokens** |
| --- | --- | --- | --- | --- | ---: | ---: |
| [1](case-1-chat-only/report.md) | Chat only | grok-4.6 | none / thin | **FAIL** (missed E3/E4 bar) | **25/40** | **292,524** |
| [2](case-2-naive-subagents/report.md) | Naive nested LLM (3 tracks + merge) | grok-4.6 | BE 13/13, FE 7/7 | **PASS** | **36/40** | **2,405,094** |
| [3](case-3-agents-holding/report.md) | agents-holding optimized | grok-4.5 low | API + FE 6/6 | **PASS** | **40/40** | **470,075** |

**Token bill (primary + nested LLM):** [TOKENS.md](TOKENS.md).

| Case | Nested LLM agents | Nested total | **Case total** | vs case 1 | Score |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | **292,524** | 1.0× | 25/40 |
| 2 | 4 | 2,405,094 | **2,405,094** | 8.2× | 36/40 |
| 3 | 0 | 0 | **470,075** | 1.6× | 40/40 |
| **Sum of 3 cases** |  |  | **3,167,693** |  |  |

## Takeaway

- **Case 1** cheapest/fastest path but **missed the test bar** in EXPECTED.
- **Case 2** with real nested LLM is the **most expensive** (conflicting tracks + heavy merge ≈ 1.7M tokens on merge alone) while scoring below holding.
- **Case 3** (Company OS + starter + `task_cache`, grok-4.5 low) is **~5.1× cheaper than nested case 2** and hits the fullest EXPECTED surface in this bench.

Workspaces (local): `$BENCH_ROOT` = `~/Documents/Agents/eval-todo-bench` (case 3 optimized tree under `eval-todo-bench-v2/case-3-agents-holding`).
