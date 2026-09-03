# Staffs org — {{COMPANY_TITLE}}

Canonical: this `system/staffs/` tree. Spawn by `name:` frontmatter.

**Always-on (formula):** `ceo`, `cto`, `ba-lead` (+ `ba-user` / `ba-workflow`),
`po-lead` (+ `po-new` / `po-modify`), `git`, QC (`qc-lead` + adapt). **Optional:**
tech teams (from CTO/stack), `data`, **design** (when UI-heavy — see holding ORG).

**User channel (product):** only `ceo` and `ba-user` address the user.

**Hiring:** this company does **not** recruit. Shortage → notify
`holding-ceo` only (*“we lack staff like …”*). `holding-hr` deals with the
user and writes staffs/skills. Do not add `system/staffs/` or hop agents locally
to “fill a gap.”

## Layout

```text
system/staffs/
├── ORG.md
├── leadership/     ceo, cto
├── ba/             ba-lead, ba-user, ba-workflow
├── po/             po-lead, po-new, po-modify
├── qc/             qc-lead (+ embed *-qc as the company grows)
└── cross-cut/      git
```

`tech-lead` lives on the **seeded tech team** folder (`frontend/`, `mobile/`,
or `backend/`) — not under `cross-cut/`. `git` stays cross-cut.

**Tiers (default):** leads (`ba-lead`, `po-lead`, `design-lead`, `qc-lead`,
`tech-lead`) = `dispatch` (effort low). BA ICs `ba-user` / `ba-workflow` =
medium. Plan writers `po-new` / `po-modify` = always xhigh.

Tech teams are added after CTO selects the stack (see `CTO_TECH_SEED.md` if
present). Do not invent Marlin-specific teams unless this is a Marlin company.

**Monorepo (`teams`):** packages under this company’s `--project-root` are tech
**teams** only (hop routes by path prefix). There is still **one** `ceo`, `cto`,
BA/PO/QC, and `git` for the whole workspace — do not spawn per-package ceos.
Cross-package work stays with `cto` / `tech-lead`.
True multi-**company** handoffs only when holding registered sibling companies
(see parent `.agents/WORKSPACE.md`, topology `companies`).
