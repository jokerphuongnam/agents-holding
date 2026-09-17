# Harness drivers + optional runtime router

| File | Role |
| --- | --- |
| `grok.toml` / `codex.toml` / `claude.toml` | Vendor layout + tier→model/effort |
| **`runtime_router.toml`** | **Opt-in** split: which SoT roles go into each **generated** export |

## Two ways teams work

| Mode | `runtime_router.toml` | `company_os.sh all` |
| --- | --- | --- |
| **Single vendor** (default) | `enabled = false` (or omit file) | Full roster on Grok **and** Codex **and** Claude — pick one CLI to work in |
| **Split vendors (merge)** | `enabled = true` + `[[roles]]` map | Each generate only roles for that runtime (e.g. ceo→grok, ba-*→claude, po-*→codex) |

**Invariant:** `system/staffs/**` and hop `agents.tsv` stay portable. **Staff cards never change** when you pick grok vs merge — only which harness/runtime runs them changes. Generated adapters may filter; SoT does not.

| Launch | What happens |
| --- | --- |
| **`grok` / `codex` / `claude`** | Full that vendor: whole session uses that harness setup (`tier_to_model` / `tier_to_effort` in that `.toml`). Staff still the same role. |
| **`merge`** | Overlay only: `runtime_router.toml` picks **which vendor CLI** each staff runs on; model/effort come from **that** vendor’s harness + the staff’s portable `tier`. Staff definition unchanged. |

**Merge hop example:** CEO session on grok, BA mapped to claude → `hop` **CLI-bridges** into Claude (not a native grok spawn of `ba-user`). BA staff file / blurb / skills stay the same.
```bash
RR=system/skills/defaults/marlin-hop/scripts/runtime_router.py

# Classic (everyone same brand — open whichever CLI you like):
#   leave enabled = false
.agents/<slug>-company/system/install/company_os.sh all

# Split (merge): set enabled = true, edit [[roles]], then:
python3 …/$RR check
python3 …/$RR resolve --role ba-user --session grok
# → runtime=claude, model/effort from claude.toml + BA tier; mode=cli
python3 …/$RR hop --from ceo --to ba-user --session grok --goal 'clarify AC'
# plan + handoff; add --execute to invoke Claude CLI
.agents/<slug>-company/system/install/company_os.sh all
```
