---
name: objc-core
description: >
  Objective-C / Objective-C++ idioms with ARC, nullability, delegates, blocks,
  and header clarity. Use for ObjC native modules and UIKit-era code. Not
  SwiftUI-first tasks (swiftui) or pure Swift API design (swift-core).
---

# objc-core

## Who / paths

- **You:** Objective-C / Objective-C++ sources, headers, and Apple-framework integrations.
- **Not you:** Pure SwiftUI features (`swiftui`); Swift-only modules (`swift-core`); Android/Kotlin; design pixels.
- **Paths:** `**/*.{h,m,mm}`, bridging headers `**-Bridging-Header.h`
- **Load when:** Brief touches `.m`/`.mm`/ObjC headers or ObjC↔Swift bridging.

## How

1. **ARC by default.** Document MRC/`__bridge` at CF or non-ARC boundaries.

2. **Delegates weak.** Delegate/dataSource are `weak`. Strong delegates → retain cycles.

3. **Nullability.** Annotate Swift-facing headers (`nullable`/`nonnull`). Audited regions beat silent surprises.

4. **Initializers.** Clear `initWith…`; true designated initializer; chain through it.

5. **Blocks.** Weakify `self` when the block is retained by `self`; avoid cycles.

6. **Headers.** Minimal public `.h`; ivars in class extensions. No god classes; prefix category methods.

7. **Errors.** Prefer `NSError **` at Cocoa boundaries; do not ignore silently.

8. **Collections.** Do not mutate arrays/dicts you do not own; immutable copies when sharing across threads.

9. **Threading.** UIKit/AppKit on main only; document queue affinity for custom objects.

10. **ObjC++.** Keep `.mm` boundaries thin; do not leak C++ types into pure ObjC headers consumed by Swift.

11. **Naming.** Follow Cocoa naming (verbosity at call site); prefix unique symbols when in shared namespaces.

12. **Anti-pattern — silent casts:** unchecked bridging casts that hide ownership bugs.

13. **Tests.** Cover initializer failure and error paths when changing public ObjC APIs.

## Done-when

- [ ] ARC-safe; retain cycles checked on delegates/blocks.
- [ ] Nullability annotated on Swift-facing headers you touched.
- [ ] Designated initializers coherent; public headers lean.
- [ ] Errors not swallowed at Cocoa boundaries.
- [ ] UI/work queue rules respected.
- [ ] No C++ types leaked into Swift-consumed ObjC headers.

## References (external)

- https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/
- https://developer.apple.com/documentation/objectivec
- https://clang.llvm.org/docs/AutomaticReferenceCounting.html
- https://developer.apple.com/documentation/swift/imported_c_and_objective-c_apis
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
