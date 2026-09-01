---
name: design-critique
description: >
  Structured design-lead review — score clarity, consistency, a11y, content,
  feasibility; one Assign per hop to ui-designer or ux-writer for fixes.
---

# design-critique

`design-lead` quality bar for UX/UI. Short scored review artifacts. Inspired by
structured critique practice and Anthropic-style frontend design attention to
hierarchy, clarity, and craft — without pasting copyrighted rubrics verbatim.

## Who / paths

- **You:** `design-lead` reviews / Assign. One design IC per hop
  (`ui-designer` or `ux-writer`).
- **Not you:** coding product UI; rewriting BA scope; inventing engineering APIs;
  multi-IC parallel design without need.
- **Upstream:** BA canonical brief. **Downstream:** fix Assign to the matching
  IC; escalate stack to CTO when feasibility is architectural.

## How

1. **Rubric dimensions (score or RAG each):**
   - Clarity of hierarchy / primary action
   - Consistency with design system tokens/components
   - Accessibility (contrast, focus, targets, semantics)
   - Content quality (tone, errors, empty — with `ux-writer` if needed)
   - Feasibility (platform constraints, eng cost flags)
   - Brand / brief fit
2. **Severity:** blocker / major / minor. Blockers stop ship; minors batch.
3. **Evidence:** cite screen/flow id + brief section. “Looks off” is not a finding.
4. **One Assign per hop.** Pick `ui-designer` (visual/system) **or** `ux-writer`
   (copy). Do not spray both unless the brief splits work across hops.
5. **Keep the artifact short.** Table + top findings; token-cheap for the next
   spawn. Link Figma/frames; do not paste huge screenshots as prose.
6. **Respect intake.** If the brief is wrong, bounce to `ba` — do not “fix”
   product scope inside a visual critique.
7. **Craft bar.** Hierarchy, spacing rhythm, contrast, and motion should feel
   intentional — flag “template default” UI that ignores the system.
8. **Follow-up.** Re-review only blockers/majors unless minors were in-scope
   for the hop; avoid infinite polish loops.
9. **Anti-patterns:** taste-only nitpicks without severity; inventing a second
   design system in review comments; assigning engineering to “make it pretty”
   with no IC; rubber-stamp LGTM with unchecked a11y; debating stack in a
   visual review.

## Done-when

- [ ] Rubric scored (or RAG) across dimensions above
- [ ] Findings prioritized by severity with evidence
- [ ] Single IC owner assigned for the hop (or BA/CTO bounce named)
- [ ] Re-review scope limited to agreed severities
- [ ] Review artifact short enough for one spawn load
- [ ] No silent scope or API invention

## References (external)

- https://www.nngroup.com/articles/design-reviews/
- https://uxcel.com/blog/product-designer-skills
- https://www.interaction-design.org/literature/topics/design-critique
- https://www.anthropic.com/engineering/frontend-design
- https://www.w3.org/WAI/test-evaluate/
- https://www.nngroup.com/articles/aesthetic-usability-effect/
