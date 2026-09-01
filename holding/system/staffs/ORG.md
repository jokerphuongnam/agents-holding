# Holding staff org

Conglomerate personnel. Spawn by `name:` frontmatter.

**User channels:**

| Topic | Who talks to the user |
| --- | --- |
| Product work inside a company | that company’s `ceo` / `ba` |
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
     ├─ staffing shortage ("we lack staff like this")
     │    └─ holding-hr ↔ USER (budget, name, role, skills, duties, project slice)
     │         → confirm/lock → HR writes .agents/<company>/ (+ company_os)
     ├─ multi-company task → Assign subsidiary ceo(s) / coordinator
     └─ single-company product → that company's ceo (existing hop)
```

### Hiring example

Subsidiary: *“holding-ceo, call feature — need one Swift developer.”*

1. **`holding-ceo`** → Assign **`holding-hr`** (no deal by CEO).
2. **`holding-hr` ↔ user**: have/need, options, budget for that hire, role
   name, skills to add, responsibilities, which paths/features they own.
3. User **confirms/locks** → HR executes into that company only.

### Cross-company API ask (canonical)

Example subsidiaries: `todo-backend-company`, `todo-react-company`,
`todo-android-company`, `todo-ios-company`.

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
| `ceo` | In-company dispatch |
| `cto` | Architecture / tech selection with user+holding |
| BA team (`ba`) | Clarify ask |
| PO team (`po-modify`, `po-new`) | Plans / AC |
| `git` | Commit / branch gate |
| QC team | Always present — shape adapts: one `qc-lead` + embedded `*-qc`, or a larger QC org |

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
| `ba` (design intake) | Same always-on `ba`, with a **design-intake** duty: read designs from
  external sources (Figma/specs/other products) and produce a **canonical brief**
  for the company (what to build, constraints, glossary) — not invent pixels |

**Flow:** external design / research → `ba` (canonical brief) → `design-lead`
Assigns `ui-designer` / `ux-writer` as needed → engineering consumes the system
and copy. Engineering does **not** invent a parallel design system.

`marlin-language-company` is the **reference instance** of the formula (Marlin /
C++ / Comm / MPM shaped — usually **no** design team). New frontend companies
copy the formula **plus** design staffs when CTO marks the stack UI-heavy.
