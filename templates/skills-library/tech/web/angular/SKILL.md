---
name: angular
description: >
  Angular apps — standalone components, RxJS subscription safety, typed HTTP,
  signals (when used), and smart/presentational split. Use for Angular. Not
  React/Vue.
---

# angular

## Who / paths

- **You:** Angular components, services, routes, and templates.
- **Not you:** React/Vue; backend Nest unless brief spans both; design token authorship.
- **Paths:** `**/*.{ts,html,scss}`, `**/app/**`, `**/angular.json`, `**/projects/**`
- **Load when:** Brief builds or fixes Angular UI/app logic.

## How

1. **Current style.** Follow the project's Angular major. Prefer standalone components when the app already uses them; do not reintroduce NgModules into a standalone app without reason.

2. **Templates lean.** Logic in TypeScript; prefer async pipe over manual subscribe when practical.

3. **RxJS leaks.** takeUntilDestroyed, AsyncPipe, or DestroyRef teardown.

4. **Anti-pattern — bare subscribe:** .subscribe() with no teardown in components.

5. **Smart vs presentational.** Containers orchestrate; presentational take inputs/outputs (or signal inputs).

6. **HTTP.** HttpClient + typed models; auth/error in interceptors; handle errors explicitly.

7. **Change detection.** OnPush for presentational when that is app standard; do not mutate inputs in place.

8. **Signals (Angular 16+ when used).** Prefer consistent signals/computed in new code over mixing three state styles in one feature.

9. **DI.** Constructor inject / inject() per style; providedIn root for true singletons only.

10. **Forms.** Reactive forms for non-trivial validation; typed controls when available.

11. **Design system.** Shared Angular UI library/tokens over one-off styles.

12. **Routing.** Lazy-load feature routes when the app already does; keep guards focused.

13. **Tests.** Component/service tests with TestBed patterns the repo uses when required.

## Done-when

- [ ] No subscription leaks on touched components.
- [ ] HTTP typed; errors handled via project patterns.
- [ ] Templates lean; CD strategy respected (OnPush if standard).
- [ ] Standalone/module style matches the app.
- [ ] Tokens/shared UI used when available.
- [ ] Guards/interceptors unchanged in behavior unless brief requires.

## References (external)

- https://angular.dev/style-guide
- https://angular.dev/guide/components
- https://angular.dev/guide/http
- https://angular.dev/guide/signals
- https://github.com/pproenca/dot-skills
- https://www.agentskills.io/
