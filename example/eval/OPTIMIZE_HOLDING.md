# Why case 3 (agents-holding) cost more — and how to cut it

## Why it was expensive (this bench)

From HISTORY + bill:

1. **Explored Company OS before coding** — hop, ORG, customs skills, plans,
   task cache — large **input** (1.17M) even with cache reads.
2. **Heavier stack** — NestJS + SQLite + e2e + more FE tests vs Express MVP in
   case 1 (quality up, tokens up).
3. **More model calls** — 29 vs 12 (case 1).
4. **More reasoning tokens** — 17k vs 3.8k.
5. **Requested effort `low` but session `reasoning_effort: high`** — host did
   not honor low; bills like a high-effort run.
6. **Model price** — grok-4.5-build `costUsdTicks` grew faster than raw tokens
   vs grok-4.6-build.

Case 3 still scored best on EXPECTED (39/40). The issue is **efficiency**, not
correctness.

## Optimizations (product + library)

### A. Agent behavior (biggest win)

0. **`task_cache.py show` first every turn** — same goal → resume cached role; never re-analyze hop/ORG/skills. This was the intended fix for repeated analysis.

1. **CEO brief must be path-narrow:** Assign one IC with Exact paths
   (`apps/api/**`, `apps/web/**`). Forbid “read all of ORG / all skills”.
2. **Hop Unique Path only** — already the design; enforce in `holding-ceo` /
   subsidiary `ceo`: one hop resolution, then stop browsing staffs.
3. **Load at most one customs `SKILL.md`** per IC (nestjs **or** react), not the
   whole customs tree.
4. **Budget `low` ⇒ lighter default stack** in create-company / HR brief:
   prefer Express+Vite template over full Nest monorepo unless user asks Nest.
5. **Tests policy by budget:** `low` = minimal API unit + one RTL smoke; defer
   e2e until `medium`/`high` or user asks.
6. **Honor effort** — if user/HR sets low, runtime/session must actually use
   low reasoning (fix separately if host ignores it).

### B. Library / factory

1. **Starter app templates** under `templates/starters/{express-react,nestjs-react}`
   so agents **edit** instead of scaffolding Nest from zero.
2. **Slimmer hop bootstrap** in new companies (fewer scripts copied into context
   paths agents casually open).
3. **COMPANY_BOOT one-pager** for product tasks: 15 lines, link deep docs only
   on demand.
4. **create-company chat path:** HR confirm/lock should emit a single shell
   block; CEO should not narrate the whole holding ORG.

### C. Bench / measurement

1. Always export final `usage` snapshot into `example/eval/case-*/usage.json`
   after runs (scripted).
2. Compare **billable** `inputTokens`/`outputTokens`/`costUsdTicks`, not only
   end-of-session `contextTokensUsed`.

## Target (next bench)

Same INPUT + EXPECTED pass bar, case 3 **totalTokens ≤ ~1.5× case 1** while
still passing E0–E4 — via starter template + narrow hop + low-effort actually
applied + no e2e on low unless asked.
