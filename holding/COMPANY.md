# Holding Company OS

**Holding** coordinates **subsidiary companies** under `.agents/<name>-company/`
(or `.agents/<name>/` when created by the factory). Subsidiaries do not talk
cross-project ad hoc — they escalate to **holding** for multi-company work.

## Layout (dual home)

Holding SoT may live in either place:

| Home | Path |
| --- | --- |
| **Dev SoT** (product repo) | `<repo>/.agents/holding/` |
| **Public package** | `this repository` — community git (**agents-holding**) |
| **System home** | `~/.agents/holding/` (+ `~/.agents/templates/`) |

**Subsidiaries always:** `<project>/.agents/<slug>-company/`  
(never under `~/.agents/` as the product tree — factory uses `--project-root`).

```text
# Dev (in a product repo)
.agents/
├── holding/                    # conglomerate SoT (this tree)
├── templates/                  # company + skills-library
├── marlin-language-company/    # first subsidiary + reference instance (optional)
└── <other>-company/

# Public git checkout (canonical)
this repository/   →  ./install.sh  →  ~/.agents/{holding,templates}/
```

Pack + promote:

```bash
.agents/holding/system/install/pack_agents_holding.sh
.agents/holding/system/install/install_holding_system.sh [--dest ~/.agents]
# or from the package: ./holding/system/install/install_holding_system.sh --dest ~/.agents
```

## Always: SoT → generate

Each company (holding or subsidiary) keeps a SoT (`system/`, `cache/`, `example/`).  
`system/install/company_os.sh` generates adapters **wherever that harness reads**
(holding export dirs, `.grok/agents`, …) — polish SoT only. Prefer no
repo-root `AGENTS.md`.

## Workspace topologies (one parent folder, many packages)

A parent folder often has several packages (`frontend/`, `backend/`, `apps/web/`, …).
The user chooses how holding maps them:

| Topology | Meaning | `--project-root` |
| --- | --- | --- |
| **`teams` (default)** | One `.agents/<slug>-company/`; packages = **tech teams only** + hop routes. **Shared once:** `ceo`, `cto`, BA/PO/QC, `git` (and design when UI-shaped). Not one ceo per package. | Parent (monorepo root) |
| **`companies`** | Each package = full subsidiary (own ceo/cto/BA/…); handoffs via `holding-ceo` | **One root per package** (e.g. `…/frontend`, `…/backend`) |

**Why separate roots for `companies`:** runtime adapters (`.grok/agents`, `.claude/`)
are flat per project root — two companies sharing one root **overwrite** each other.
Namespaced adapters are out of scope for v1.

Self-serve:

```bash
# Monorepo → one company, FE/BE as teams
~/.agents/holding/system/install/create-workspace.sh \
  --parent /path/to/shop --topology teams --name shop --budget medium \
  --package frontend:react --package backend:nestjs

# Sibling companies (separate roots under the same parent)
~/.agents/holding/system/install/create-workspace.sh \
  --parent /path/to/shop --topology companies --budget medium \
  --package frontend:shop-web:react --package backend:shop-api:nestjs
```

`create-company.sh --packages "frontend:react,backend:nestjs"` is the single-company
path (implies `teams`). Parent registry: `<parent>/.agents/WORKSPACE.md`
(rendered from `templates/workspace/`).

## Holding responsibilities

1. **Coordinate** work that spans two or more companies.
2. **Create** new companies with the user: user gives **budget** to
   `holding-ceo` → CEO Assigns **`holding-hr`** → HR returns hiring brief
   (roster + `--tech`) → factory runs.
3. **Do not** implement product code inside a subsidiary’s trees.

## Budget → hiring → harness

### Hiring personnel (holding-only)

Subsidiaries **do not hire**. They only notify:

```text
subsidiary → holding-ceo: "we lack staff like …"
          → holding-hr ↔ user (deal: budget, name, role, skills,
                               responsibilities, project slice)
          → confirm/lock → HR writes into that company
```

**No hire before user confirm/lock** with HR.

### Budget + harness

User gives budget wording to **`holding-ceo`** (`low` | `medium` | `high`). **Default path:** CEO Assigns **`holding-hr`**. HR
normalizes budget, proposes roster/`--tech` in the options brief, and after
confirm/lock applies harness.

**Self-serve:** user or CEO may set budget themselves anytime:

```bash
# new company
.agents/holding/system/install/create-company.sh \
  --name <slug> --budget low --tech "react,nestjs"

# re-budget existing company
python3 .agents/holding/system/install/apply_budget_harness.py \
  --dest .agents/<slug>-company \
  --budget high \
  --budget-json .agents/holding/system/install/budget_tiers.json
# then: .agents/<slug>-company/system/install/company_os.sh all
```

Same script either way (writes `system/harness/*.toml` `[tier_to_effort]`,
hop `agents.tsv` tiers, `BUDGET_APPLIED.json`). HR is optional help, not a lock.

**Invariant:** plan/doc writers (`po-new`, `po-modify`) always stay at
`policy.always_max_tier` (`xhigh`) — even on **low**.

## Language

Holding + company SoT = **English**. User chat = user’s language.
