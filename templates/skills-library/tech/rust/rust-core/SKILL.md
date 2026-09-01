---
name: rust-core
description: >
  Idiomatic Rust — ownership, Result/Option, minimal unsafe, clippy hygiene,
  error types, and Cargo features. Use for Rust crates/apps. Not a mandate to
  expand into unrelated FFI backends without brief.
---

# rust-core

## Who / paths

- **You:** Rust application and library crates owned by this company.
- **Not you:** Go/C++ stacks; casual unsafe sprawl; expanding large FFI surfaces the brief did not request.
- **Paths:** `**/*.rs`, `**/Cargo.toml`, `**/Cargo.lock`, `**/rust-toolchain.toml`
- **Load when:** Brief names Rust crate/app work.

## How

1. **Ownership first.** Prefer borrowing over clones; clone deliberately. Make lifetimes obvious or return owned values when ergonomics win.

2. **Result/Option.** Result at fallible boundaries; use ?.

3. **Anti-pattern — unwrap culture:** unwrap/expect in library code without proven invariants. If expect, message states the invariant.

4. **Panic policy.** Libraries avoid panics for expected errors; binaries may panic on unrecoverable startup misconfig.

5. **Unsafe.** Minimal; each block gets a safety comment describing the invariant. Prefer safe wrappers.

6. **Clippy and fmt.** cargo fmt; fix clippy on touched code when CI expects. No broad allow without reason.

7. **Error types.** thiserror in libraries when callers match; anyhow in binaries/apps — stay consistent per layer.

8. **Cargo.** Explicit features; no wildcard deps without reason; document feature flags.

9. **Traits.** Implement Debug/Clone/Send/Sync as appropriate; keep traits small.

10. **Concurrency.** Match crate async runtime; do not block async runtimes on heavy CPU without spawn_blocking.

11. **API stability.** Semver-conscious for published crates; avoid breaking public types casually.

12. **Docs.** Public items get brief rustdoc when the crate is a shared interface.

13. **Tests.** Unit tests beside modules; integration tests under tests/ for public API behavior you change.

## Done-when

- [ ] No unjustified unwrap/unsafe on touched library paths.
- [ ] Result used at fallible boundaries; errors typed or anyhow per layer.
- [ ] cargo fmt + clippy-clean on touched code when required.
- [ ] Features/deps explicit; no mystery wildcards.
- [ ] Tests cover critical public behavior you changed.
- [ ] Safety comments present on any new unsafe blocks.

## References (external)

- https://doc.rust-lang.org/book/
- https://rust-lang.github.io/api-guidelines/
- https://doc.rust-lang.org/clippy/
- https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html
- https://github.com/pproenca/dot-skills
- https://www.agentskills.io/
