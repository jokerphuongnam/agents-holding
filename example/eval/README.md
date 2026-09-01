# example/eval — Todo API + React bench

Compare three ways to build the **same** product from the **same** short chat.

| Case | Setup | Model / effort |
| --- | --- | --- |
| [case-1-chat-only](case-1-chat-only/) | Single chat | grok-4.6 medium/full |
| [case-2-naive-subagents](case-2-naive-subagents/) | Naive parallel subagents | grok-4.6 medium/full |
| [case-3-agents-holding](case-3-agents-holding/) | agents-holding company OS | grok-4.5 low |

- **Input (agents):** [INPUT.md](INPUT.md) — 1–2 lines  
- **Expected (scorers only):** [EXPECTED.md](EXPECTED.md) — API + React + backend tests + FE unit/UI tests  
- **Settings / protocol / rubric:** [SETTINGS.md](SETTINGS.md), [PROTOCOL.md](PROTOCOL.md), [RUBRIC.md](RUBRIC.md)  
- **Live run:** [RUN_META.md](RUN_META.md)  
- **Workspaces:** `$BENCH_ROOT (default: sibling eval-todo-bench outside the git clone)/case-*/`

Reports per case (`HISTORY.md`, `AGENT_SUMMARY.md`, `report.md`) are filled from **real** runs only.
