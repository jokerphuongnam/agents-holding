# Company registry (local only)

SQLite `companies.sqlite` here is a **per-machine** inventory of subsidiaries
(slug + project root + SoT path). **Gitignored** — each holding install differs;
never commit or pack this DB into `agents-holding`.

## Agent I/O

Staffs read CLI TSV stdout only — never open `*.sqlite` / dump.

```bash
CR=".agents/holding/system/install/company_registry.py"
# ~/.agents/holding/system/install/company_registry.py

python3 "$CR" list              # pretty table on TTY
python3 "$CR" list --tsv        # agent / machine TSV
python3 "$CR" scan              # discover .agents/*-company on disk
python3 "$CR" scan --register   # upsert discoveries into local DB
python3 "$CR" scan --root ~/Documents --max-depth 8
python3 "$CR" prune             # SoT deleted on disk but still in registry
python3 "$CR" prune --forget --i-am-human   # drop those registry rows
python3 "$CR" check
python3 "$CR" show --slug my-app-company
```

TTY → ASCII table. Agents / pipes → pass `--tsv` (or `COMPANY_REGISTRY_TSV=1`).

Factory (`create-company.sh`) calls `register` on success. Use `scan --register`
to backfill companies created before the registry existed.

## Deleted on disk

If someone removes `.agents/<slug>-company` (or the project) but holding still
lists it, `list`/`check` mark `status=missing`. Prefer:

```bash
python3 "$CR" prune
python3 "$CR" prune --forget --i-am-human
```

`prune --forget` only deletes **registry rows** — it does not touch remaining app files.

## Family (slug arrangement can vary)

**Source of truth:** explicit `family` field — not a fixed slug grammar.

Slug order may be anything:

| Slug examples | Set family to |
| --- | --- |
| `chat-backend`, `chat-frontend` | `chat` |
| `web-retail-api`, `web-retail` | `retail` (you choose the id) |

```bash
# At create / register:
create-company.sh --name web-retail-frontend … --family retail
python3 "$CR" register … --family chat

# Later:
python3 "$CR" set-family --slug web-retail-frontend --family retail
python3 "$CR" set-family --slug chat-backend --family chat
```

Heuristic `{org}-{product}-{role}` parse is **fallback only** when `family` is empty.

## Relations + resolve (cross-company, token-cheap)

```bash
python3 "$CR" related --slug chat-frontend   # links + same-family peers
python3 "$CR" resolve --from chat-frontend --need api
# prefers same family; optional:
python3 "$CR" relate --from … --to … --kind api --bidirectional
```

Cascade: requesting `ceo` → `holding-ceo` → `resolve` → Assign **target `ceo`
only** (short English brief). Never Assign foreign ICs directly.

Score order: explicit `relate` > same **family** > packages/tech/path keywords.

## Duplicates

Same slug at two different `project_root` values is allowed but flagged
(`dup=1`, `hint=same_slug_other_root`). Prefer:

1. `archive --id … --i-am-human` on the stale SoT (renames to `*-archived-TIMESTAMP`)
2. or rename the slug / keep both if intentional forks

`archive` does **not** delete app source; it may print a suggest line for that.

## Not this

| Store | Purpose |
| --- | --- |
| `companies.sqlite` | Conglomerate inventory |
| `user_habits.sqlite` | How *you* usually structure / restaff |
| `<company>/cache/WORKSPACE.md` | Per-subsidiary topology note |
| `<parent>/.agents/WORKSPACE.md` | Sibling list for one parent folder |
