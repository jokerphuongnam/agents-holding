# Company formula

Every subsidiary follows this shape (see reference:
`.agents/marlin-language-company/`):

```text
<company>/
├── COMPANY.md, README.md, COMPANY_BOOT.md
├── system/
│   ├── staffs/     # always-on + tech-shaped personnel
│   ├── skills/     # defaults/ + customs/<team>/<role>/
│   ├── harness/    # grok|codex|claude.toml — [paths] + budget tiers
│   └── install/    # company_os.sh
├── cache/          # graphs, plans, reports, export, cache/
└── example/eval/   # hop+subagents vs subagents vs raw
```

**Always-on staffs:** ceo, cto, **product-lead**, ba-lead (+ ba-user,
ba-workflow), po-new / po-modify (optional po-lead), git, qc-lead; tech-lead
on the seeded tech team.  
**Optional:** tech teams (stack), data, po-lead (large PO orgs).  
**Holding** creates the company; **subsidiary cto** refines tech teams.

**Product + cross-team (strict + cheap):** CEO → product-lead → ba-user →
product-lead → (po-*?) → ## Result → CEO → eng. Need another team → always
**up to CEO** with slim `plan_dir` + `read` (never paste full plans). Each
staff stays in lane.

## Frontend-shaped companies — design staffs

When stack is UI-heavy (React, mobile, …), include under `system/staffs/design/`:

- `design-lead`
- `ux-writer`
- `ui-designer`

And use always-on `ba-user` for **design intake** (external designs → canonical brief).
