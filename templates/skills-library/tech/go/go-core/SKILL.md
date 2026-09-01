---
name: go-core
description: >
  Idiomatic Go — package layout, error wrapping, context, concurrency, modules,
  and testing. Use for Go services and libraries. Not Rust/C++ or frontend
  stacks.
---

# go-core

## Who / paths

- **You:** Go services, libraries, and CLIs for this company.
- **Not you:** Rust/Python/TS stacks; embedding business logic in shell; design UI.
- **Paths:** `**/*.go`, `**/go.mod`, `**/go.sum`, `**/cmd/**`, `**/internal/**`
- **Load when:** Brief names Go code changes.

## How

1. **Layout.** cmd/ binaries; internal/ private packages; public packages carefully. Avoid circular imports.

2. **Errors.** Return error; wrap with fmt.Errorf and %w. Do not discard with _ without reason.

3. **Anti-pattern — panic control flow:** panics for ordinary failures in libraries.

4. **Context.** First param ctx context.Context on I/O/RPC. Propagate cancel/deadline; do not store context in structs long-term.

5. **Concurrency.** Goroutines with clear lifetime + errgroup/cancel. Mutex or channel ownership for shared memory. No leaked goroutines; no map races.

6. **APIs.** Accept interfaces, return structs as practical. Keep interfaces small at consumer side.

7. **Naming.** MixedCaps; short clear package names; avoid stutter.

8. **Modules.** go mod tidy; pin versions deliberately; unexplained replace directives are defects.

9. **Logging.** Structured (slog/zap); no secrets. Pass logger via deps/context per repo pattern.

10. **HTTP/server.** Timeouts on clients/servers; graceful shutdown with context; validate handler inputs.

11. **Tables.** Prefer table-driven tests; t.Helper; use t.Parallel thoughtfully.

12. **Race.** Run go test -race on concurrent code when CI allows.

13. **Go vet.** Clean on touched packages; honor context key typing rules (custom key types).

## Done-when

- [ ] Errors checked and wrapped; no panic-for-control-flow.
- [ ] Context propagated on I/O APIs you touched.
- [ ] No goroutine leaks; shared state synchronized.
- [ ] Packages laid out idiomatically (cmd/internal when applicable).
- [ ] go test (and race when relevant) passes for touched packages.
- [ ] No unexplained replace directives introduced.

## References (external)

- https://go.dev/doc/effective_go
- https://go.dev/wiki/CodeReviewComments
- https://go.dev/blog/go1.13-errors
- https://go.dev/blog/context
- https://github.com/HK-hub/AgentSkills
- https://www.agentskills.io/
