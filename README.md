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
| **Skills library** | Ready customs (React, Nest, Kotlin, Swift, BA/PO, design, QC, …) copied by `--tech` tags |
| **Budget → harness** | `low` / `medium` / `high`  tunes agent tiers; plan/doc roles (`po-*`) always stay max |
| **Hiring (holding-only)** | Subsidiaries never recruit — they report gaps; HR deals with **you** on role, skills, duties, slice |
| **Multi-runtime** | `company_os.sh` generates adapters for Grok (`.grok/agents`), Codex (`.codex/`), Claude (runtime dir) |

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
  --project-root "$PWD"

.agents/my-app-company/system/install/company_os.sh all
```

Either way you get `/path/to/project/.agents/my-app-company/` with staffs, hop, harness, and matching skills. Then talk to that company’s **`ceo`** / **`ba-user`** for product work.

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

Cross-company asks (e.g. frontend needs a new backend API) go:

```text
frontend ceo → holding-ceo → backend ceo → … → result back up
```

Never hop straight from one subsidiary IC to another company’s IC.

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
│   └── system/
│       ├── staffs/           # holding-ceo, holding-hr, holding-coordinator
│       ├── harness/          # grok.toml, codex.toml, claude.toml
│       ├── skills/defaults/marlin-hop/
│       └── install/          # factory + company_os + budget tools
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
| **Grok** | Cards under export + links into `.grok/agents` (per harness `[paths]`) |
| **Codex** | `.codex/AGENTS.md` pointer (no repo-root `AGENTS.md`) + fallback in `.codex/config.toml` |
| **Claude** | Runtime tree / symlinks per `claude.toml` |

**Rule:** edit SoT under `holding/` or `<slug>-company/` only; regenerate adapters — do not hand-polish generated folders as the source of truth.

---

## Typical workflows

### Greenfield app

1. Install `agents-holding` → `~/.agents`
2. `create-company` with `--project-root` + `--tech`
3. `company_os.sh all` in the project
4. Chat with subsidiary `ceo` / `ba-user`

### Existing codebase

1. Same create (or hire more roles later)
2. Tell `holding-ceo` what stack you already use; `holding-hr` proposes roster/skills
3. You confirm/lock → HR applies → regenerate adapters

### Need a specialist mid-flight

1. Subsidiary notifies `holding-ceo` (“missing Swift for Call”)
2. `holding-hr` deals with you
3. Lock → staffs/customs/hop updated

---

## Updating

```bash
cd agents-holding
git pull
./holding/system/install/install_holding_system.sh --dest ~/.agents
~/.agents/holding/system/install/company_os.sh all
```

Existing subsidiaries are **not** overwritten. Re-pack skills into a company only if you re-run factory pieces or copy skills deliberately.

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
