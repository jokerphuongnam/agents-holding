# example/eval — Todo API + React bench

Compare three ways to build the **same** product from the **same** short chat.

| Case | Setup | Model / effort | Score |
| --- | --- | --- | --- |
| [case-1-chat-only](case-1-chat-only/) | Single chat | grok-4.6 medium/full | [25/40](case-1-chat-only/report.md) — FAIL pass bar (no tests) |
| [case-2-naive-subagents](case-2-naive-subagents/) | Naive parallel subagents | grok-4.6 medium/full | [34/40](case-2-naive-subagents/report.md) — PASS |
| [case-3-agents-holding](case-3-agents-holding/) | agents-holding company OS | grok-4.5 low | [39/40](case-3-agents-holding/report.md) — PASS |

**Summary:** [RESULTS.md](RESULTS.md) · **Token bill:** [TOKENS.md](TOKENS.md) · **Optimize holding:** [OPTIMIZE_HOLDING.md](OPTIMIZE_HOLDING.md)

- **Input (agents):** [INPUT.md](INPUT.md)  
- **Expected (scorers only):** [EXPECTED.md](EXPECTED.md) — API + React + backend tests + FE unit/UI tests  
- **Settings / protocol / rubric:** [SETTINGS.md](SETTINGS.md), [PROTOCOL.md](PROTOCOL.md), [RUBRIC.md](RUBRIC.md)  
- **Live run ids:** [RUN_META.md](RUN_META.md)  
- **Workspaces:** `$BENCH_ROOT/case-*` (local bench dirs on the runner machine)

## Create company (product use, not only this bench)

After install, you can open a subsidiary **via chat** (`holding-ceo` → `holding-hr`) **or** via `create-company.sh` — see root [README.md](../../README.md).
