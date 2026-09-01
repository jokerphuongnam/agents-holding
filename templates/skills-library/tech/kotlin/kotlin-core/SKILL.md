---
name: kotlin-core
description: >
  Idiomatic Kotlin — null safety, coroutines basics, data/sealed classes,
  visibility, and collections. Use for general Kotlin/JVM code. Not Android UI
  (kotlin-android), KMP expect/actual (kotlin-kmp), or HTTP service deep dive
  (kotlin-backend).
---

# kotlin-core

## Who / paths

- **You:** Kotlin language-level code — shared JVM libs, domain, utilities.
- **Not you:** Compose/Android resources (kotlin-android); KMP expect/actual graphs (kotlin-kmp); Ktor/Spring API layering (kotlin-backend) beyond language idioms.
- **Paths:** `**/*.kt`, `**/*.kts`, `**/build.gradle.kts`
- **Load when:** Brief is Kotlin without Android-UI or KMP-boundary focus.

## How

1. **Null safety.** Prefer non-null types; use nullable deliberately. Avoid !! unless a one-line invariant comment exists. Prefer ?. / ?: / requireNotNull.

2. **Data modeling.** data class for values; sealed class/interface for closed hierarchies; enum class for fixed sets.

3. **Immutability.** Prefer val and read-only List/Map at APIs. Expose mutable collections only when mutation is the contract.

4. **Functions.** Top-level/extension for stateless ops; default arguments over overload explosion. Avoid unnecessary singleton object bags.

5. **Visibility.** Narrowest visibility (private/internal). Public API is deliberate.

6. **Coroutines.** suspend for async APIs; structured concurrency (coroutineScope/supervisorScope).

7. **Anti-pattern — unstructured async:** GlobalScope.launch in libraries; runBlocking on hot paths or Android main thread.

8. **Exceptions.** Explicit error types or Result-like patterns when the module uses them; no empty catch.

9. **Collections.** Prefer readable list ops; use Sequence only when lazy pipelines help large data.

10. **Java interop.** Respect nullability annotations; do not leak platform types into public Kotlin APIs.

11. **Style.** Kotlin coding conventions; ktlint/Detekt if present. Named args for boolean/ambiguous parameters.

12. **Equality.** Prefer structural equality for data; document identity needs for entities.

13. **Tests.** Cover null/edge paths for changed public APIs.

## Done-when

- [ ] No unjustified !! on touched code.
- [ ] Public APIs clear nullability + narrow visibility.
- [ ] No GlobalScope/runBlocking abuse on new async APIs.
- [ ] Data/sealed types used where hierarchy clarity matters.
- [ ] Lint/format clean on touched files when tooling exists.
- [ ] Critical paths tested when brief requires tests.

## References (external)

- https://kotlinlang.org/docs/coding-conventions.html
- https://kotlinlang.org/docs/null-safety.html
- https://kotlinlang.org/docs/coroutines-guide.html
- https://kotlinlang.org/docs/data-classes.html
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
