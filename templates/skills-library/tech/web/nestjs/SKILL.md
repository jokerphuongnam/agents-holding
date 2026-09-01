---
name: nestjs
description: >
  NestJS modular backends — domain modules, thin controllers, DTO validation,
  providers, guards, and filters. Use for Nest services. Not generic Node
  without Nest (js-ts-backend) or frontend.
---

# nestjs

## Who / paths

- **You:** NestJS applications — modules, controllers, providers, guards, interceptors.
- **Not you:** Frontend React/Next; plain Express without Nest (js-ts-backend); cross-company API without holding-ceo.
- **Paths:** `**/*.module.ts`, `**/*.controller.ts`, `**/*.service.ts`, `**/*.dto.ts`, `**/main.ts`
- **Load when:** Brief is NestJS feature, module, or API work.

## How

1. **One module per domain.** Encapsulate controllers + providers + exports. Avoid mega-AppModule dumping grounds.

2. **Thin controllers.** HTTP mapping only; logic in injectable services.

3. **Anti-pattern — fat controllers:** ORM calls and policy inside controllers.

4. **DTO validation.** class-validator + ValidationPipe whitelist/forbid unknowns as standard. Do not trust raw body.

5. **DI tokens.** Constructor injection; custom providers when abstracting. Interfaces + tokens for swappable infra.

6. **Config.** @nestjs/config with validated env schema at boot. No scattered process.env in deep services.

7. **Errors.** Exception filters map domain to HTTP. No stack traces to clients. Typed exceptions.

8. **Auth.** Guards + decorators for roles/scopes at controller/method level.

9. **Persistence.** Repository/ORM behind providers; transactions at service boundaries when needed.

10. **Cross-cutting.** Logging interceptor; Helmet/CORS/rate-limit in main.ts as required.

11. **Async.** Prefer async services; do not block the event loop with sync CPU/FS on request path.

12. **Versioning.** Keep DTO/API changes backward compatible unless brief allows break.

13. **Tests.** Unit-test services with mocked providers; e2e for critical modules when required.

## Done-when

- [ ] Modules encapsulated; controllers thin.
- [ ] DTOs validated (whitelist); config centralized.
- [ ] Errors filtered; no stack traces to clients.
- [ ] Guards on sensitive routes you touched.
- [ ] Services unit-testable without HTTP boot when logic is non-trivial.
- [ ] No new mega-module dumping grounds.

## References (external)

- https://docs.nestjs.com/
- https://docs.nestjs.com/techniques/validation
- https://docs.nestjs.com/modules
- https://docs.nestjs.com/guards
- https://github.com/svssdeva/agentic-skills
- https://www.agentskills.io/
