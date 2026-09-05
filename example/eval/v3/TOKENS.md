# Token bill v3 — from session `updates.jsonl` (`turn_completed.usage`)

| Case | Session | Input | Output | Reasoning | Cached read | Turns | **Total** |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A plain | `01a06fa6-…7512a3` | 646,438 | 11,528 | 9,871 | 591,744 | 30 | **657,966** |
| B company-os | `01a06fa6-…f47d23` | 470,423 | 8,426 | 4,370 | 403,328 | 18 | **478,849** |

| Compare | Value |
| --- | ---: |
| B / A total | **0.73×** (~27% fewer tokens on B) |
| A − B | **179,117** tokens saved on Company OS arm |

Wall clock (subagent duration_ms): A **244.3s**, B **159.1s** (B ≈ **0.65×** A).

Nested LLM subagents: **0** on both arms (single general-purpose worker each; Case B followed Company OS cascade conceptually inside one session).
