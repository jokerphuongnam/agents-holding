---
name: csharp-backend
description: >
  ASP.NET Core API / service patterns — thin controllers, DTOs, DI, options,
  logging, authZ, EF hygiene, and error shaping. Use for C# HTTP backends.
  Not Unity (csharp-unity); not pure class-lib work (csharp-core).
---

# csharp-backend

## Who / paths

- **You:** ASP.NET Core Web APIs, minimal APIs, and hosted HTTP/gRPC workers.
- **Not you:** Unity clients (`csharp-unity`); pure class libs without host (`csharp-core`); frontend; cross-company APIs without holding-ceo.
- **Paths:** `**/Controllers/**/*.cs`, `**/Endpoints/**/*.cs`, `**/Program.cs`, `**/appsettings*.json`, `**/*Dto*.cs`, `**/Middleware/**/*.cs`
- **Load when:** Brief is a C# service/API feature, bugfix, or hardening task.

## How

1. **Thin HTTP edge.** Controllers/minimal APIs map HTTP ↔ DTOs; business rules live in services/use-cases.

2. **Anti-pattern — fat controllers:** EF queries, policy, and side effects all inside the action.

3. **DTOs at the edge.** Do not leak EF entities as JSON contracts unless explicitly accepted. Validate with DataAnnotations or FluentValidation.

4. **DI first.** Constructor injection from the composition root. Do not `new` DbContext/HttpClient in handlers; avoid service locator in domain code.

5. **Options pattern.** `IOptions<T>` / `IOptionsMonitor<T>`; centralize config — no scattered env reads.

6. **HttpClient.** `IHttpClientFactory` + timeouts; never unbounded `new HttpClient()` per request.

7. **Errors.** Problem details / stable envelopes. Never return stack traces or secret-bearing messages to clients.

8. **Logging.** Structured logs + correlation ids. Never log tokens, passwords, or full PII payloads.

9. **AuthZ.** Authorize endpoints; check tenant/user ownership (IDOR). Hidden URLs are not security.

10. **EF / data.** Scoped DbContext; explicit projections for lists; avoid lazy-load serialization surprises and N+1.

11. **Retries.** Only on idempotent ops; pass cancellation tokens on outbound calls.

12. **Shutdown.** Graceful drain for background services when product requires it.

13. **Health.** Expose readiness/liveness as the host already does; do not break probes casually.

## Done-when

- [ ] Input validated; 4xx stable shape on bad requests.
- [ ] Handlers thin; logic in testable services.
- [ ] Config via options; no hard-coded secrets.
- [ ] Errors normalized; no stack traces to clients.
- [ ] Outbound HTTP timed out; DI graph clear.
- [ ] Sensitive routes enforce authZ + ownership.

## References (external)

- https://learn.microsoft.com/aspnet/core/fundamentals/
- https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis
- https://learn.microsoft.com/dotnet/core/extensions/options
- https://learn.microsoft.com/aspnet/core/fundamentals/http-requests
- https://learn.microsoft.com/aspnet/core/security/authorization/introduction
- https://github.com/microsoft/skills
