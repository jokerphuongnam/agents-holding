---
name: csharp-unity
description: >
  Unity C# gameplay/engine scripting — composition, cheap Update, allocation
  hygiene, ScriptableObject config, and editor/runtime guards. Use for Unity
  client/game code. Not ASP.NET APIs (csharp-backend).
---

# csharp-unity

## Who / paths

- **You:** Unity C# gameplay scripts, systems, and editor tooling for this company.
- **Not you:** ASP.NET/server APIs (`csharp-backend`); pure .NET without Unity APIs (`csharp-core`); design pixel polish.
- **Paths:** `**/Assets/**/*.cs`, `**/Assets/**/*.asmdef`, `**/Packages/**/Runtime/**/*.cs`, `**/Assets/**/Editor/**/*.cs`
- **Load when:** Brief touches Unity Assets scripts, prefabs wiring in code, or gameplay systems.

## How

1. **Composition over god MonoBehaviours.** Split input, simulation, and view into small components + orchestrators.

2. **Anti-pattern — god object:** thousand-line `Player.cs` owning UI, netcode, and physics.

3. **Cheap Update/FixedUpdate.** Cache in `Awake`/`Start`. No per-frame `GetComponent` / `FindObjectOfType` / `Find`.

4. **Allocation hygiene.** Avoid per-frame boxing, LINQ, string concat, and new collections in hot loops. Profile when brief requires.

5. **ScriptableObjects.** Shared config/balance in assets — not scene singletons or magic constants everywhere.

6. **Serialize intentionally.** `[SerializeField]` private fields; explicit bootstrap over fragile singleton order.

7. **Coroutines/async.** Stop on disable/destroy. No fire-and-forget `async void` except UI handlers; handle exceptions.

8. **Physics & time.** Forces in `FixedUpdate`; use `Time.deltaTime` for frame-independent motion.

9. **UI vs sim.** Presenters separate from simulation; prefer events over polling everything in Update.

10. **Editor vs runtime.** `#if UNITY_EDITOR` for editor APIs; no editor debug hooks in player without defines.

11. **Assemblies.** asmdefs to limit compile surface; no cycles between gameplay and tooling.

12. **Events.** Unsubscribe on destroy; avoid static event leaks.

13. **Scenes.** Prefer additive/load patterns the project uses; do not hard-code scene indices without constants.

## Done-when

- [ ] No per-frame GetComponent/Find spam in touched code.
- [ ] Hot paths avoid obvious allocations; Update lean.
- [ ] Shared config via ScriptableObjects or project data assets.
- [ ] Sim vs view responsibilities split enough to reason about.
- [ ] Compiles in editor; editor-only APIs guarded.
- [ ] Event/coroutine lifetimes cleaned on destroy/disable.

## References (external)

- https://docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity.html
- https://docs.unity3d.com/Manual/ExecutionOrder.html
- https://docs.unity3d.com/Manual/class-ScriptableObject.html
- https://docs.unity3d.com/Manual/ScriptCompilationAssemblyDefinitionFiles.html
- https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions
- https://www.agentskills.io/
