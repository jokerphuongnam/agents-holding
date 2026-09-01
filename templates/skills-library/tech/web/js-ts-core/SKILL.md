---
name: js-ts-core
description: >
  Modern TypeScript/JavaScript baseline — strict typing, modules, async safety,
  and lint hygiene. Use for shared TS/JS app code. Not Node API deep dive
  (js-ts-backend) or framework-specific UI (react/vue/angular/nextjs).
---

# js-ts-core

## Who / paths

- **You:** TypeScript/JavaScript application and shared library code.
- **Not you:** Python/Go/etc.; Nest-only structure (nestjs); React/Vue component patterns (use those skills); design token authorship.
- **Paths:** `**/*.{ts,tsx,js,jsx,mjs,cjs}`, `**/tsconfig*.json`, `**/eslint.config.*`, `**/package.json`
- **Load when:** Brief is TS/JS without a more specific framework skill owning the change.

## How

1. **Strict TypeScript.** Match repo tsconfig (prefer strict). Avoid any without a one-line reason; prefer unknown + narrowing.

2. **Honest types.** Do not cast away errors. Model unions/narrowing properly.

3. **Modules.** Clear boundaries; named exports consistent with repo. Avoid circular imports; extract shared types to leaf modules.

4. **Async.** No floating promises; handle rejections. async/await with try/catch or .catch at the edge.

5. **Immutability habit.** Prefer const; avoid mutating shared objects when project style (esp. React state) forbids it.

6. **Nullish.** Prefer ?? / ?. over loose || when 0 or empty string are valid.

7. **Equality.** Use === only; intentional truthiness only.

8. **Tooling.** Respect ESLint/Prettier/Biome; do not disable rules broadly to land a patch.

9. **Package hygiene.** No needless deps; pin ranges per policy; no secrets in client bundles.

10. **Anti-pattern — any sprawl:** silencing the typechecker instead of modeling data.

11. **Dates/IDs.** Be explicit about string vs branded IDs; do not invent conflicting ID types in one feature.

12. **Tests.** Cover pure utils and parsers you change when brief requires (Vitest/Jest/node:test).

13. **Comments.** Explain non-obvious constraints only — no narrating what the code already says.

## Done-when

- [ ] Types honest; no new unjustified any.
- [ ] No floating promises on touched code.
- [ ] Lint/format clean on touched files.
- [ ] Module boundaries clear; no new circular import knots.
- [ ] Client bundles free of secrets you introduced.
- [ ] Tests added for critical pure logic when required.

## References (external)

- https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html
- https://www.typescriptlang.org/tsconfig#strict
- https://eslint.org/docs/latest/rules/
- https://github.com/vercel-labs/agent-skills
- https://github.com/HK-hub/AgentSkills
- https://www.agentskills.io/
