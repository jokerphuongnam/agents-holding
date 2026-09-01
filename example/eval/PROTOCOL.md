# Bench protocol (real runs only)

## Arms

| Case | Directory | How work is done | Model | Effort (requested) |
| --- | --- | --- | --- | --- |
| 1 | `eval-todo-bench/case-1-chat-only` | Single chat agent | **grok-4.6** | **medium** / prompt **full** |
| 2 | `eval-todo-bench/case-2-naive-subagents` | Naive parallel subagents (no org) | **grok-4.6** | **medium** / prompt **full** |
| 3 | `eval-todo-bench/case-3-agents-holding` | agents-holding from `create-company` → delivery | **grok-4.5** | **low** |

## Order of operations

1. **Lock design** — `INPUT.md`, `EXPECTED.md`, `SETTINGS.md`, `RUBRIC.md`, this file.
2. **Reset workspaces** — three clean git worktrees/dirs under `$BENCH_ROOT/` (local; outside or beside the clone).
3. **Case 3 only** — install holding → `create-company` (`react,nestjs`, budget aligned with low) → `company_os.sh all`.
4. **Open three runs** with the **same** `INPUT.md` text only.
5. **Human mid-flight** — if the agent asks, answer in-character; may point at *one* missing EXPECTED slice (e.g. “need unit tests for the API”) without pasting the whole checklist.
6. **Stop** when agent claims done **or** wall-clock/budget cap hit.
7. **Score** against `EXPECTED.md` + `RUBRIC.md` using the real tree + transcript. Record tokens only from runtime metadata (else `unknown`).

## Honesty

- No fabricated history, scores, or token counts.
- No secretly injecting `EXPECTED.md` into the first message.
- Case 3 must use the real company tree under `.agents/<slug>-company/`.
