# Token bill (from session `updates.jsonl`)

Source: last cumulative `usage` object that includes `costUsdTicks` in each
subagent’s `updates.jsonl` (Grok Build session telemetry).

**Method:** take the **final** usage snapshot (not sum of every intermediate
event — those are progressive updates and would double-count).

| Case | Model | Input | Output | Reasoning | Cached read | **Total** | Model calls | API ms | costUsdTicks |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 chat-only | grok-4.6 | 282,649 | 9,875 | 3,775 | 233,344 | **292,524** | 12 | 150,076 | 466,704,400 |
| 2 naive subagents | grok-4.6 | 985,816 | 21,343 | 11,344 | 881,920 | **1,007,159** | 26 | 371,295 | 1,320,577,000 |
| 3 agents-holding | grok-4.5 | 1,169,969 | 19,309 | 17,013 | 832,768 | **1,189,278** | 29 | 349,739 | 3,536,293,760 |

### Relative to case 1

| Case | Total tokens | costUsdTicks |
| --- | ---: | ---: |
| 1 | 1.0× | 1.0× |
| 2 | **3.4×** | **2.8×** |
| 3 | **4.1×** | **7.6×** |

Notes:

- `totalTokens` = `inputTokens` + `outputTokens` in these snapshots.
- `cachedReadTokens` is reported separately (subset/related to input); do not add
  it on top of `totalTokens`.
- `costUsdTicks` is the host’s internal cost unit (not converted to USD here —
  scale unknown). Use it for **relative** cost only.
- Case 3’s cost ratio (7.6×) is higher than its token ratio (4.1×) — consistent
  with **grok-4.5-build** pricing differing from **grok-4.6-build**, plus more
  reasoning tokens.

Session ids:

- case-1 `01a05c59-ec2c-7ad2-83f4-276c2a0e5f48`
- case-2 `01a05c59-ec2c-7ad2-83f4-277e9ec47986`
- case-3 `01a05c59-ec2c-7ad2-83f4-278f29d974b2`
