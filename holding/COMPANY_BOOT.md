# Holding boot (any runtime)

You are inside the **Holding Company OS** (`.agents/holding/` or `~/.agents/holding/`).
Grok, Codex, Claude, … are **runtimes** — they do not own the conglomerate.

**Language:** reply to the user in **their** language; keep all holding artifacts
(roles, ORG, skills, hop, harness, export) in **English**.

**User channel (holding):**

| Topic | Who talks to the user |
| --- | --- |
| Conglomerate / multi-company / **new company ask** | **`holding-ceo`** |
| **Create-company or hire deal** (budget, name, tech, roles, skills) | **`holding-hr`** (after `holding-ceo` routes) |

Creating a company is supported **via chat** (ceo → hr ↔ you → factory) **or**
self-serve `create-company.sh` — same factory.

Subsidiary product chat stays with that company’s `ceo` / `ba-user` — not holding ICs.

Full guide: [`README.md`](README.md) · org: [`system/staffs/ORG.md`](system/staffs/ORG.md).

## Do this first

1. If you just installed or changed hop / `harness/*.toml`:

```bash
.agents/holding/system/install/company_os.sh grok         # or: codex / claude / all
# system home:
# ~/.agents/holding/system/install/company_os.sh all
```

2. Route with hop — do **not** read all of `ORG.md`:

```bash
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --path <file>
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --roster holding-ceo
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --list
```

3. Act as the **role** hop returns (or the parent assigned).
4. Load **one** skill path from hop (`skill:`) when present.
5. Cascade:
   - New company → **`holding-ceo`** → **`holding-hr`** ↔ user → lock → `create-company.sh` + `company_os.sh all`.
   - Shortage → **`holding-ceo`** → **`holding-hr`** ↔ user → lock → HR writes into that company.
   - Multi-company → **`holding-ceo`** → **`holding-coordinator`** / subsidiary `ceo`(s).
6. Short briefs only (goal / path / done-when). English SoT only.
7. **Habits (optional):** HR may `habit_cache.py propose` once (new-company /
   restaff) for a compact prior — never open the SQLite blob; never skip lock.
   Data is local/gitignored (`cache/user_habits.sqlite`).

## Portable vs vendor

- Role cards in `system/staffs/**`: portable (`tier`, permissions) — **no** baked `model: grok-…`.
- Vendor model/effort: `system/harness/<id>.toml` + `cache/export/` (or the runtime UI).
- Match UI/model strength to hop `tier` (`dispatch` … `xhigh`).

## Runtime-specific mounts

| Runtime | Boot artifact |
| --- | --- |
| Grok | `.agents/holding/cache/export/grok/` + flat links under `.grok/agents` |
| Codex | `.agents/holding/cache/export/codex/AGENTS.md` (not repo-root, not `~/.codex/AGENTS.md`) |
| Claude | `.agents/holding/cache/export/claude-runtime/` tree mounts (avoids clobbering project `.claude`) |

Re-generate: `.agents/holding/system/install/company_os.sh <harness|all>`
