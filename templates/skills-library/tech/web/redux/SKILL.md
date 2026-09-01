---
name: redux
description: >
  Redux Toolkit and React-Redux — slices, typed hooks, selectors, and when not
  to put server cache in Redux. Use when global client state is required. Not a
  default for all remote data (prefer Query/SWR).
---

# redux

## Who / paths

- **You:** Redux store, slices, selectors, and React-Redux bindings.
- **Not you:** Stuffing all server cache into Redux when TanStack Query/SWR fits; Vuex/Pinia; backend APIs.
- **Paths:** `**/store/**/*.{ts,js}`, `**/slices/**`, `**/features/**/*Slice.ts`, `**/selectors/**`
- **Load when:** Brief requires global client state or existing Redux feature work.

## How

1. **Redux Toolkit.** createSlice / configureStore. Avoid hand-written switch reducers for new code unless legacy.

2. **Typed hooks.** Export typed useAppDispatch / useAppSelector once; do not repeat RootState casts.

3. **Scope.** Complex cross-tree client workflows and coordinated UI. Prefer Query/SWR for remote GET cache unless RTK Query is standard.

4. **RTK Query (when used).** createApi; invalidate tags deliberately; do not duplicate the same cache in slices.

5. **Selectors.** Pure; createSelector when deriving objects/arrays to avoid needless re-renders.

6. **Anti-pattern — unstable selectors:** inline selectors returning new objects in useSelector without memoization.

7. **Actions.** Intent-revealing names; side effects in thunks/listeners/RTKQ — not ad-hoc in every component.

8. **Immutability.** Immer inside slices; never mutate state outside reducers.

9. **Provider.** Single store Provider at root (or clearly scoped sub-apps).

10. **Serializable.** Keep payloads serializable; no class instances in state without explicit middleware config.

11. **Migration.** Delete dead slices/selectors when removing Redux from a feature.

12. **DevTools.** Action names readable; avoid mega-payloads of entire trees when a diff id suffices.

13. **Tests.** Reducer/selector unit tests for non-trivial logic you change.

## Done-when

- [ ] Toolkit used for new Redux code.
- [ ] Selectors stable; no accidental new-object selectors.
- [ ] Server cache not duplicated without documented reason.
- [ ] Typed hooks used; store serializable.
- [ ] Dead slices removed when feature drops Redux.
- [ ] Side effects not scattered as ad-hoc component fetches that fight the store.

## References (external)

- https://redux.js.org/usage/next
- https://redux-toolkit.js.org/usage/usage-guide
- https://react-redux.js.org/
- https://github.com/vercel-labs/agent-skills
- https://github.com/pproenca/dot-skills
- https://www.agentskills.io/
