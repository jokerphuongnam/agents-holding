---
name: swiftui
description: >
  SwiftUI declarative UI — small views, explicit state ownership, side effects,
  navigation, previews, and tokens. Use for SwiftUI screens. Not UIKit-only
  legacy (uikit) unless the brief is a migration bridge.
---

# swiftui

## Who / paths

- **You:** SwiftUI views, observables/view models used by those views, and previews.
- **Not you:** UIKit-first screens without migration brief (`uikit`); non-UI Swift (`swift-core`); inventing design tokens.
- **Paths:** `**/*View.swift`, `**/Views/**/*.swift`, `**/Features/**/*.swift`
- **Load when:** Brief builds or fixes SwiftUI UI.

## How

1. **Small views.** Extract subviews; composition over inheritance; avoid mega-view files.

2. **State ownership.** `@State` local; `@Binding` child writes; `@StateObject`/`@ObservedObject`/`@Observable` per Swift version. Parents own `@StateObject` creation.

3. **Anti-pattern — wrong owner:** creating `@StateObject` in a child that should receive ownership from parent.

4. **Side effects.** `.task` / `.onChange` with cancellation; no heavy work inside `body`.

5. **Lists.** Stable identities; cheap row views; avoid index-only ids when reordering.

6. **Navigation.** One NavigationStack/Path style per feature; do not mix three patterns.

7. **Design system.** Map colors/fonts to assets/theme; no one-off styling when tokens exist.

8. **Previews.** Empty/loading/error/populated when practical.

9. **Performance.** Split state to limit redraws; memo patterns only when measured.

10. **UIKit interop.** Thin `UIViewRepresentable` / `UIViewControllerRepresentable`; update in `updateUIView`.

11. **Accessibility.** Labels/traits; Dynamic Type via SwiftUI fonts.

12. **Dependencies.** Inject services into observable models; avoid singletons in every view.

13. **File organization.** Feature folders over type-only dumping grounds when the repo uses features.

## Done-when

- [ ] Views composable and focused.
- [ ] State ownership clear (create vs observe).
- [ ] Side effects not inside `body`; tasks cancellable.
- [ ] Previews cover main states for user-facing UI.
- [ ] Tokens/theme used; accessibility basics present.
- [ ] Navigation pattern consistent within the feature.

## References (external)

- https://developer.apple.com/documentation/swiftui
- https://developer.apple.com/documentation/swiftui/managing-user-interface-state
- https://developer.apple.com/tutorials/swiftui
- https://github.com/anthropics/skills
- https://github.com/pproenca/dot-skills
- https://www.agentskills.io/
