---
name: design-system
description: >
  Own project design tokens and components as ui-designer — consume BA canonical
  brief; engineers consume tokens; no parallel one-off UI systems.
---

# design-system

`ui-designer` owns the company design system (color, type, space, radius, icons,
components). Align with `ba` design-intake brief. English SoT for specs;
product locale for user-facing samples.

## Who / paths

- **You:** `ui-designer` (assigned by `design-lead`). Produce tokens, component
  specs, do/don’t, states, a11y notes.
- **Not you:** Assign hops (`design-lead`); final product microcopy (`ux-writer`);
  implementing React/Swift/Kotlin UI unless brief says assets-only handoff;
  inventing product scope (`ba` / `po-*`).
- **Upstream:** canonical brief from `ba`. **Downstream:** frontend/mobile
  engineers consume tokens — they do not invent a second system.

## How

1. **Tokens first.** Color (semantic + primitive), typography scale, spacing,
   radius, elevation, motion. Name tokens for code (`color.text.primary`), not
   only hex swatches.
2. **Components second.** Document anatomy, variants, sizes, and **all states**
   (default, hover/press, focus, disabled, loading, error, empty).
3. **Do / don’t.** One concrete anti-example per tricky component beats vague
   “be consistent”.
4. **Accessibility.** Contrast targets, focus rings, hit targets, reduced
   motion. Note WCAG level expected by the brief.
5. **Governance.** Who may add a component; when to extend vs compose; version
   or changelog for breaking token renames.
6. **Platform notes.** Shared tokens with platform-specific components when
   needed — document deltas, do not pretend iOS == web.
7. **Sync with copy.** Reserve slots for labels/errors; pull strings from
   `ux-writer` / glossary — do not hardcode throwaway Lorem as SoT.
8. **Density / responsive.** Document breakpoints or size classes the product
   actually ships — not a theoretical 12-breakpoint grid unused by eng.
9. **Handoff:** token names + component inventory link in the hop so frontend/
   mobile ICs bind without reverse-engineering Figma.
10. **Anti-patterns:** one-off hex in engineer PRs while tokens exist;
    components without states; redesigning the product brief; shipping
    Figma-only with no token names engineers can bind; shadow design systems
    per feature squad.

## Done-when

- [ ] Token set named and documented for engineer consumption
- [ ] Key components have variants + states + a11y notes
- [ ] Do/don’t and governance for additions present
- [ ] Responsive/density rules match real platforms
- [ ] Aligned with BA brief glossary/constraints
- [ ] No encouragement of a parallel ad-hoc UI kit

## References (external)

- https://designsystemschecklist.com/
- https://www.designsystems.com/
- https://musemind.agency/blog/how-to-build-a-ui-design-system-for-your-website
- https://www.nngroup.com/articles/design-systems-101/
- https://www.w3.org/WAI/WCAG22/quickref/
- https://m3.material.io/foundations/design-tokens/overview
