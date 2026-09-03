# Workspace templates

SoT for **multi-package parents** (frontend / backend / mobile / …).

Holding factory (`create-workspace.sh`, `create-company.sh --packages`) renders
these into the product tree. Do not hand-edit generated copies as the long-term
source — change files here, then re-run factory / install.

## Topologies

| Topology | File rendered | Shared staffs | Per package |
| --- | --- | --- | --- |
| **`teams`** (default) | parent `.agents/WORKSPACE.md` from `WORKSPACE.teams.md` + company `cache/WORKSPACE.md` from `COMPANY_CACHE_WORKSPACE.md` | **One** `ceo`, `cto`, BA, PO, QC, `git` (+ design when UI-shaped) | Tech engineers + hop routes only |
| **`companies`** | parent `.agents/WORKSPACE.md` from `WORKSPACE.companies.md` | Full formula **per** package company | Own `--project-root` (never share — adapters collide) |

## Placeholders

| Token | Meaning |
| --- | --- |
| `{{PARENT}}` | Absolute parent folder |
| `{{TOPOLOGY}}` | `teams` or `companies` |
| `{{COMPANY_SLUG}}` | Subsidiary slug (`*-company`) — teams only |
| `{{PACKAGES}}` | CSV `path[:tech],…` |
| `{{SUBSIDIARIES_TABLE}}` | Markdown rows for companies topology |
| `{{NEXT_STEPS}}` | `company_os.sh` reminders |

## Factory entrypoints

```bash
# One company, many tech teams (shared ceo/cto/…)
create-workspace.sh --parent … --topology teams --name shop \
  --package frontend:react --package backend:nestjs

# Sibling companies (one root each)
create-workspace.sh --parent … --topology companies \
  --package frontend:shop-web:react --package backend:shop-api:nestjs
```

Also: `create-company.sh --packages "frontend:react,backend:nestjs"` (implies teams).
