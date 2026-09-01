---
name: ba-design-intake
description: >
  Ingest external designs/research into one canonical company brief for
  design-lead / ui-designer / ux-writer — BA owns intake, not the design system.
---

# ba-design-intake

Frontend-shaped companies: external Figma/specs/other products → **one**
canonical brief. Flow: intake (`ba`) → `design-lead` assigns `ui-designer` /
`ux-writer` → engineering consumes. English SoT.

## Who / paths

- **You:** `ba` design-intake duty. User channel remains **CEO + BA**; gather
  design links/constraints from the user or CEO, not from random ICs.
- **Not you:** owning palette/components (`ui-designer`), microcopy final
  (`ux-writer`), Assign hops (`design-lead`), or implementing UI code.
- **Paths:** brief lives under company cache (e.g. `cache/plans/…` or a short
  design-brief artifact). Keep it loadable in one spawn.

## How

1. **Ingest sources:** Figma/file links, competitor refs, research notes, brand
   rules. Cite each source; do not paste copyrighted decks verbatim.
2. **Canonical brief structure (short):**
   - Problem / jobs-to-be-done
   - Primary flows (happy path + 1–2 critical edges)
   - Glossary (terms engineers and writers must share)
   - Constraints (platforms, a11y, localization, offline, perf)
   - Non-goals
3. **Platform deltas:** call out web vs iOS vs Android differences that imply
   API or UX variance. One brief, platform notes — not three conflicting briefs.
4. **Handoff owners:** name `design-lead` as next Assign; note whether first IC
   is `ui-designer` (system) or `ux-writer` (copy-heavy). Engineering does **not**
   invent a parallel design system.
5. **Scope honesty:** if designs imply features outside current musts, list them
   as parked and escalate via wait-user / PO — do not smuggle scope.
6. **Token budget:** prefer bullets and flow ids over essays. One screen of text
   beats a novel nobody loads.
7. **A11y / i18n flags early.** If the brief implies WCAG, RTL, or multi-locale,
   say so up front so `ui-designer` / `ux-writer` / QC plan for it.
8. **Conflict resolution.** When Figma contradicts user chat, escalate via
   wait-user — do not pick a silent winner.
9. **Anti-patterns:** redesigning pixels in prose; inventing a second component
   library; skipping glossary; “match the Figma” with zero constraints; handing
   engineers raw Figma with no brief; duplicating PO AC inside the brief.

## Done-when

- [ ] Canonical brief exists and cites sources
- [ ] Flows + glossary + constraints + non-goals present
- [ ] Platform deltas noted where they change build/API/UX
- [ ] A11y / locale expectations flagged when relevant
- [ ] Next owner named (`design-lead` → IC); no second design system invented
- [ ] Scope extras parked or wait-user’d — not silently added

## References (external)

- https://kodework.com/blog/ux-designer-checklist-for-every-project/
- https://www.nngroup.com/articles/ux-research-cheat-sheet/
- https://www.interaction-design.org/literature/topics/design-briefs
- https://www.iiba.org/
- https://www.nngroup.com/articles/design-systems-101/
