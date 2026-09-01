# Live run metadata

Design locked first (`INPUT.md`, `EXPECTED.md`, `PROTOCOL.md`), then workspaces reset, then agents launched.

| Case | Subagent id | Model | Effort requested | Workspace |
| --- | --- | --- | --- | --- |
| 1 | `01a05c59-ec2c-7ad2-83f4-276c2a0e5f48` | grok-4.6 | medium / full | `$BENCH_ROOT/case-1-chat-only` |
| 2 | `01a05c59-ec2c-7ad2-83f4-277e9ec47986` | grok-4.6 | medium / full | `$BENCH_ROOT/case-2-naive-subagents` |
| 3 | `01a05c59-ec2c-7ad2-83f4-278f29d974b2` | grok-4.5 | low | `$BENCH_ROOT/case-3-agents-holding` |

- Agents receive **INPUT.md text only** (EXPECTED withheld).
- Mid-flight: if `ASK_USER.md` appears, human answers one slice at a time from EXPECTED.
- Case 3: `create-company` log in `case-3-agents-holding/create-company.log`.
