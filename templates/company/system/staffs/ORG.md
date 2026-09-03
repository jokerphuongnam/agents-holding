# Staffs org — {{COMPANY_TITLE}}

Canonical: this `system/staffs/` tree. Spawn by `name:` frontmatter.

**Always-on (formula):** `ceo`, `cto`, **`product-lead`**, `ba-lead` (+ `ba-user` /
`ba-workflow`), `po-new` / `po-modify` (optional `po-lead` for large PO orgs),
`git`, QC (`qc-lead` + adapt). **Optional:** tech teams (from CTO/stack),
`data`, **design** (when UI-heavy — see holding ORG).

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
├── product/        product-lead
├── ba/             ba-lead, ba-user, ba-workflow
├── po/             po-new, po-modify (, optional po-lead)
├── qc/             qc-lead (+ embed *-qc as the company grows)
└── cross-cut/      git
```

`tech-lead` lives on the **seeded tech team** folder (`frontend/`, `mobile/`,
or `backend/`) — not under `cross-cut/`. `git` stays cross-cut.

**Tiers (default):** leads (`product-lead`, `ba-lead`, `po-lead`, `design-lead`,
`qc-lead`, `tech-lead`) = `dispatch` (effort low). BA ICs `ba-user` /
`ba-workflow` = medium. Plan writers `po-new` / `po-modify` = always xhigh.

## Product cascade (canonical)

```text
ceo → product-lead → ba-user → product-lead → (po-new | po-modify)? → ## Result → ceo → eng
```

- CEO never spawns `ba-user` / `po-*` for product — **`product-lead` first**.
- After BA (or when no PO needed / PO finished), product-lead **`## Result` up** —
  does **not** Assign eng.
- **CEO** hops and spawns eng with a **slim brief**.

## Cross-team handoff (general — strict + cheap)

**Always up to CEO, then down.** No lateral spawn across teams.

```text
anyone who needs another team
  → ## Result / ## Escalate → CEO
       (goal, paths, plan_dir?, read:, hint?)
CEO → hop → team-lead | unique IC
  → [lead →] IC
IC opens only plan_dir + read loci — never receives a pasted full plan
```

| Field | Meaning |
| --- | --- |
| `goal` | One-line ask |
| `paths` | Code/work directories the IC owns |
| `plan_dir` | e.g. `cache/plans/<slice>/` (directory only OK) |
| `read` | Optional loci: `AC.md:12-40`, `file:start-end` |
| `done-when` | Testable exit |

**Strict:** each staff stays in lane (one job). **Cheap:** do not ship plan
bodies through a long staff chain — cite directory + read pointers.

Same-team help → own `*-lead` `## Assign`. Foreign team → **up to CEO** only.

## Cheap hop (mandatory)

1. Scripts first (`hop.py`, `task_cache.py`, `task_memory.py`). Brief ≤ ~15 lines.
2. Do not paste ORG, **full plans**, skill bodies, or full logs.
3. One live hop. Child returns `## Assign` / `## Result`; parent spawns.
4. Unique IC known → skip team-lead. QC only after IC `done`.

## Monorepo / workspace

**Monorepo (`teams`):** packages under this company’s `--project-root` are tech
**teams** only (hop routes by path prefix). There is still **one** `ceo`, `cto`,
product/BA/PO/QC, and `git` for the whole workspace — do not spawn per-package
ceos. Cross-package work: **Escalate up to CEO** (slim brief), not lateral lead→lead.
True multi-**company** handoffs only when holding registered sibling companies
(see parent `.agents/WORKSPACE.md`, topology `companies`).

Tech teams are added after CTO selects the stack (see `CTO_TECH_SEED.md` if
present). Do not invent Marlin-specific teams unless this is a Marlin company.
