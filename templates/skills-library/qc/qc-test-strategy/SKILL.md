---
name: qc-test-strategy
description: >
  Risk-based test strategy and case design — trace to PO AC, prove real
  surfaces, reject hollow/unused APIs; one QC owner per hop.
---

# qc-test-strategy

QC always exists. Shape adapts (central QC and/or `*-qc` in tech teams).
English SoT for strategy/cases. Adapted from ISTQB / industry risk-based
testing practice — not a syllabus dump.

## Who / paths

- **You:** `qc-lead` (Assign) and `*-qc` ICs designing strategy/cases.
- **Not you:** implementing product fixes unless the brief says; rewriting PO
  AC as informal chat; running unbounded `run_all` when a narrow suite proves
  the change (`qc-regression`).
- **Inputs:** AC in `.agents/<company>/cache/plans/`. No AC → bounce PO/BA.

## How

1. **Risk → cases.** Rank by user impact × likelihood. Cover happy, edge, and
   negative for high risks first.
2. **Traceability.** Every case maps to an AC id (or explicit exploratory charter
   with owner). Orphan cases and untested musts are both defects in process.
3. **Prove surfaces.** Tests must call the real public API / UI entry the user
   or integrator uses. **No hollow or unused APIs** — if a surface exists only
   to make a test compile, fail the review and send back to engineering.
4. **Depth mix.** Prefer stable automation for regression-critical paths;
   manual/exploratory for novelty, UX judgment, and hostile input brainstorming.
5. **Environments.** State data setup, fixtures, feature flags, and clean-up.
   Flaky shared state is a strategy bug.
6. **One job per hop.** Report owning engineer on fail; do not silently reassign
   product work to QC.
7. **Data & entitlements.** Include authz, empty, and corrupted-input cases when
   the AC claims those guarantees.
8. **Exit criteria.** Define what “tested enough” means for this hop (suite
   green, exploratory time-box, known residual risks).
9. **Anti-patterns:** testing only mocks while production path differs; green
   suites on dead code; “LGTM” without AC ids; expanding scope into product
   redesign mid-test; ignoring SoT and hand-writing divergent cases.

## Done-when

- [ ] Risks ranked; cases cover top risks (happy + edge + negative)
- [ ] Cases trace to AC ids (or named exploratory charters)
- [ ] Surfaces under test are real and used — no hollow APIs
- [ ] Automation vs manual split justified; exit criteria stated
- [ ] Failures name owning engineer / next hop

## References (external)

- https://www.istqb.org/
- https://www.ministryoftesting.com/
- https://martinfowler.com/articles/practical-test-pyramid.html
- https://testing.googleblog.com/
- https://www.satisfice.com/blog/archives/category/software-testing
- https://www.kaner.com/pdfs/QAIExploring.pdf
