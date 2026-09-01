---
name: kotlin-backend
description: >
  Kotlin HTTP backends (Ktor/Spring-style) — thin routes, validation, DI,
  structured logging, coroutines, and timeouts. Use for JVM services. Not
  Android UI (kotlin-android) or KMP mobile sharing (kotlin-kmp).
---

# kotlin-backend

## Who / paths

- **You:** Kotlin backend services — REST/gRPC handlers, application services, persistence adapters.
- **Not you:** Compose screens (kotlin-android); shared mobile KMP UI (kotlin-kmp); frontend web; cross-company API without holding-ceo.
- **Paths:** `**/src/main/kotlin/**/*.kt`, `**/resources/application*.{yml,conf,properties}`, `**/routes/**`
- **Load when:** Brief is a Kotlin JVM service/API task.

## How

1. **Thin routes.** HTTP to DTOs only; business logic in services/use-cases.

2. **Anti-pattern — fat handlers:** SQL + policy + JSON shaping in one route method.

3. **Validation at the edge.** Validate bodies/params before domain work; stable 4xx shapes.

4. **DI.** Use project DI (Koin/Hilt/Spring/Ktor install) consistently. No hidden global DB singletons.

5. **Coroutines.** Suspend services; Dispatchers.IO for blocking JDBC; cancel cooperatively; no per-request job leaks.

6. **HTTP clients.** Connect/request timeouts; retry only with idempotency rules. Never log Authorization headers.

7. **Persistence.** Transactions at service boundaries; avoid N+1 on lists; project DTOs when policy forbids leaking entities.

8. **Config.** Centralize; secrets from env/secret store — never hard-coded.

9. **Errors.** Map domain to HTTP; no stack traces to clients. Structured logs with request/correlation ids.

10. **AuthZ.** Enforce on every sensitive route; check resource ownership, not only authentication.

11. **Observability.** Metrics/health as product requires; graceful shutdown for in-flight requests.

12. **Serialization.** Explicit DTOs; unknown fields policy consistent with project.

13. **Tests.** Unit-test services; integration-test critical routes when brief requires.

## Done-when

- [ ] Routes thin; domain testable without HTTP.
- [ ] Input validated; errors shaped; no stack traces to clients.
- [ ] Outbound calls timed out; secrets not in source.
- [ ] Coroutines structured; no GlobalScope request leaks.
- [ ] AuthZ on sensitive endpoints you touched.
- [ ] Config centralized and boot-validated when pattern exists.

## References (external)

- https://ktor.io/docs/server-create-a-new-application.html
- https://docs.spring.io/spring-boot/docs/current/reference/html/
- https://kotlinlang.org/docs/coroutines-guide.html
- https://github.com/svssdeva/agentic-skills
- https://github.com/HK-hub/AgentSkills
- https://www.agentskills.io/
