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

**Always-on staffs:** ceo, cto, ba-lead (+ ba-user, ba-workflow), po-lead (+
po-modify, po-new), git, qc-lead; tech-lead on the seeded tech team.  
**Optional:** tech teams (stack), data.  
**Holding** creates the company; **subsidiary cto** refines tech teams.

## Frontend-shaped companies — design staffs

When stack is UI-heavy (React, mobile, …), include under `system/staffs/design/`:

- `design-lead`
- `ux-writer`
- `ui-designer`

And use always-on `ba-user` for **design intake** (external designs → canonical brief).
