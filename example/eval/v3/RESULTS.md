# Results v3 (real runs) + history

Same **INPUT.md** (one Vietnamese vibe sentence). Scorers used **OUTPUT.md**. Tokens from session `turn_completed.usage`.

## History context (v1 three-arm)

| Case (v1) | Setup | Score | Tokens | Wall (if known) |
| --- | --- | ---: | ---: | --- |
| 1 chat-only | No OS | **25/40** | **292,524** | — |
| 2 naive nested LLM | No OS | **36/40** | **2,405,094** | — |
| 3 agents-holding optimized | OS + starter | **40/40** | **470,075** | — |

Source: `history/RESULTS-v1.md`, `history/TOKENS-v1.md`. Workspaces: `history/workspaces-v1`, `history/workspaces-v2`.

## This run (2 arms)

| Case | Setup | Wall time | Tokens | Score /40 | Pass bar (E0–E4) | Notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| **A** plain | No Company OS | **244s** | **657,966** | **39/40** | **PASS** | Express+SQLite+Vite; BE 8, FE 12 tests |
| **B** company-os | agents-holding plugin | **159s** | **478,849** | **39/40** | **PASS** | Starter+OS cascade; BE 2, FE 1 RTL (covers CRUD UX) |

Details: `case-a-plain/BENCH_DONE.md`, `case-b-company-os/BENCH_DONE.md`, `TOKENS.md`, `RUN_META.md`.

### Rubric snapshot (/40)

| Dim | A | B | Note |
| --- | ---: | ---: | --- |
| D1 API | 5 | 5 | CRUD+toggle+persist+errors |
| D2 React↔API | 5 | 5 | Real proxy/network UI |
| D3 Run docs | 5 | 5 | RUN.md |
| D4 Libs | 5 | 5 | Express/React idiomatic |
| D5 BE tests | 5 | 5 | Pass locally |
| D6 FE tests | 5 | 4 | A deeper suite; B one RTL covering flows |
| D7 Process/tokens | 4 | 5 | B fewer tokens + documented OS cascade |
| D8 Gaps | 5 | 5 | No pass-bar blockers |
| **Total** | **39** | **39** | |

## Gap (A vs B)

| Metric | A | B | Gap |
| --- | ---: | ---: | --- |
| Score | 39 | 39 | **0** |
| Tokens | 657,966 | 478,849 | **B −27%** (saves ~179k) |
| Wall | 244s | 159s | **B −35%** (~85s faster) |
| FE test depth | 12 tests | 1 RTL | A thicker automated FE |

## Gap vs history

| Compare | Score | Tokens |
| --- | --- | --- |
| B (v3) vs case 3 (v1) | 39 vs 40 | 478,849 vs 470,075 (~same ballpark) |
| A (v3) vs case 1 (v1) | 39 vs 25 | 658k vs 293k (A now hits test bar; more tokens than failed chat-only) |
| B (v3) vs case 2 (v1) | 39 vs 36 | **0.20×** tokens of naive nested LLM |

Chat-by-chat narrative compare: [`CHAT_COMPARE.md`](CHAT_COMPARE.md).

## Takeaway

- With **history included**: Company OS remains the efficient way to hit the full Todo bar vs naive multi-agent (v1 case 2).
- **This 2-arm run:** both shipped a passing MVP; **plugin arm (B)** was **faster and cheaper on tokens** than plain chat (A), with slightly thinner FE test surface.
- Vibe INPUT (one sentence) + mid-flight autonomy worked; neither arm needed human OUTPUT drip for pass bar in this run.
