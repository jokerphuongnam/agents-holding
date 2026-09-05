# Results summary (real runs)

## Latest — v3 two-arm (plain vs Company OS)

Full detail: [`v3/RESULTS.md`](v3/RESULTS.md) · tokens [`v3/TOKENS.md`](v3/TOKENS.md) · input [`v3/INPUT.md`](v3/INPUT.md) · output [`v3/OUTPUT.md`](v3/OUTPUT.md).

Same **one-sentence vibe INPUT**. Scorers used **OUTPUT.md**. Tokens from `turn_completed.usage`.

| Case | Setup | Wall | Tokens | Score | Pass bar |
| --- | --- | ---: | ---: | ---: | --- |
| [A](v3/case-a-plain/BENCH_DONE.md) | Plain chat (no OS) | **244s** | **657,966** | **39/40** | **PASS** |
| [B](v3/case-b-company-os/BENCH_DONE.md) | **agents-holding** Company OS | **159s** | **478,849** | **39/40** | **PASS** |

| Gap A → B | |
| --- | --- |
| Tokens | **B −27%** (~179k fewer) |
| Wall | **B −35%** (~85s faster) |
| Score | tie 39/40 (B thinner FE test file count) |

**Evidence (no fabricated runs):** raw agent `chat_history.jsonl` + `CHAT_TRANSCRIPT.md` under `v3/case-*` (and v1 `case-*`).

**Takeaway:** with equal pass bar, Company OS is **faster and cheaper** than plain vibe chat on this Todo MVP.

---

## History — v1 three-arm

Archived under [`history-v1/`](history-v1/). Case folders `case-1-*` … `case-3-*` keep original reports.

| Case | Setup | Score | Tokens |
| --- | --- | ---: | ---: |
| [1](case-1-chat-only/report.md) | Chat only | **25/40** | **292,524** |
| [2](case-2-naive-subagents/report.md) | Naive nested LLM | **36/40** | **2,405,094** |
| [3](case-3-agents-holding/report.md) | agents-holding optimized | **40/40** | **470,075** |

| Case | Nested LLM | Case total | vs case 1 | Score |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0 | **292,524** | 1.0× | 25/40 |
| 2 | 4 | **2,405,094** | 8.2× | 36/40 |
| 3 | 0 | **470,075** | 1.6× | 40/40 |

**v1 takeaway:** case 1 missed test bar; case 2 most expensive; case 3 hit fullest EXPECTED ~5.1× cheaper than nested case 2.

**v3 vs v1:** B ≈ case 3 tokens; B ≈ **0.20×** case 2 tokens; A now passes tests (unlike case 1) but costs more than failed chat-only.
