---
name: kotlin-android
description: >
  Android Kotlin apps — Activity/Fragment or Compose UI, ViewModel, lifecycle,
  resources, and Material theming. Use for Android client work. Not JVM-only
  backend (kotlin-backend) or KMP shared expect/actual (kotlin-kmp).
---

# kotlin-android

## Who / paths

- **You:** Android application modules — UI, ViewModels, navigation, resources.
- **Not you:** Pure backend Ktor/Spring (kotlin-backend); KMP shared module wiring (kotlin-kmp) beyond consuming shared code; inventing brand tokens.
- **Paths:** `**/src/main/{java,kotlin}/**/*.kt`, `**/res/**`, `**/composeApp/**`, `**/AndroidManifest.xml`
- **Load when:** Brief delivers Android UI or Android app logic.

## How

1. **UI toolkit.** Follow project choice: Compose (preferred for new UI) or Views — do not invent a third pattern mid-feature.

2. **Compose rules.** Pass Modifier; keep composables pure; hoist state; stable keys in LazyColumn. Prefer Material 3 semantic colors/type over one-off hex/sp.

3. **Lifecycle.** UI state in ViewModel; collect Flows lifecycle-aware (collectAsStateWithLifecycle / repeatOnLifecycle).

4. **Anti-pattern — leaks:** coroutines tied to destroyed views; holding Context/View in ViewModels.

5. **Navigation.** Single nav graph ownership per feature; typed routes/args when available.

6. **Resources.** User-facing strings in strings.xml (or project i18n) — not hard-coded in Kotlin when resources exist.

7. **Threading.** Main for UI only; coroutines + proper dispatchers for IO. Never runBlocking on main.

8. **Permissions and security.** Request at point of use; secrets in encrypted storage/Keystore patterns the app uses — not plaintext prefs.

9. **DI.** Hilt/Koin as project standard; avoid service locators in composables.

10. **Previews/tests.** Compose previews for key states; unit-test ViewModels for critical logic.

11. **Performance.** Avoid unstable lambdas/lists causing needless recomposition; baseline profiles only when brief asks.

12. **Configuration changes.** State survives via ViewModel (or documented exception).

13. **Manifest.** Permissions/exported components explicit and minimal.

## Done-when

- [ ] State survives config changes via ViewModel (or documented exception).
- [ ] No Context leaks; coroutines lifecycle-aware.
- [ ] UI uses theme/tokens; user strings externalized when resources exist.
- [ ] Navigation/args consistent with project.
- [ ] Main-thread rules respected; touched modules build.
- [ ] Material3/theme used for new Compose UI when project is on M3.

## References (external)

- https://developer.android.com/kotlin/style-guide
- https://developer.android.com/jetpack/compose/mental-model
- https://developer.android.com/topic/architecture
- https://developer.android.com/develop/ui/compose/designsystems/material3
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
