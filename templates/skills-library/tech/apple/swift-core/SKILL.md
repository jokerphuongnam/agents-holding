---
name: swift-core
description: >
  Swift API design and safety — clarity at call site, value vs reference,
  concurrency, Optionals, Sendable, and access control. Use for Swift modules.
  Not SwiftUI view structure (swiftui) or UIKit VC patterns (uikit).
---

# swift-core

## Who / paths

- **You:** Swift application and library code (models, services, utilities) on Apple platforms.
- **Not you:** SwiftUI layout/state deep dive (`swiftui`); UIKit VC/navigation (`uikit`); Kotlin/Android; ObjC-only (`objc-core`) unless bridging.
- **Paths:** `**/*.swift`, `**/Package.swift`, `**/*.xcodeproj/**`
- **Load when:** Brief is Swift non-UI or shared Swift logic (may still compile in app targets).

## How

1. **Clarity at call site.** Swift API Design Guidelines: argument labels read as prose; omit needless words.

2. **Value vs reference.** Prefer `struct`/`enum` for data; `class`/`actor` when identity or shared mutable state is required.

3. **Optionals.** Avoid force-unwrap/`!` except outlets or proven invariants (one-line comment). Prefer `guard let` / `if let` / `??`.

4. **Errors.** Prefer consistent `throws` / `async throws`. Do not mix silent `nil` and thrown errors for the same failure class without docs.

5. **Concurrency.** Structured concurrency (`async`/`await`, `Task`, `actor`). Avoid unstructured detached tasks without cancellation.

6. **Anti-pattern — queue soup:** new `DispatchQueue` sprawl when async APIs already exist.

7. **Sendability.** Honor `Sendable` and actor isolation under project settings; fix warnings you introduce.

8. **Access control.** Default `internal`; `public`/`open` deliberate with docs.

9. **Protocols.** Small requirements; prefer protocol + struct composition over deep class hierarchies.

10. **Naming.** UpperCamelCase types; lowerCamelCase members; boolean APIs as assertions (`isEmpty`).

11. **Collections.** Prefer values; copy-on-write awareness for large arrays at hot boundaries.

12. **Tests.** Exercise failure paths and edge Optionals for changed APIs (XCTest/Swift Testing).

13. **Docs.** Public APIs get `///` summaries when the module is a shipped interface.

## Done-when

- [ ] Call sites read clearly; argument labels intentional.
- [ ] No casual force-unwraps on new/changed code.
- [ ] Public surface and access control deliberate.
- [ ] Async/throws style consistent in the module.
- [ ] Concurrency warnings addressed on touched files.
- [ ] Tests cover critical failure paths when required.

## References (external)

- https://www.swift.org/documentation/api-design-guidelines/
- https://docs.swift.org/swift-book/documentation/the-swift-programming-language/
- https://www.swift.org/documentation/concurrency/
- https://github.com/pproenca/dot-skills
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
