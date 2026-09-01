# Token / cost proxies (real session signals)

**Billed total tokens (input+output across the run): not available** from the Grok host for these subagent sessions. No `input_tokens` / `output_tokens` / `total_tokens` fields were found in session JSON.

What **is** recorded in each case’s `signals.json` (host telemetry):

| Metric | Meaning |
| --- | --- |
| `contextTokensUsed` | Tokens in the context window at session end (not cumulative spend) |
| `contextWindowUsage` | Percent of 500k window |
| `toolCallCount` | Tool invocations |
| `sessionDurationSeconds` | Wall time |
| `assistantMessageCount` / `num_messages` | Message volume |
| `totalChunkCount` | Stream chunks (output-ish proxy) |
| `reasoning_effort` | Actual effort flag on the session (`summary.json`) |

## Comparison

| Case | Model | Requested effort | Actual `reasoning_effort` | Context used | Window % | Tools | Duration | Asst msgs | Chunks |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 chat-only | grok-4.6 | medium/full | **high** | **33,124** | 6% | **32** | **173s** | 12 | 321 |
| 2 naive subagents | grok-4.6 | medium/full | **high** | **55,179** | 11% | **71** | **394s** | 26 | 569 |
| 3 agents-holding | grok-4.5 | low | **high** | **61,017** | 12% | **96** | **497s** | 29 | 507 |

Sources (on the bench machine):

- `~/.grok/sessions/.../case-1-chat-only/01a05c59-ec2c-7ad2-83f4-276c2a0e5f48/signals.json`
- `.../case-2-naive-subagents/01a05c59-ec2c-7ad2-83f4-277e9ec47986/signals.json`
- `.../case-3-agents-holding/01a05c59-ec2c-7ad2-83f4-278f29d974b2/signals.json`

## How to read this

- **Leanest run:** case 1 (fewest tools / shortest / smallest context) but **failed** the EXPECTED test bar.
- **Case 2 vs 1:** ~2.3× duration, ~2.2× tools, ~1.7× context — paid for tests + naive fan-out thrash.
- **Case 3:** highest context/tools/duration among the three, but **highest quality score (39/40)** and fullest tests; note requested **low** effort yet session recorded `reasoning_effort: high` (host override / default).

Until the runtime exports cumulative billed tokens, use this table for comparison — do not invent dollar costs.
