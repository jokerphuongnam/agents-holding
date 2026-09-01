---
name: js-ts-backend
description: >
  Node.js TypeScript service patterns — layered routes/services, validation,
  timeouts, structured logs, and graceful shutdown. Use for Node APIs. For
  NestJS modular standards prefer nestjs skill.
---

# js-ts-backend

## Who / paths

- **You:** Node.js/TypeScript HTTP workers and APIs (Express/Fastify/Hono/custom).
- **Not you:** Nest deep modules/guards (nestjs); browser React (react); cross-company API without holding-ceo.
- **Paths:** `**/src/**/*.{ts,js}`, `**/server/**`, `**/routes/**`, `**/apps/*-api/**`
- **Load when:** Brief is a Node service without Nest-specific module work.

## How

1. **Layering.** Routes parse HTTP; services own rules; data access isolated.

2. **Anti-pattern — fat routes:** DB queries and policy inside route handlers.

3. **Validation.** Schema-validate bodies/query (Zod/Joi/etc.) before work; stable 4xx.

4. **Timeouts.** On outbound fetch/HTTP and DB pool acquires — no unlimited hangs.

5. **Errors.** Central middleware; never leak stack traces/secrets to clients. Log full error server-side with request ids.

6. **Logging.** Structured JSON when standard; never log passwords/tokens/raw card data.

7. **Config.** Read env once at boot; fail fast on missing required secrets.

8. **Security basics.** Helmet/CORS/rate-limit as required; parameterized queries only; sanitize redirects.

9. **Async safety.** Await all async paths; define unhandledRejection strategy per project. Avoid sync FS on request path.

10. **Shutdown.** SIGTERM then stop accepting then drain with deadline.

11. **AuthZ.** Check on sensitive routes; verify resource ownership.

12. **Health.** Keep liveness/readiness accurate when you touch infra hooks.

13. **Tests.** Integration tests for critical routes when brief requires; mock outbound I/O.

## Done-when

- [ ] Validation present on mutated endpoints.
- [ ] Outbound I/O has timeouts; errors normalized.
- [ ] Logs structured and secret-free.
- [ ] Graceful shutdown hooks for long-running servers you touch.
- [ ] Layering preserved (thin routes).
- [ ] AuthZ enforced on sensitive changes.

## References (external)

- https://nodejs.org/en/learn
- https://nodejs.org/api/http.html
- https://github.com/vercel-labs/agent-skills
- https://github.com/HK-hub/AgentSkills
- https://github.com/svssdeva/agentic-skills
- https://www.agentskills.io/
