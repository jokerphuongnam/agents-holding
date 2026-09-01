---
name: uikit
description: >
  UIKit app structure — view controllers, navigation, Auto Layout, safe area,
  cells, and design-token consumption. Use for UIKit screens. Not SwiftUI-first
  work (swiftui) unless migrating with an explicit brief.
---

# uikit

## Who / paths

- **You:** UIKit screens, navigation, views, and storyboards/XIBs when still in use.
- **Not you:** SwiftUI-first features (`swiftui`); pure Swift non-UI (`swift-core`); inventing brand colors (ui-designer).
- **Paths:** `**/*ViewController*.swift`, `**/*View*.swift`, `**/*.{storyboard,xib}`, `**/UI/**/*.swift`
- **Load when:** Brief delivers or fixes a UIKit screen/flow.

## How

1. **Focused VCs.** One VC ≈ one screen. Extract helpers/child VCs/view models per CTO architecture (MVC/MVVM).

2. **Anti-pattern — kitchen-sink VC:** networking + layout + persistence in one file.

3. **Navigation explicit.** Push/present/coordinator ownership clear; do not scatter pushes deep in leaf views against project patterns.

4. **Auto Layout.** Constraints/stack views/anchors over magic frames. Support rotation/Dynamic Type when product requires.

5. **Safe area.** Pin to safe area guides; respect notch/home indicator.

6. **Main thread.** All UIKit mutations on main; hop back after async before touching views.

7. **Design tokens.** Colors/typography/spacing from design system or asset catalog — no one-off hex when tokens exist.

8. **Cells.** Register/reuse; configure in dedicated methods; cancel image loads on reuse.

9. **Memory.** Weak delegates; invalidate timers/observers appropriately.

10. **Accessibility.** Labels on icon-only controls; Dynamic Type when required.

11. **Hybrid.** `UIHostingController` bridges stay thin; state ownership clear.

12. **Traits.** Adapt to size classes/dark mode via assets/traits, not hard-coded assumptions.

13. **Tests.** Snapshot/UI tests only when the project already runs them for the surface.

## Done-when

- [ ] VC responsibilities focused; navigation path clear.
- [ ] Layout safe-area aware; no fragile frame-only new UI.
- [ ] Colors/type from tokens/system when available.
- [ ] UI updates on main; delegates weak.
- [ ] Cell reuse + cancellation handled for lists you touched.
- [ ] Basic accessibility on new interactive controls.

## References (external)

- https://developer.apple.com/documentation/uikit
- https://developer.apple.com/documentation/uikit/uiview/positioning_content_relative_to_the_safe_area
- https://developer.apple.com/design/human-interface-guidelines/
- https://github.com/anthropics/skills
- https://github.com/pproenca/dot-skills
- https://www.agentskills.io/
