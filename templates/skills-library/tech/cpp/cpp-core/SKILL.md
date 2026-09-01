---
name: cpp-core
description: >
  Modern C++ safety and structure — RAII, ownership, const-correctness, headers,
  threading, and warning hygiene for application/native code. Use when the brief
  names C++. Not Marlin compiler trees unless this is the Marlin company brief.
---

# cpp-core

## Who / paths

- **You:** C++ application code, native modules, and shared libraries for this company.
- **Not you:** Other language stacks; design UI; Marlin compiler/runtime unless the brief assigns it here.
- **Paths:** `**/*.{hpp,h,hh,hxx,cpp,cc,cxx,ipp}`, `**/CMakeLists.txt`, `**/*.cmake`
- **Load when:** Brief explicitly includes C++ sources or native library work.

## How

1. **RAII always.** Resources owned by types that release in destructors. Prefer `unique_ptr`/`shared_ptr`/containers over raw owning pointers.

2. **Anti-pattern — naked ownership:** `new`/`delete` pairs without documented exception; owning raw pointers in public APIs.

3. **Ownership clarity.** Default single owner (`unique_ptr`); `shared_ptr` only for shared lifetime. Non-owning views via references/`span`/`string_view`. Never return dangling refs to locals.

4. **const-correctness.** `const` methods/refs when non-mutating; `constexpr` for compile-time values.

5. **Headers.** Minimal includes; forward-declare when possible. No `using namespace` in headers. Hide impl in `.cpp`.

6. **Rule of 0/3/5.** Prefer RAII members and defaulted special members; if you define one of dtor/copy/move, define the set deliberately.

7. **Errors.** Match project style (`expected`/`optional`/exceptions). Honor `[[nodiscard]]` on touched APIs.

8. **Threading.** Document shared mutable state; mutex/atomic with invariants; no data races.

9. **Standard.** Match project C++17/20/23. Prefer std utilities over reinvented wheels.

10. **Warnings.** Fix what you introduce; no blanket pragma suppress without a one-line reason.

11. **Includes.** `#pragma once` or guards per project; keep include order consistent.

12. **Build/API stability.** Do not casually break public headers or install exports when brief says API-stable.

13. **Tests.** Exercise ownership/lifetime edge cases for APIs you change when a test target exists.

## Done-when

- [ ] Ownership clear; no unjustified raw owning pointers.
- [ ] Headers lean; no `using namespace` in headers.
- [ ] const-correct on new/changed APIs.
- [ ] Touched targets build clean under project warning level.
- [ ] No dangling views; lifetimes documented at tricky boundaries.
- [ ] Shared mutable state synchronized or confined.

## References (external)

- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- https://en.cppreference.com/w/
- https://github.com/HK-hub/AgentSkills
- https://github.com/svssdeva/agentic-skills
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://www.agentskills.io/
