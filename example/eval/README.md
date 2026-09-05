# example/eval — Todo API + React bench

## Latest: v3 (2 arms + history)

| Case | Setup | Wall | Tokens | Score |
| --- | --- | ---: | ---: | ---: |
| [A plain](v3/case-a-plain/) | No Company OS | 244s | 657,966 | **39/40** PASS |
| [B company-os](v3/case-b-company-os/) | **agents-holding** plugin | 159s | 478,849 | **39/40** PASS |

**B is −27% tokens and −35% wall vs A** at the same score.

- Pack: [`v3/`](v3/) — `INPUT.md`, `OUTPUT.md`, `RESULTS.md`, `TOKENS.md`, `PROTOCOL.md`, `SETTINGS.md`, `RUN_META.md`
- Local worktrees (runner): `~/Documents/Agents/eval-todo-bench-v3/`

## History: v1 (3 arms)

| Case | Setup | Score | Tokens |
| --- | --- | ---: | ---: |
| [case-1-chat-only](case-1-chat-only/) | Single chat | 25/40 FAIL bar | 292,524 |
| [case-2-naive-subagents](case-2-naive-subagents/) | Naive nested LLM | 36/40 PASS | 2,405,094 |
| [case-3-agents-holding](case-3-agents-holding/) | agents-holding | 40/40 PASS | 470,075 |

Snapshots: [`history-v1/`](history-v1/). Summary: [RESULTS.md](RESULTS.md) · [TOKENS.md](TOKENS.md).

## Shared refs

- Rubric: [RUBRIC.md](RUBRIC.md)  
- Optimize notes: [OPTIMIZE_HOLDING.md](OPTIMIZE_HOLDING.md)  
- Root install / create-company: [../../README.md](../../README.md)

## Agent chat history (raw + transcript)

| Arm | Transcript | Raw JSONL |
| --- | --- | --- |
| v3 A plain | [CHAT_TRANSCRIPT.md](v3/case-a-plain/CHAT_TRANSCRIPT.md) | [chat_history.jsonl](v3/case-a-plain/chat_history.jsonl) |
| v3 B company-os | [CHAT_TRANSCRIPT.md](v3/case-b-company-os/CHAT_TRANSCRIPT.md) | [chat_history.jsonl](v3/case-b-company-os/chat_history.jsonl) |
| v1 case 1 | [CHAT_TRANSCRIPT.md](case-1-chat-only/CHAT_TRANSCRIPT.md) | [chat_history.jsonl](case-1-chat-only/chat_history.jsonl) |
| v1 case 2 | [chat/](case-2-naive-subagents/chat/) (backend/frontend/docs/merge) | same folder |
| v1 case 3 | [CHAT_TRANSCRIPT.md](case-3-agents-holding/CHAT_TRANSCRIPT.md) | [chat_history.jsonl](case-3-agents-holding/chat_history.jsonl) |
