---
name: qc-regression
description: >
  Select the narrowest regression suite that proves the change; document skips;
  expand only when shared modules are touched; coordinate multi-company via holding.
---

# qc-regression

After a change, prove you did not break what mattered — with minimum justified
runtime. Ties to `qc-test-strategy` (what exists) and `qc-automation` (how it
runs). English SoT for selection notes.

## Who / paths

- **You:** QC planning/selecting regression for a hop or release gate.
- **Not you:** defaulting to full `run_all` / entire pyramid without need;
  implementing product fixes; skipping must AC silently.
- **Inputs:** diff/touched modules, AC ids in `cache/plans/`, prior suite map,
  CI budget.

## How

1. **Narrowest proving suite.** Map changed files/modules → dependent suites.
   Run that set first. Broaden only on shared kernels, public API breaks, or
   failed smoke.
2. **Always include:** smoke on the primary user/integrator path for the area,
   plus AC-linked cases for touched musts.
3. **Record skips.** What you did **not** run and why (untouched, covered by X,
   known quarantine). Unrecorded skips are process failures.
4. **Shared modules.** If Foundation/runtime/design-tokens/core libs move,
   expand to downstream consumers — say so explicitly.
5. **Hollow check.** If regression “passes” via unused or test-only APIs, it
   does not prove the change — fail and demand real surfaces.
6. **Multi-company.** Cross-subsidiary regressions coordinate via holding; do
   not unilaterally schedule sister companies.
7. **Fail → triage.** On red: isolate owning team, file/hop with repro, do not
   widen the suite as a substitute for a fix.
8. **Release gates.** Distinguish hop-local regression vs release candidate
   pack; document which gate this run satisfies.
9. **Anti-patterns:** ritual full-grid every typo fix; skipping flaky suites
   forever without owners; green on stubs; hiding skip lists in chat only;
   regenerating expectations by hand instead of SoT → harness.

## Done-when

- [ ] Selected suite justified against the diff
- [ ] Must AC for touched area covered or explicitly deferred with owner
- [ ] Skips documented with rationale
- [ ] Expansion triggered when shared modules touched
- [ ] Gate level (hop vs release) stated
- [ ] Results cite real surfaces; holding notified if multi-company

## References (external)

- https://martinfowler.com/bliki/TestPyramid.html
- https://martinfowler.com/articles/practical-test-pyramid.html
- https://testing.googleblog.com/
- https://www.istqb.org/
- https://www.ministryoftesting.com/
- https://martinfowler.com/bliki/ContinuousIntegration.html
