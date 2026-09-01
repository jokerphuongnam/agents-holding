---
name: vue
description: >
  Vue 3 Composition API and SFCs — script setup, typed props/emits, composables,
  lifecycle cleanup, and token alignment. Use for Vue apps. Not React/Angular.
---

# vue

## Who / paths

- **You:** Vue single-file components, composables, and Vue Router views.
- **Not you:** React/Angular; inventing design tokens; Nest backend.
- **Paths:** `**/*.vue`, `**/composables/**`, `**/components/**`, `**/pages/**`, `**/router/**`
- **Load when:** Brief builds or fixes Vue UI.

## How

1. **Composition API + script setup** for new code unless mid Options API migration.

2. **Small SFCs.** Extract subcomponents and useX composables. Avoid 1k-line SFCs with unrelated concerns.

3. **Props and emits.** Type props; declare emits; never mutate props — emit upward.

4. **v-model.** Standard modelValue / update:modelValue (or named v-models) consistently.

5. **Reactivity.** ref/reactive deliberately; use toRefs/storeToRefs when destructuring.

6. **Watchers vs computed.** computed for derived values; watchers for side effects only.

7. **Lifecycle.** Clean listeners/timers in onBeforeUnmount; cancel in-flight requests.

8. **Lists.** Stable :key on v-for (ids, not index when reordering).

9. **State.** Local first; Pinia for shared client state. Do not invent a second global store pattern.

10. **Design tokens.** Align with design system CSS vars/classes; no one-off hex when tokens exist.

11. **Anti-pattern — prop drilling hell:** prefer provide/inject or Pinia for deep shared state.

12. **Router.** Navigation guards lean; data fetching patterns match the project (composables vs views).

13. **Tests.** Component/composable tests when the repo already tests that layer.

## Done-when

- [ ] SFCs typed (props/emits); no prop mutation.
- [ ] Composables reuse shared logic; cleanup on unmount.
- [ ] Keys stable; computed preferred over watch-for-derive.
- [ ] Tokens/system styles respected.
- [ ] Composition API used for new Vue code.
- [ ] Pinia/global state used only when local state is insufficient.

## References (external)

- https://vuejs.org/style-guide/
- https://vuejs.org/guide/extras/composition-api-faq.html
- https://pinia.vuejs.org/core-concepts/
- https://github.com/anthropics/skills
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
