---
name: nextjs
description: >
  Next.js App Router and React Server Components — server/client boundaries,
  caching, metadata, mutations, and secret hygiene. Use for Next apps. Not
  plain CRA/Vite SPA-only (react) without Next APIs.
---

# nextjs

## Who / paths

- **You:** Next.js App Router (or Pages Router when the repo still uses it) applications.
- **Not you:** Nest backend (nestjs); Vue/Angular; inventing design system.
- **Paths:** `**/app/**`, `**/pages/**`, `**/next.config.*`, `**/middleware.ts`, `**/src/app/**`
- **Load when:** Brief is a Next.js feature, route, or RSC/client boundary change.

## How

1. **App Router for new work** when the project is on it. Default Server Components; add use client only for interactivity, browser APIs, or client hooks.

2. **Boundary clarity.** Never import server-only modules (secrets, fs, private env) into client components.

3. **Data fetching.** Fetch on the server when possible; cache deliberately. Avoid duplicate waterfalls.

4. **Mutations.** Server Actions or route handlers per standard; validate input; revalidate tags/paths after writes.

5. **Env.** NEXT_PUBLIC_* only for truly public values. Secrets stay server-only.

6. **Anti-pattern — secret leak:** shipping API keys in client bundles.

7. **Routing UI.** loading.tsx / error.tsx / not-found.tsx; never leak stack traces to users.

8. **Metadata.** Export metadata/generateMetadata for SEO-critical pages when required.

9. **Middleware.** Keep edge middleware light; auth gating without heavy business logic.

10. **Images.** next/image with known remote patterns; set sizes appropriately.

11. **React rules.** Client islands still follow react skill (effects, keys, a11y).

12. **Caching.** Be explicit about static vs dynamic; do not accidentally force dynamic on entire trees.

13. **Tests.** Route/unit tests when the repo already covers that layer.

## Done-when

- [ ] RSC vs client boundaries clear; secrets server-only.
- [ ] Mutations validate + revalidate correctly.
- [ ] Error/loading UI safe; no stack traces to clients.
- [ ] Caching choices intentional on touched fetchers.
- [ ] Client islands minimized to true interactivity needs.
- [ ] Middleware remains lean if you touched it.

## References (external)

- https://nextjs.org/docs
- https://nextjs.org/docs/app/building-your-application/rendering/server-components
- https://react.dev/reference/rsc/server-components
- https://github.com/vercel-labs/agent-skills
- https://github.com/anthropics/skills
- https://www.agentskills.io/
