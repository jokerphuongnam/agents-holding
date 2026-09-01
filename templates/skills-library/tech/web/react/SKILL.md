---
name: react
description: >
  React components and hooks — state placement, effects cleanup, list keys,
  a11y, and design-system consumption. Use for React UI. Not Vue/Angular; not
  Redux deep dive (redux) or Next.js RSC routing (nextjs).
---

# react

## Who / paths

- **You:** React UI components, hooks, and client-side view logic.
- **Not you:** Vue/Angular; Nest APIs; inventing brand pixels (ui-designer); owning UX microcopy (ux-writer) — consume their outputs.
- **Paths:** `**/*.{tsx,jsx}`, `**/components/**`, `**/hooks/**`, `**/features/**`
- **Load when:** Brief builds or fixes React UI (SPA or client islands).

## How

1. **Functional components.** Function components + hooks. Extract reusable logic into hooks; keep render focused.

2. **State placement.** Local UI state nearest the consumer. Prefer TanStack Query/SWR (or project equivalent) for remote cache over fetch+useEffect reinvention. Redux only for complex client workflows (redux).

3. **Effects.** Subscriptions/timers/requests clean up. Correct deps; do not casually disable react-hooks/exhaustive-deps.

4. **Lists.** Stable key (ids — not index when order changes).

5. **Derived state.** Compute during render when cheap; avoid mirroring props into state unless syncing is intentional.

6. **Performance.** Memoize only for measured cost or stable deps children need — not by default everywhere.

7. **Accessibility.** Real buttons/links; label inputs; keyboard operable controls.

8. **Design system.** Shared components/tokens. No one-off colors/spacing when tokens exist.

9. **Errors.** Error boundaries where project standard requires; user-safe messages.

10. **Composition.** Prefer children/slots over boolean prop pyramids.

11. **Anti-pattern — effect spaghetti:** syncing lots of state in cascading effects instead of deriving or using a query lib.

12. **Controlled inputs.** Prefer one source of truth; do not fight controlled/uncontrolled hybrids.

13. **Tests.** Component/hook tests when the repo already tests that layer and brief requires.

## Done-when

- [ ] Components focused; hooks extract shared behavior.
- [ ] Effects cleaned up; deps honest.
- [ ] List keys stable; remote cache not reinvented without reason.
- [ ] Design tokens/components used when available.
- [ ] Basic a11y for interactive controls you added.
- [ ] No new unjustified prop-boolean pyramids.

## References (external)

- https://react.dev/learn
- https://react.dev/reference/react/hooks
- https://github.com/vercel-labs/agent-skills
- https://github.com/anthropics/skills
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
