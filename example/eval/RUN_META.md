# Live run metadata

## Case 1 (chat-only — kept)

| Field | Value |
| --- | --- |
| Subagent id | `01a05c59-ec2c-7ad2-83f4-276c2a0e5f48` |
| Model | grok-4.6 |
| Total tokens | 292,524 |
| Score | 25/40 |

## Case 2 (naive nested LLM — overwrite)

| Field | Value |
| --- | --- |
| Launcher | Parent chat (`PARENT_SPAWNED`) |
| Children | `01a05c79-96a0-7203-b26d-156f4a09febf` (BE), `01a05c79-96bb-7182-8270-4cc11c859bb6` (FE), `01a05c79-96bb-7182-8270-4cd4d6d86222` (docs) |
| Merge | `01a05c7c-3cdc-7fe1-8826-c3bd84f80267` |
| Model | grok-4.6 |
| Case total tokens | **2,405,094** |
| Score | 36/40 |
| Workspace | `eval-todo-bench/case-2-naive-subagents` |

Excluded: abort primary `01a05c75-…`, old v1 primary `01a05c59-…277e9ec47986`.

## Case 3 (agents-holding optimized — overwrite)

| Field | Value |
| --- | --- |
| Subagent id | `01a05c70-cbda-77d3-9dc8-24c21044c52a` |
| Model | grok-4.5 |
| Total tokens | 470,075 |
| Score | 40/40 |
| Workspace | `eval-todo-bench-v2/case-3-agents-holding` |
