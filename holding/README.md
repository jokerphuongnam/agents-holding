# Holding Company OS

**Holding** is the conglomerate Company OS. It coordinates subsidiaries; it does
not own product trees.

| Home | Path |
| --- | --- |
| Dev SoT (in a product repo) | `<repo>/.agents/holding/` |
| **Public git package** | `this repository` (refresh: `pack_agents_holding.sh`) |
| System install | `~/.agents/holding/` (+ `~/.agents/templates/`) |
| Subsidiaries | always `<project>/.agents/<slug>-company/` |

**SoT → generate:** polish this tree; `system/install/company_os.sh` writes
adapters wherever each harness `[paths]` says.

Refresh the community package (then `cd …/agents-holding && git init`):

```bash
.agents/holding/system/install/pack_agents_holding.sh
```

Promote to system agents home (from this tree or from `agents-holding`):

```bash
.agents/holding/system/install/install_holding_system.sh [--dest ~/.agents]
# or, after clone of agents-holding:
# ./holding/system/install/install_holding_system.sh --dest ~/.agents
```

Create a subsidiary (after hire deal or self-serve):

```bash
.agents/holding/system/install/create-company.sh \
  --name my-app --budget medium --tech "react,nestjs" \
  --project-root /path/to/project \
  --packages "frontend:react,backend:nestjs"

# Or: create-workspace.sh --parent … --topology teams|companies --package …
```

Boot card: [`COMPANY_BOOT.md`](COMPANY_BOOT.md).  
Org / hire rules: [`system/staffs/ORG.md`](system/staffs/ORG.md).  
Layout detail: [`COMPANY.md`](COMPANY.md).

## Codex runtime

The Holding Company OS is the source of truth for the holding roster and routing rules.
After a subsidiary company is generated, run its installer from that company repository:

```bash
.agents/<company-slug>/system/install/company_os.sh codex
```

This generates the Codex runtime view under `.codex/`. Codex reads the generated boot
pointer and role cards from that workspace directory. Grok remains an independent runtime:

```bash
.agents/<company-slug>/system/install/company_os.sh grok
```

Do not edit generated runtime files by hand. Update Holding/Company source, then regenerate
only the selected harness.
