# Holding staff org

Conglomerate personnel. Spawn by `name:` frontmatter.

**User channels:**

| Topic | Who talks to the user |
| --- | --- |
| Product work inside a company | that company’s `ceo` / `ba-user` |
| Conglomerate / multi-company | `holding-ceo` |
| **Hiring / staffing deal** | **`holding-hr`** (after `holding-ceo` routes the shortage) |

**Hard rule:** only **holding** hires. A subsidiary **never** recruits — it only
notifies `holding-ceo`: *“we lack staff like …”*. Self-serve factory/budget
scripts stay holding-side tools, not subsidiary HR.

## Roster (holding)

| Role | Owns |
| --- | --- |
| `holding-ceo` | Shortage inbox; Assign HR; multi-company; no hire negotiation |
| `holding-hr` | **Only hiring authority** — deal with user; execute staffs/skills/harness |
| `holding-coordinator` | Cross-company handoffs (no product code, no hiring) |

## Cascade

```text
user / subsidiary
 └─ holding-ceo
     ├─ new company (chat) OR staffing shortage
     │    └─ holding-hr ↔ USER (budget, name, tech/roles, skills, duties,
     │         topology teams|companies, packages, project-root(s))
     │         → confirm/lock → create-company.sh / create-workspace.sh / hire SoT
     ├─ multi-company task → Assign subsidiary ceo(s) / coordinator
     └─ single-company product → that company's ceo (existing hop)
```

**Create company / workspace:** chat with `holding-ceo` (Assign `holding-hr`) **or**
self-serve `create-company.sh` / `create-workspace.sh` — same factory.

### Workspace topologies

| Topology | When | Roots |
| --- | --- | --- |
| **`teams`** | One product monorepo; **one** `ceo`/`cto`/BA/PO/QC/`git` for the whole workspace; FE/BE/mobile are tech teams (engineers + routes) only | One `--project-root` = parent |
| **`companies`** | User wants hard isolation / separate product contracts per package (each gets its own full formula) | **One `--project-root` per package** (adapters collide if shared) |

Parent registry file: `<parent>/.agents/WORKSPACE.md`.

### Hiring example

Subsidiary: *“holding-ceo, call feature — need one Swift developer.”*

1. **`holding-ceo`** → Assign **`holding-hr`** (no deal by CEO).
2. **`holding-hr` ↔ user**: have/need, options, budget for that hire, role
   name, skills to add, responsibilities, which paths/features they own.
3. User **confirms/locks** → HR executes into that company only.

### Cross-company API ask (canonical)

Example subsidiaries: `todo-backend-company`, `todo-react-company`,
`todo-android-company`, `todo-ios-company` — each created with **its own**
`--project-root` (e.g. `…/backend`, `…/web`, `…/android`, `…/ios`), typically via
`create-workspace.sh --topology companies`.

If the same packages instead live under **`teams`** topology (one company at the
monorepo parent), FE↔BE stays **in-company** (`cto` / `tech-lead`) — do **not**
route through holding.

When a **frontend** company needs a **new/changed backend API** (mobile screens
often differ from web → different payloads/endpoints):

```text
frontend ceo  →  holding-ceo  →  backend ceo  →  backend lead/IC → QC
```

**Rules:**

1. Frontend **does not** Assign backend ICs directly (no bypass of holding).
2. `holding-ceo` (or `holding-coordinator`) carries a short English handoff:
   goal, why (e.g. Android-only screen), contract sketch, done-when, owning
   backend paths — then Assigns **backend `ceo` only**.
3. Backend `ceo` runs the **normal in-company cascade** (CTO/lead/IC/QC).
4. Result returns **up** backend → holding → requesting frontend `ceo`.
5. If **several** frontends need related APIs, holding **batches** one backend
   ask when possible (one job → one backend assignee stream), instead of three
   parallel unstructured pings.

Same pattern for any producer/consumer pair across subsidiaries (not only
todo/API).

## Always-on roles inside every subsidiary (formula)

Every company cloned from `templates/company/` **must** include:

| Role / team | Notes |
| --- | --- |
| `ceo` | In-company dispatch; product → `product-lead` first; cross-team up-then-down |
| `cto` | Architecture / tech selection with user+holding |
| `product-lead` | Product lane only: `ba-user` / `po-*`; `## Result` up to CEO (never spawn eng) |
| BA team (`ba-lead` → `ba-user`, `ba-workflow`) | Under product-lead; `ba-user` clarifies with user; `ba-workflow` owns Jira/tools |
| PO (`po-new`, `po-modify`; optional `po-lead`) | Writers own plans / AC; default Assign from `product-lead` |
| `git` | Commit / branch gate |
| QC team | Always present — shape adapts: one `qc-lead` + embedded `*-qc`, or a larger QC org |

**Strict + cheap (mandatory in every subsidiary):** each staff one lane — no
lateral cross-team spawn. Need another team → **up to CEO** with slim brief
(`goal` + `paths` + optional `plan_dir` + `read`) — **never** paste full plans
through a long staff chain. CEO hops and spawns down; IC opens those loci.

**Why split (beyond tokens):** each staff holds **1–3** skills (not a mega
catalog); each does **only its duty**; blocked on foreign work → escalate —
producer lands **headers/contract** first, consumer implements against them
**in parallel** (no one leaves their lane to fix the other tree).

## Optional / tech-shaped teams

CTO (+ holding/user) adds teams from the stack, for example:

- Frontend: JS/TS + React / Vue / Angular customs under `system/skills/customs/…`
- Backend, mobile, infra, …
- `data` team when analytics/reports are in scope

### Design team (when the company is frontend-shaped)

If the subsidiary is primarily **UI/UX** (React, mobile, etc.), CTO should seed a
**design** team (always English SoT):

| Role | Owns |
| --- | --- |
| `design-lead` | Assign one design IC per hop; quality bar for UX/UI consistency |
| `ux-writer` | User-facing copy, microcopy, tone — clearer UX through words |
| `ui-designer` | Design system for the project: color, type, iconography, components |
| `ba-user` (design intake) | Always-on BA IC, with a **design-intake** duty: read designs from
  external sources (Figma/specs/other products) and produce a **canonical brief**
  for the company (what to build, constraints, glossary) — not invent pixels |

**Flow:** external design / research → `ba-user` (canonical brief) → `design-lead`
Assigns `ui-designer` / `ux-writer` as needed → engineering consumes the system
and copy. Engineering does **not** invent a parallel design system.

`marlin-language-company` is the **reference instance** of the formula (Marlin /
C++ / Comm / MPM shaped — usually **no** design team). New frontend companies
copy the formula **plus** design staffs when CTO marks the stack UI-heavy.
