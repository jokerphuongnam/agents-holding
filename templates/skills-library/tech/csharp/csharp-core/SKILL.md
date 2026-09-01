---
name: csharp-core
description: >
  Idiomatic C# / .NET coding conventions, nullability, async, collections,
  disposal, and API safety. Use for general C# application and library code.
  Not Unity gameplay (csharp-unity) or ASP.NET-only deep patterns (csharp-backend).
---

# csharp-core

## Who / paths

- **You:** C# / .NET libraries, workers, and shared domain code for this company.
- **Not you:** Unity MonoBehaviour hot paths (`csharp-unity`); ASP.NET controller/DI deep dive (`csharp-backend`); other languages; design pixels.
- **Paths:** `**/*.{cs,csproj,props,targets}`, `**/Directory.Build.*`, `**/global.json`
- **Load when:** Brief names C#/.NET library or app work without Unity or ASP.NET-specific scope.

## How

1. **Nullable on.** Treat nullable warnings as defects on touched code. Prefer `string?` + checks over `!` unless a one-line invariant comment exists.

2. **Naming.** PascalCase types/methods/properties; camelCase locals/params; `I`-prefixed interfaces; async methods end with `Async`. Honor `.editorconfig`.

3. **Async end-to-end.** `async`/`await` on I/O; pass `CancellationToken` on public async APIs that can cancel.

4. **Anti-pattern — sync-over-async:** `.Result` / `.Wait()` / `GetAwaiter().GetResult()` on request or UI threads. Prefer `ConfigureAwait(false)` in library code.

5. **Immutability.** Prefer `record` / init-only DTOs. Avoid mutable static shared state; if required, document lock/ownership.

6. **Collections.** Expose `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>` when callers must not mutate. Do not leak internal `List<T>` as settable properties.

7. **Exceptions.** Specific types + useful messages at boundaries. No empty `catch`. No exceptions for ordinary control flow.

8. **Dispose.** `IAsyncDisposable` for async resources; `using` / `await using`. No finalizer-only cleanup for managed resources.

9. **LINQ.** Clarity over cleverness; materialize when enumerating twice. Avoid LINQ in proven hot loops.

10. **API surface.** `public` only when needed. Expression-bodied members for trivial one-liners only.

11. **Span (when justified).** `Span<T>` / `ReadOnlySpan<T>` for hot parsing without alloc — only if project already uses them or profiling demands it.

12. **Tests.** Cover null/edge paths for changed public APIs (xUnit/NUnit/MSTest). Name tests by behavior.

13. **Logging interfaces.** Do not log secrets in shared helpers; accept `ILogger` rather than static loggers when DI is available.

## Done-when

- [ ] Nullable enabled; no new ignored nullable warnings without reason.
- [ ] No blocking waits on async hot paths; cancellation plumbed where tokens already exist.
- [ ] Public APIs clear on nullability and disposal ownership.
- [ ] Naming + `Async` suffixes match conventions.
- [ ] Boundary validation tested when the brief requires tests.
- [ ] No new unsynchronized mutable static state.

## References (external)

- https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions
- https://learn.microsoft.com/dotnet/csharp/nullable-references
- https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/async-scenarios
- https://learn.microsoft.com/dotnet/standard/garbage-collection/implementing-dispose
- https://github.com/microsoft/skills
- https://www.agentskills.io/
