---
name: marlin-hop
description: >
  Script lookup instead of reading full ORG or catalogs. Use when spawn /
  holding-ceo classify Path, or when listing / rostering holding roles.
  Do not use to implement product. /marlin-hop
---

# Cheap lookup (run; do not read ORG.md)

Scripts live next to this file. First tool on a routing hop.

```bash
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --path <file>
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --path <file> --harness codex
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --section hiring
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --list
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/hop.py --roster holding-ceo
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/export_harness.py --to grok
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/export_harness.py --to codex
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/export_harness.py --to all
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/sync_agents.py
python3 .agents/holding/system/skills/defaults/marlin-hop/scripts/task_cache.py show|set|clear
# Company product hop — durable per-staff memory (ALWAYS index first):
python3 .agents/<slug>-company/system/skills/defaults/marlin-hop/scripts/task_memory.py index --staff <ic> --path <file> [--goal '…']
# mode=reuse only:
python3 .agents/<slug>-company/system/skills/defaults/marlin-hop/scripts/task_memory.py get --staff <ic> --key <key>
# after finish (new OR reuse-with-changes; upsert overwrites):
python3 .agents/<slug>-company/system/skills/defaults/marlin-hop/scripts/task_memory.py record-done --staff <ic> --goal '…' --path '…' --summary '…'
```


Holding overview: `.agents/holding/COMPANY.md`. Harness drivers: `.agents/holding/system/harness/*.toml`.

Stdout is the brief. Do **not** open `ORG.md` or the skill catalog after the script printed.

- `hop.py` → agent, **tier**, harness, model/effort (from harness map), capability_mode, one skill path
- `hop.py --list` → full agent list from `data/agents.tsv` (do **not** ls `.md`)
- `hop.py --roster <rank>` → one-line blurbs of the rank below; **do not open child `.md`**
- `export_harness.py` → materialize runtime views (Grok cards; Codex `AGENTS.md`; Claude mounts)
- `sync_agents.py` → thin alias for `export_harness.py --to grok`

### Spawn brief (parent / holding-ceo)

- Spawn the exact `subagent_type` hop returned (`holding-hr`, `holding-coordinator`, …).
- Prompt is a **short goal** only: path, done-when, constraints. Do not rewrite persona.
- Cascade: user/subsidiary → holding-ceo → holding-hr (hire) or holding-coordinator (multi-company).
- Product work after hire returns to the **subsidiary** `ceo` hop — not holding ICs.

Route tables are TSV under `data/`, not JSON.
