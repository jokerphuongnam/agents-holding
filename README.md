# agents-holding

**Conglomerate Company OS** for AI coding agents — Grok, Codex, Claude, …

One **holding** coordinates many **subsidiary** companies (one per product). You talk to holding for budget and hiring; each subsidiary runs product work through its own `ceo` / `ba-user`.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/agents-holding/main/install.sh | bash
```

**Bench (Todo API + React, three real arms):** see [`example/eval/RESULTS.md`](example/eval/RESULTS.md) — case 3 (this library) scored highest against the full expected bar including FE unit/UI tests.

That downloads from GitHub and installs into `~/.agents/holding` + `~/.agents/templates`.

Re-run the same command anytime after you push updates.

---

## What you get

| Capability | What it does |
| --- | --- |
| **Holding org** | `holding-ceo`, `holding-hr`, `holding-coordinator` — conglomerate roles, not product coders |
| **Factory** | `create-company.sh` clones a full subsidiary Company OS into any project |
| **Template sync** | Edit defaults in one company → `promote-company-defaults.sh` → holding `templates/` → `update-company.sh --all` distributes; customs kept |
| **Child companies** | Same relation as holding→company (recursive). Only with **`hr` + manage-children`**: HR owns child portfolio (approve/create/grants/staff); product hop → child ceo |
| **Skills library** | Ready customs (React, Nest, Kotlin, Swift, BA/PO, design, QC, …) copied by `--tech` tags |
| **Budget → harness** | `low` / `medium` / `high`  tunes agent tiers; plan/doc roles (`po-*`) always stay max |
| **Hiring (holding-only)** | Subsidiaries never recruit — they report gaps; HR deals with **you** on role, skills, duties, slice |
| **Habit cache (local)** | SQLite prefs for how *you* usually structure / restaff companies — `habit_cache.py` get-by-key; **gitignored**, not shared |
| **Company registry (local)** | Inventory of subsidiaries + **family** + cross-company **`resolve`** (FE→BE handoffs without opening every ORG) — `company_registry.py`; **gitignored** per machine, not shared |
| **Company task memory** | Per-staff SQLite — CEO `resolve --brief` into IC brief; skip re-resolve/record on reuse → ~**40%** fewer tokens after ~3 similar tasks (measured) |
| **Multi-runtime (optional split)** | Default: full roster on every vendor. Opt-in `runtime_router.toml` (`enabled = true`) so each generate only includes mapped roles (e.g. ceo→grok, ba/po→codex, *-dev→claude). SoT staffs unchanged. |

---

## Requirements

- macOS or Linux
- `bash`, `python3` (3.10+)
- Optional: `rsync` (faster installs)

---

## Two copies (do not mix)

| Copy | Path | Purpose |
| --- | --- | --- |
| **Author** | `this repository` | Edit → `git push` |
| **Machine** | `~/.agents/holding` (+ `templates/`) | Runtime — always from GitHub via `curl \| bash` |

### Author loop

```bash
cd /path/to/agents-holding
# …edit…
git add -A && git commit -m "…" && git push

curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/agents-holding/main/install.sh | bash
```

### Options

```bash
curl -fsSL …/install.sh | bash -s -- --dest ~/.agents
curl -fsSL …/install.sh | bash -s -- --ref main
curl -fsSL …/install.sh | bash -s -- --from-local /path/to/agents-holding
```

```text
~/.agents/
├── holding/       # conglomerate (runtime)
└── templates/     # factory inputs
```

---

## Quick start — new product company

Two supported ways (same factory under the hood):

### 1) Talk to agents (recommended for humans)

After `curl …/install.sh | bash`, open any runtime on a project folder (or home) and talk to **`holding-ceo`**:

> Create a new company for this project. Budget medium. Tech: TypeScript, React, NestJS. Project root is `/path/to/project`. Name it `my-app`.

`holding-ceo` Assigns **`holding-hr`**. HR deals with you on name, budget, `--tech` tags, roles/skills, then runs (or asks you to confirm) `create-company.sh` + `company_os.sh all`.

### 2) Self-serve script

