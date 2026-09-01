---
name: kotlin-kmp
description: >
  Kotlin Multiplatform shared code — expect/actual discipline, shared domain,
  Gradle source sets, and platform boundaries. Use when CTO authorizes KMP.
  Not Android-UI-only (kotlin-android) or JVM backend-only (kotlin-backend).
---

# kotlin-kmp

## Who / paths

- **You:** Shared KMP modules (commonMain, platform source sets), expect/actual APIs, shared domain/data.
- **Not you:** Platform UI polish in Android/iOS apps (kotlin-android / Apple skills); pure server services with no shared mobile need; inventing KMP when CTO said platform-native only.
- **Paths:** `**/commonMain/**`, `**/androidMain/**`, `**/iosMain/**`, `**/jvmMain/**`, multiplatform `**/build.gradle.kts`
- **Load when:** CTO/brief explicitly authorizes multiplatform shared code.

## How

1. **Share what pays off.** Domain, validation, networking contracts, and pure logic in commonMain. Keep UI platform-native unless Compose Multiplatform is explicit.

2. **expect/actual sparingly.** Smallest expect surface; actuals per platform.

3. **Anti-pattern — expect everything:** prefer common interfaces injected from platforms over sprawling expect/actual.

4. **Source sets.** Platforms depend on common. Never import Android SDK types into commonMain.

5. **Coroutines and serialization.** kotlinx.coroutines + kotlinx.serialization aligned via catalog/BOM.

6. **Models.** Stable shared DTOs/domain; wrap platform-specific date/file types — do not put them in common APIs.

7. **Threading.** Document assumptions; dispatchers differ by target.

8. **Gradle.** Hierarchical source sets / KMP plugin as standard; do not break iOS framework export or Android consumption casually.

9. **Testing.** Prefer commonTest for shared logic; platform tests only for actuals.

10. **Interop.** Keep ObjC/Swift export names clean; avoid exploding public shared API.

11. **Ownership.** Platform teams own UI; shared module owners own common regressions.

12. **Versioning.** Treat common API breaks as cross-platform releases.

13. **CI.** Ensure all shipped targets compile in CI for changes you make.

## Done-when

- [ ] No Android/iOS framework types leaked into commonMain.
- [ ] expect/actual surface minimal and documented.
- [ ] Shared logic covered by common tests when changed.
- [ ] Gradle targets still resolve for shipped platforms.
- [ ] UI remains on the correct side of the boundary unless CMP in-scope.
- [ ] Public shared API changes called out in the brief/PR notes.

## References (external)

- https://kotlinlang.org/docs/multiplatform.html
- https://kotlinlang.org/docs/multiplatform-expect-actual.html
- https://kotlinlang.org/docs/multiplatform-discover-project.html
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://github.com/svssdeva/agentic-skills
- https://www.agentskills.io/
