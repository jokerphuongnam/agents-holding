---
name: po-ac-writing
description: >
  Own crisp, measurable acceptance criteria in company cache/plans — PO writes
  AC; user talks only to CEO/BA; QC traces cases to these AC.
---

# po-ac-writing

PO owns AC text and plan updates under `.agents/<company>/cache/plans/`.
English SoT. User never negotiates AC directly with PO — BA/CEO bring clarified
intent; you harden it into executable criteria.

## Who / paths

- **You:** `po-modify` (update existing plan AC) and AC sections on plans that
  `po-new` created. Cite exact plan paths.
- **Not you:** clarifying with the user in chat (CEO/BA); implementing features;
  writing the full QC suite; inventing tech stack (CTO).
- **Paths:** only under this company’s `cache/plans/`. New file → `po-new`. Edit
  AC on an existing file → `po-modify`.

## How

1. **Start from BA intent.** If must/should/could is missing or ambiguous,
   bounce to `ba-user` / wait-user — do not invent user promises.
2. **Format:** Given / When / Then **or** a numbered checklist. Each AC is
   binary-passable by QC without asking you what “better” means.
3. **Measurable:** include observables (UI state, API response, log, metric).
   Ban “fast”, “intuitive”, “secure” unless defined (p95 < X, WCAG level, …).
4. **One ownership:** every AC lives in exactly one plan file section. Link
   related plans; do not fork conflicting AC across files.
5. **Trace to QC:** label AC ids (e.g. `AC-login-01`) so `*-qc` can map cases.
   You do not write every test — you make mapping trivial.
6. **Negative + edge:** at least one failure/empty/permission case per critical
   flow when risk warrants it.
7. **Change discipline:** when modifying AC, note what changed and why (budget,
   wait-user decision, regression). Do not silently weaken AC to match a buggy
   build.
8. **Non-functional when claimed.** Perf, security, a11y — only if BA/CEO made
   them musts; then define numbers/levels QC can check.
9. **Out of scope line.** Explicit non-goals stop scope creep in review.
10. **Anti-patterns:** AC that require reading the implementer’s mind; AC only
    in chat; AC in code comments as SoT; duplicating BA prose without hardening;
    mixing must and could in one unchecked blob; AC that only pass via hollow
    test APIs.

## Done-when

- [ ] AC in `cache/plans/…` with stable ids
- [ ] Each AC measurable / binary for QC
- [ ] Happy + critical negative/edge covered where risk requires
- [ ] Non-goals and NFRs stated when they affect ship
- [ ] Plan path cited in hop; no conflicting forks
- [ ] Weakening or cuts documented with owner/decision

## References (external)

- https://www.scrum.org/resources/blog/acceptance-criteria-purpose-format-examples
- https://www.productplan.com/glossary/acceptance-criteria/
- https://www.mountaingoatsoftware.com/blog/the-differences-between-user-stories-and-use-cases
- https://www.iiba.org/
- https://www.scrum.org/resources/what-definition-done
