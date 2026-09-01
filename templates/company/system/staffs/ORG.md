# Staffs org — {{COMPANY_TITLE}}

Canonical: this `system/staffs/` tree. Spawn by `name:` frontmatter.

**Always-on (formula):** `ceo`, `cto`, `ba`, `po-modify`, `po-new`, `git`, QC
(`qc-lead` + adapt). **Optional:** tech teams (from CTO/stack), `data`,
**design** (when UI-heavy — see holding ORG).

**User channel (product):** only `ceo` and `ba` address the user.

**Hiring:** this company does **not** recruit. Shortage → notify
`holding-ceo` only (*“we lack staff like …”*). `holding-hr` deals with the
user and writes staffs/skills. Do not add `system/staffs/` or hop agents locally
to “fill a gap.”

## Layout

```text
system/staffs/
├── ORG.md
├── leadership/     ceo, cto
├── product/        ba, po-modify, po-new
├── qc/             qc-lead (+ embed *-qc as the company grows)
└── cross-cut/      git, tech-lead, …
```

Tech teams are added after CTO selects the stack (see `CTO_TECH_SEED.md` if
present). Do not invent Marlin-specific teams unless this is a Marlin company.
