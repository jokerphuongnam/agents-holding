---
name: po-plan-slicing
description: >
  Slice delivery into shippable vertical plans under cache/plans without silent
  scope cuts; po-new creates one new plan file per hop.
---

# po-plan-slicing

Turn clarified BA intent into executable plan slices. English SoT under
`.agents/<company>/cache/plans/`. User channel stays CEO/BA — you plan, you do
not renegotiate with the user in chat.

## Who / paths

- **You:** `po-new` especially (one **new** plan file per hop); `po-modify` when
  re-slicing AC inside an existing plan.
- **Not you:** inventing tech stack (CTO); implementing; design system; talking
  to the user as if you were BA.
- **Paths:** `cache/plans/<area>/…-plan.md` (company-local). Multi-company asks
  → flag holding; do not invent sister-company plans alone.

## How

1. **Vertical slices over horizontal layers.** Prefer “thin end-to-end user
   outcome” over “all DB then all API then all UI”. Each slice should be
   demoable or QC-able alone.
2. **One new file per `po-new` hop.** Do not sprinkle five half-plans in one
   hop. Name files so graphs/hop can cite them.
3. **Dependencies explicit.** Upstream plans, shared modules, feature flags,
   migrations. Blocked-by / blocks tables beat buried prose.
4. **Scope preservation.** Slicing ≠ cutting. If a must cannot fit the slice,
   park it in a follow-on plan id — never drop it quietly.
5. **AC hooks.** Every slice lists AC ids (or “AC TBD → po-modify”) so QC can
   attach. Empty “build the module” plans fail the bar.
6. **Budget / tier.** If holding seeded a budget, note effort assumptions and
   what falls out when over budget — with wait-user when musts conflict.
7. **Holding / multi-company.** Cross-subsidiary work: flag for holding CEO;
   do not assign other companies’ ICs from this plan.
8. **QC & design hooks.** Note whether slice needs `design-lead` before eng,
   and which `*-qc` shape proves it — avoid “build then invent tests”.
9. **Rollback / feature-flag notes** when a slice ships dark or partial.
10. **Anti-patterns:** horizontal-only waterfalls; mega-plans that never ship;
    silent must drops; tech spikes disguised as product scope without CTO;
    duplicating the same AC across three files with drift; plans with no demo
    or QC story.

## Done-when

- [ ] Slice is shippable or QC-provable on its own
- [ ] Deps / blockers listed; holding flagged when needed
- [ ] Musts preserved or explicitly parked with ids
- [ ] Plan path exists under `cache/plans/`; AC hooks present
- [ ] Design/QC hooks noted when relevant
- [ ] One new file ownership clear for `po-new` hops

## References (external)

- https://www.productplan.com/glossary/user-story-mapping/
- https://www.jpattonassociates.com/user-story-mapping/
- https://martinfowler.com/bliki/UserStory.html
- https://www.scrum.org/resources/blog/slicing-user-stories
- https://www.productplan.com/learn/how-to-prioritize-features/
