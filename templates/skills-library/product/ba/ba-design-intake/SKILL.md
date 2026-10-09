---
name: ba-design-intake
description: >
  ui-designer reads Figma and other design files into one design brief.
  ba-user does not do this; ba-user only clarifies the ask with the user.
---

# ba-design-intake

Frontend-shaped companies: Figma and other design files → **one** design brief
written by `ui-designer`. `design-lead` assigns `ux-writer` when copy is needed.
Engineering consumes the brief. English SoT. `ba-user` only clarifies the ask
with the user and does not read Figma.

## Who / paths

- **You:** `ui-designer`. Read Figma and write the design brief and the design system.
- **Not you:** user-channel clarification (`ba-user`), microcopy final
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
4. **Handoff owners:** `ui-designer` already owns this brief. Name `design-lead`
   as next Assign when `ux-writer` must write copy. Engineering does **not**
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
