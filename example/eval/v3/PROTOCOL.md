# Bench protocol v3 — 2 arms + history

## History (prior runs — keep for comparison)

See `history/`:

| File | What |
| --- | --- |
| `INPUT-v1.md` / `EXPECTED-v1.md` | Prior shared input + acceptance |
| `RESULTS-v1.md` / `TOKENS-v1.md` | Prior 3-arm scores + token bills |
| `SETTINGS-v1.md` / `PROTOCOL-v1.md` | Prior settings |
| `RUBRIC.md` | Scoring dimensions D1–D8 (/40) |

Prior takeaway (do not erase): chat-only cheap but failed test bar; naive nested LLM very expensive; agents-holding optimized ~470k tokens @ 40/40.

## Arms (this run)

| Case | Worktree | How | Model (requested) |
| --- | --- | --- | --- |
| **A** | `case-a-plain` | Normal vibe chat — **no** Company OS / holding | grok-4.6 medium |
| **B** | `case-b-company-os` | **Plugin** = agents-holding: `create-company` → `company_os.sh all` → ceo/product cascade | grok-4.6 (or 4.5) low |

Same `INPUT.md` text only on first message.

## Order

1. Lock `INPUT.md`, `OUTPUT.md`, this file, `SETTINGS.md`.
2. Reset two worktrees (clean product trees).
3. **Case B only:** install holding → create-company (`react`+`express` or nest, budget low) → `company_os.sh all`.
4. Run A and B (can parallelize) with identical INPUT.
5. Mid-flight human: one missing OUTPUT slice at a time if asked / if thin.
6. Stop on agent “done” or wall-clock/budget cap.
7. Score vs `OUTPUT.md` + `history/RUBRIC.md`. Record **wall time**, **tokens** (session usage), **score /40**, **gap** vs the other arm and vs `history/RESULTS-v1.md`.

## Honesty

- No fabricated tokens/scores.
- Do not inject `OUTPUT.md` into the first message.
- Case B must use real `.agents/<slug>-company/`.
- Include prior history in the final RESULTS table for trend context.