```bash
mkdir -p /path/to/project && cd /path/to/project
git init   # optional

~/.agents/holding/system/install/create-company.sh \
  --name my-app \
  --budget medium \
  --tech "typescript,react,nestjs" \
  --project-root "$PWD" \
  --packages "frontend:react,backend:nestjs"

.agents/my-app-company/system/install/company_os.sh all

# Multi-package: teams (one company) or companies (one root per package)
~/.agents/holding/system/install/create-workspace.sh \
  --parent "$PWD" --topology teams --name my-app --budget medium \
  --package frontend:react --package backend:nestjs
```

Either way you get `/path/to/project/.agents/my-app-company/` with staffs, hop, harness, and matching skills. Then talk to that company’s **`ceo`** / **`ba-user`** for product work.

**Topologies:**

| Topology | When | Linkage |
| --- | --- | --- |
| **teams** | Packages in one product are linked | Shared ceo/BA/PO; cross-package via cto/tech-lead |
| **companies** | Each package is its own holding subsidiary | Cross-company via holding-ceo / registry `relate` |
| **children** | Smaller agent context under one product company | Same relation as holding→company (recursive). See [Child companies](#child-companies-developer-guide) |

---

## How to use

### A. Create a company

**A1 — Via agents**

1. User → **`holding-ceo`**: new company + budget + tech hints + `--project-root`.
2. **`holding-ceo` → `holding-hr`**: options brief (roster, skills-library tags).
3. **`holding-hr` ↔ user**: negotiate name / budget / tech / roles until you **confirm/lock**.
4. HR executes factory + `company_os.sh all`, then returns the subsidiary path.

**A2 — Via script (self-serve)**

```bash
~/.agents/holding/system/install/create-company.sh \
  --name <slug> \
  --budget low|medium|high \
  --tech "tag1,tag2,..." \
  --project-root /path/to/project
```

| Flag | Meaning |
| --- | --- |
| `--name` | Company slug → `.agents/<slug>-company/` |
| `--budget` | Effort map for harness + hop tiers |
| `--tech` | Tags matched against `templates/skills-library/MANIFEST.json` |
| `--project-root` | Project directory that should own the subsidiary |
| `--packages` | `path[:tech],…` → tech teams + hop routes (monorepo `teams`) |
| `--topology` | `teams` (default). Use `create-workspace.sh` for `companies` |

Then:

```bash
/path/to/project/.agents/<slug>-company/system/install/company_os.sh all
```

### B. Change budget later

```bash
python3 ~/.agents/holding/system/install/apply_budget_harness.py \
  --dest /path/to/project/.agents/<slug>-company \
  --budget high \
  --budget-json ~/.agents/holding/system/install/budget_tiers.json

/path/to/project/.agents/<slug>-company/system/install/company_os.sh all
```

**Invariant:** `po-new`, `po-modify` always keep max tier (`xhigh`), even on `low`.

### C0. Company registry (holding inventory + cross-company resolve)

**Feature:** a per-machine index of every subsidiary holding manages — so
`holding-ceo` can **list**, **scan**, and **`resolve`** the right company for a
handoff (e.g. chat frontend needs an API → pick `chat-backend-company`) without
opening every subsidiary `ORG.md`.

Store (**gitignored**, never commit / never share across machines):

`~/.agents/holding/cache/companies.sqlite`

```bash
CR=~/.agents/holding/system/install/company_registry.py

python3 "$CR" --help
python3 "$CR" list                 # pretty table on TTY; --tsv for agents
python3 "$CR" show --slug chat-frontend-company
python3 "$CR" check                # dup slug / missing SoT paths

# Discover Company OS trees already on disk; upsert into the DB:
python3 "$CR" scan
python3 "$CR" scan --register
python3 "$CR" scan --root ~/Documents --max-depth 8

# SoT deleted on disk but still listed:
python3 "$CR" prune
python3 "$CR" prune --forget --i-am-human

# Family (slug order can vary — set explicitly):
#   chat-backend, web-chat-api  →  --family chat
#   retail-frontend, api-retail →  --family retail
python3 "$CR" set-family --slug chat-backend-company --family chat
create-company.sh … --family chat   # also accepted at create time

# Optional explicit edge + token-cheap handoff:
python3 "$CR" relate --from chat-frontend-company --to chat-backend-company \
  --kind api --bidirectional
python3 "$CR" related --slug chat-frontend-company
python3 "$CR" resolve --from chat-frontend-company --need api
# → pick / project_root / channel=ceo  — Assign that subsidiary ceo only

# Factory auto-registers; manual one-off:
python3 "$CR" register \
  --slug chat-frontend-company \
  --project-root /path/to/chat-web \
  --company-path /path/to/chat-web/.agents/chat-frontend-company \
  --budget medium --topology companies --family chat --packages frontend

# Same slug at two folders → check warns; archive renames SoT only:
python3 "$CR" archive --id <id> --i-am-human
```

Docs: [`holding/cache/COMPANIES.md`](holding/cache/COMPANIES.md).

**Score order for `resolve`:** explicit `relate` > same **family** > packages/tech/path.

### C. Hiring — always through holding

Subsidiaries **do not** add staffs themselves.

```text
Anyone (subsidiary ceo / you):
  “holding-ceo, we lack staff like … (e.g. one Swift dev for Call)”

holding-ceo → holding-hr

holding-hr ↔ you (deal):
  • budget impact for this hire
  • role name
  • skills to add (from skills-library)
  • responsibilities
  • which part of the project (paths / features)

you confirm/lock → holding-hr writes into that company's .agents/<slug>-company/
         → company_os.sh all
```

You may still run factory / `apply_budget_harness.py` yourself when the lock is already clear — HR is the default path for **personnel choices**, not a hard gate on scripts.

### D. Multi-company work

Cross-company asks (e.g. chat frontend needs a new backend API) go:

```text
frontend ceo → holding-ceo
  → company_registry.py resolve --from <fe> --need api
  → Assign backend ceo only (short English brief)
  → … → result back up
```

Prefer **`resolve` / `related`** (and `--family` / `relate`) over browsing every
company tree. Never hop straight from one subsidiary IC to another company’s IC.

### E. Who talks to the user

| Topic | Role |
| --- | --- |
| Product work inside a company | that company’s `ceo` / `ba-user` |
| Conglomerate status / routing | `holding-ceo` |
| Hiring deal | `holding-hr` |
| Cross-company handoff notes | `holding-coordinator` (via ceo) |

---

## Layout of this repository

```text
agents-holding/
├── README.md                 ← you are here
├── holding/                  # conglomerate SoT
│   ├── COMPANY.md
│   ├── COMPANY_BOOT.md
│   ├── cache/
│   │   └── COMPANIES.md      # company registry docs (sqlite is local/gitignored)
│   └── system/
│       ├── staffs/           # holding-ceo, holding-hr, holding-coordinator
│       ├── harness/          # grok/codex/claude.toml + optional runtime_router.toml
│       ├── skills/defaults/marlin-hop/
│       └── install/          # factory + company_os + company_registry + budget
└── templates/
    ├── company/              # cloned into each new subsidiary
    ├── skills-library/       # optional customs by --tech
    ├── hop-reference/        # hop scripts for new companies
    └── install/company_os.sh
```

After system install, day-to-day paths are under `~/.agents/…`.

---

## Skills library (examples)

Pass tags with `--tech` (comma-separated). Matching skills are copied into the new company’s `system/skills/customs/…`.

Examples: `react`, `redux`, `nextjs`, `nestjs`, `vue`, `angular`, `kotlin`, `android`, `swift`, `swiftui`, `csharp`, `unity`, `python`, `rust`, `go`, `bash`, plus always-on BA / PO / QC (and design when UI-shaped).

See `templates/skills-library/MANIFEST.json` and `SOURCES.md`.

---

## Runtime adapters

| Runtime | Generated by `company_os.sh` |
| --- | --- |
| **Grok** | Cards under export + links into `.grok/agents` (per harness `[paths]`) + **`.grok/launch-ceo.sh`** |
| **Codex** | `.codex/AGENTS.md` pointer (no repo-root `AGENTS.md`) + fallback in `.codex/config.toml` |
| **Claude** | Runtime tree / symlinks per `claude.toml` |

**Rule:** edit SoT under `holding/` or `<slug>-company/` only; regenerate adapters — do not hand-polish generated folders as the source of truth.

---

## One vendor vs many vendors (runtime_router)

Not everyone wants cross-agent setup. Company OS supports both:

| Mode | Config | What `company_os.sh all` does |
| --- | --- | --- |
| **Single vendor** (default) | `system/harness/runtime_router.toml` → `enabled = false` (or ignore the file) | **Full roster** on Grok **and** Codex **and** Claude — open whichever CLI you use; same company SoT |
| **Split vendors** (opt-in) | set `enabled = true` + edit `[[roles]]` | Each generate includes **only** roles mapped to that runtime |

Example split (edit to taste; SoT `staffs/**` / `agents.tsv` stay portable):

```toml
# .agents/<slug>-company/system/harness/runtime_router.toml
enabled = true

[[roles]]
match = "ceo"
runtime = "grok"

[[roles]]
match = "ba-*"
runtime = "codex"

[[roles]]
match = "po-*"
runtime = "codex"

[[roles]]
match = "*-dev"
runtime = "claude"

[[roles]]
match = "*"
runtime = "grok"
```

```bash
# After editing:
python3 .agents/<slug>-company/system/skills/defaults/marlin-hop/scripts/runtime_router.py check
python3 …/runtime_router.py match --role ba-lead    # → codex
.agents/<slug>-company/system/install/company_os.sh all
```

- **Same runtime Assign** → native spawn in the current CLI.  
- **Cross-runtime Assign** → `runtime_router.py assign --from ceo --to <role> --goal '…'` (handoff under `cache/handoff/`; `--execute` to invoke the other CLI). Requires that CLI installed + logged in; missing bin → **error** (no silent fallback).

Shipped template: [`templates/company/system/harness/runtime_router.toml`](templates/company/system/harness/runtime_router.toml) · short guide: [`templates/company/system/harness/README.md`](templates/company/system/harness/README.md).

---

## Open Grok as company `ceo` (important)

Bare `grok` in a project **does not** auto-select Company OS `ceo`. Project
`.grok/config.toml` also **cannot** set `agent.name` (Grok only allows MCP /
plugins / permissions there).

After `company_os.sh grok` (or `all`), use one of:

```bash
cd /path/to/project          # or a git worktree of that repo

# Recommended — generated launcher
./.grok/launch-ceo.sh
./.grok/launch-ceo.sh "ship the empty-state fix"

# Equivalents
grok --agent ceo
GROK_AGENT=ceo grok
```

Optional **direnv** so plain `grok` becomes ceo in this tree (keep `.envrc`
gitignored if personal):

```bash
# .envrc
export GROK_AGENT=ceo
```

| Want | Command |
| --- | --- |
| Product work in a subsidiary | `./.grok/launch-ceo.sh` inside that project |
| Conglomerate / hire / new company | `grok --agent holding-ceo` (holding install in `~/.agents`) |
| Regenerate ceo card + launcher | `.agents/<slug>-company/system/install/company_os.sh grok` |

See also `.grok/README.md` written next to the launcher.

---

## Typical workflows

### Greenfield app

1. Install `agents-holding` → `~/.agents`
2. `create-company` with `--project-root` + `--tech`
3. `company_os.sh all` in the project
4. Open Grok as **`ceo`**: `./.grok/launch-ceo.sh` (not bare `grok`)

### Existing codebase

1. Same create (or hire more roles later)
2. Tell `holding-ceo` what stack you already use; `holding-hr` proposes roster/skills
3. You confirm/lock → HR applies → regenerate adapters

### Need a specialist mid-flight

1. Subsidiary notifies `holding-ceo` (“missing Swift for Call”)
2. `holding-hr` deals with you
3. Lock → staffs/customs/hop updated

### Multi-company handoff (registry)

1. Create each package as its own company (`create-workspace.sh --topology companies`) with `--family` (e.g. `chat`, `retail`)
2. Optional: `relate --from chat-frontend-company --to chat-backend-company --kind api --bidirectional`
3. When FE needs an API: talk to **`holding-ceo`** → runs `resolve --from … --need api` → Assigns **backend `ceo` only**
4. Backfill existing trees anytime: `company_registry.py scan --register`

### Scoped child under one product company

See **[Child companies (developer guide)](#child-companies-developer-guide)** below.

---

## Child companies (developer guide)

Use **children** when one product company needs **smaller agent context** for a
package/slice — same relationship as **holding → company**, nested (and
recursive). Prefer **teams** when packages are tightly linked and should share
one ceo/BA/PO.

```text
holding
  └── my-app-company              ← holding subsidiary
        └── hr                    ← REQUIRED before any child-org flow
        └── children/
              └── sdk-ios/
                    ├── GRANTS.toml
                    ├── META.toml
                    └── sdk-ios-company/   ← full Company OS (own ceo, staffs, …)
```

Children may own further children the same way (each level needs its own `hr`
before it can nest deeper).

### Who does what

| Ask | Who |
| --- | --- |
| Code / feature inside a child package | Parent **ceo** hop → **child ceo** only → child staffs |
| Create / approve child, inventory, grants policy, restaff | Parent **hr** (`manage-children`) |
| Child needs more parent docs/API | Child ceo → parent **ceo** (grants/info) — no parent-tree crawl |
| Child needs more people | Child ceo → parent ceo → parent **hr** |
| This company has no `hr` but wants children | Escalate to HR **above** to hire `hr` here first (`holding-hr` for a top subsidiary; parent `hr` if this is already a child) |

**Invariant:** no `hr` on a company ⇒ **no** child-org flows (`create-child` refuses).  
**Invariant:** no sibling hops between children — only escalate to the immediate parent.

### Setup (scripts)

Install/refresh machine copy first (`curl …/install.sh` or `install_holding_system.sh`).

```bash
PARENT=/path/to/project/.agents/my-app-company
PKG=/path/to/package   # code root owned by the child

# 1) Enable HR on the parent (dev bootstrap). Product flow: upper HR hires hr after user lock.
python3 ~/.agents/holding/system/install/seed_parent_hr.py --parent "$PARENT"
# → system/staffs/cross-cut/hr.md
# → system/skills/customs/cross-cut/hr/manage-children/

# 2) Create child (prefer: parent hr runs this after user lock on name/budget/grants)
~/.agents/holding/system/install/create-child-company.sh \
  --parent "$PARENT" \
  --name sdk-ios \
  --budget low \
  --tech "swift,ios" \
  --project-root "$PKG" \
  --grant-path documents/api/ \
  --placement nested

# 3) Inventory
python3 ~/.agents/holding/system/install/children_registry.py --parent "$PARENT" list

# 4) Generate adapters for the child
"$PARENT"/children/sdk-ios/sdk-ios-company/system/install/company_os.sh all
```

| Flag | Meaning |
| --- | --- |
| `--parent` | Path to parent `…/<slug>-company/` (must already have `hr`) |
| `--name` | Child stem → `…/children/<stem>/<stem>-company/` |
| `--project-root` | Code package the child owns |
| `--grant-path` | Read-only slice from parent (repeatable); reference only — not a crawl license |
| `--placement nested` | Default: Company OS under parent `children/` |
| `--placement external` | Company OS at `<project-root>/.agents/<stem>-company/` |

### Product runtime (token-cheap) — keep this flow

Parent still owns the user channel. Coding asks for a child path **do not** load
child ORG/staffs at the parent:

```text
parent ceo  --hop(path)-->  handoff: child ceo only (short goal)
                                │
                                ▼
                          child ceo hops own staffs
                          (scope = child company folder + package)
                                │
                                ▼ (need more parent info)
                          escalate → parent ceo (ask grants/info)
```

Hop data: parent `…/data/children.tsv`  
Try: `python3 …/marlin-hop/scripts/hop.py --path sdk-ios/src/…` → expect `handoff: child`.

**Child fence (hard):**

- Hop: out of scope → `handoff: parent`
- Tool: `scope_guard.py check --path …` (exit 2 = deny; ask parent ceo)
- SoT: `SCOPE.md` = allowed roots (child company folder + package only)

```bash
python3 …/pkg-company/system/skills/defaults/marlin-hop/scripts/scope_guard.py \
  check --path ../other/src/x.go
# expect: deny / handoff:parent
```

### Org runtime (hr portfolio)

```text
create / approve child / grants policy / restaff / enable hr on a descendant
  → parent ceo Assigns hr
  → hr loads manage-children → deal with user → lock → execute into child SoT
```

Skill: `system/skills/customs/cross-cut/hr/manage-children/SKILL.md`  
Staff: `system/staffs/cross-cut/hr.md`

### More detail

- `templates/company/children/README.md` — layout, grants, invariants  
- `templates/company/children/GRANTS.toml.example`  
- `holding/system/install/children_registry.py --help`  
- `holding/system/install/create-child-company.sh --help`

---

## Updating

### A. Pull a new agents-holding release (machine install)

```bash
curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/agents-holding/main/install.sh | bash
# or: git pull && ./holding/system/install/install_holding_system.sh --dest ~/.agents
~/.agents/holding/system/install/company_os.sh all
```

This refreshes `~/.agents/holding` + `~/.agents/templates` only. Existing
companies are **not** changed until you run **C** below.

### B. Promote defaults from one company → holding templates

Use when you improve defaults in a **reference** company (e.g. `pilot-company`)
and want that to become the factory template:

```text
reference company  ──promote──►  templates/  ──update──►  other companies
```

```bash
# preview
~/.agents/holding/system/install/promote-company-defaults.sh \
  --from /path/to/project/.agents/pilot-company \
  --dry-run

# write into git checkout (commit + push), then reinstall on machines
~/.agents/holding/system/install/promote-company-defaults.sh \
  --from /path/to/project/.agents/pilot-company \
  --agents-home /path/to/agents-holding

# or write straight into ~/.agents/templates (this machine only)
~/.agents/holding/system/install/promote-company-defaults.sh \
  --from /path/to/project/.agents/pilot-company
```

**Promotes:** hop scripts + `SKILL.md`, `company_os.sh`, `FORMULA.md`, harness
(re-generalized with `{{COMPANY_SLUG}}` / `{{EFFORT_*}}`).

**Does not promote:** `staffs/`, `skills/customs/`, hop `data/`, `COMPANY*.md`,
`CTO_TECH_SEED.md`.

### C. Distribute templates → existing companies

```bash
~/.agents/holding/system/install/update-company.sh --all --dry-run
~/.agents/holding/system/install/update-company.sh --all
# or one company:  update-company.sh --dest /path/to/.agents/<slug>-company
```

Syncs the same safe defaults. Keeps customs. Diverged / unreviewed files are
skipped unless `--force` / `--force-file`. Then:

```bash
/path/to/project/.agents/<slug>-company/system/install/company_os.sh all
```

Fingerprint: `<company>/cache/template_sync.json`.

| Status | Meaning |
| --- | --- |
| `ok` / `update` / `add` | Safe to apply |
| `diverge` | Local edited since last sync — skipped |
| `review` | No fingerprint and file ≠ template — skipped |

More detail: [`holding/system/install/AGENTS_HOLDING_README.md`](holding/system/install/AGENTS_HOLDING_README.md) § Updating.

---

## Language

- **User chat:** your language  
- **Holding + company SoT** (staffs, ORG, skills, plans, hop): **English**

---

## License / contributing

Add your license when you publish. PRs that keep staff cards short (owns / not-you / done-when) and avoid inventing unpaid roles on `low` budget are welcome.

Maintainer tip (refresh the public checkout from a monorepo holding SoT):

```bash
# default out: this repository
path/to/monorepo/.agents/holding/system/install/pack_agents_holding.sh
cd /path/to/agents-holding && git add -A && git commit && git push
```
