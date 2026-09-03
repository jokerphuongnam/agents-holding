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
