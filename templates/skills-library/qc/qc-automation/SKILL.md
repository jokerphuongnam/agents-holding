---
name: qc-automation
description: >
  Automation harness discipline — SoT once then generate harness (do not
  hand-edit generated tests); prove real surfaces; no flaky greenwash.
---

# qc-automation

Build and maintain deterministic automated suites. Company bar: **one source of
truth** for cases/expectations → **generate** harness/fixtures; do not
hand-edit generated output as SoT.

## Who / paths

- **You:** QC automation IC / `*-qc` writing harnesses, selectors, fixtures,
  CI wiring for tests.
- **Not you:** weakening asserts to pass; implementing product features to
  “make tests green”; inventing unused facade APIs for easier mocking.
- **SoT:** case tables, AC ids, `.expected` / schema / golden files — whichever
  the company chose — then codegen or templates. Hand-edits belong in SoT, then
  regenerate.

## How

1. **SoT → generate.** Edit the canonical case/expectation once; regenerate
   harness. If you must patch generated code, treat it as a generator bug and
   fix the generator.
2. **Prove real surfaces.** Call production entry points. Reject hollow helpers
   that exist only in test trees and are unused by product/integrators.
3. **Stability.** Prefer role/label/test-id selectors or stable public APIs over
   brittle XPaths/CSS tied to layout. No fixed `sleep` without a written reason;
   prefer waits on conditions.
4. **Isolation.** Fresh fixtures per case or proven reset. Shared mutable
   globals are banned unless documented and serialized.
5. **Fail loudly.** On failure: assert message, logs, screenshots/artifacts as
   applicable. Silent catch-and-continue is a defect.
6. **CI determinism.** Same commit → same result on CI agents. Quarantine flakes
   with owner + ticket; do not ignore.
7. **Layering.** Prefer fast API/contract checks near the change; keep fewer
   end-to-end journeys for critical paths (pyramid), not inverted ice-cream.
8. **Secrets & envs.** No prod credentials in fixtures; document required env
   vars in the harness README/hop notes.
9. **Anti-patterns:** hand-maintaining 200 generated files; asserts on
   implementation private details that churn weekly; greenwash via `retry(10)`;
   testing mocks exclusively while shipping untested adapters; copying SoT into
   three formats that drift.

## Done-when

- [ ] SoT updated once; harness regenerated (no divergent hand-edits)
- [ ] Suite hits real public surfaces — no hollow/unused APIs
- [ ] Deterministic on CI; failures actionable with artifacts
- [ ] Pyramid balance justified; env/secrets documented
- [ ] No unjustified sleeps; flakes owned or fixed
- [ ] Asserts still encode AC — not diluted to pass

## References (external)

- https://martinfowler.com/articles/practical-test-pyramid.html
- https://testing.googleblog.com/
- https://www.selenium.dev/documentation/test_practices/
- https://playwright.dev/docs/best-practices
- https://www.istqb.org/
- https://martinfowler.com/bliki/TestDouble.html
