# Harness drivers + optional runtime router

| File | Role |
| --- | --- |
| `grok.toml` / `codex.toml` / `claude.toml` | Vendor layout + tier→model/effort |
| **`runtime_router.toml`** | **Opt-in** split: which SoT roles go into each **generated** export |

## Two ways teams work

| Mode | `runtime_router.toml` | `company_os.sh all` |
| --- | --- | --- |
| **Single vendor** (default) | `enabled = false` (or omit file) | Full roster on Grok **and** Codex **and** Claude — pick one CLI to work in |
| **Split vendors** | `enabled = true` + `[[roles]]` map | Each generate only roles for that runtime (e.g. ceo→grok, ba/po→codex, *-dev→claude) |

**Invariant:** `system/staffs/**` and hop `agents.tsv` stay portable. Only generated adapters change.

```bash
# Classic (everyone same brand — open whichever CLI you like):
#   leave enabled = false
.agents/<slug>-company/system/install/company_os.sh all

# Split (dev wants each brand for its job):
#   set enabled = true, edit [[roles]], then:
python3 …/runtime_router.py check
.agents/<slug>-company/system/install/company_os.sh all
```
