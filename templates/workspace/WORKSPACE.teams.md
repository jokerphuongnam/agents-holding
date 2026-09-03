# Workspace registry

| Field | Value |
| --- | --- |
| Topology | `{{TOPOLOGY}}` |
| Parent | `{{PARENT}}` |
| Company | `{{COMPANY_SLUG}}` (`.agents/{{COMPANY_SLUG}}/`) |
| Packages | `{{PACKAGES}}` |

## Shared staffs (once)

This workspace is **one** company OS. Shared for the whole parent:

- `ceo`, `cto`
- BA (`ba-lead` / `ba-user` / `ba-workflow`)
- PO (`po-lead` / `po-new` / `po-modify`)
- QC (`qc-lead`), `git`
- design (when UI-shaped)

**Do not** spawn per-package ceos/ctos under `teams`.

## Tech teams (per package)

Each package path is a **tech team** slice only (engineers + hop `route.tsv`
prefixes). Cross-package work stays in-company (`cto` / `tech-lead`).
Hiring / new companies → `holding-ceo`.

## Next

{{NEXT_STEPS}}
