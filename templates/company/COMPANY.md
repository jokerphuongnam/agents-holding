# {{COMPANY_TITLE}} Company OS

Subsidiary under **`.agents/holding/`**. Formula clone from
`.agents/templates/company/`.

**Layout:** `system/` (staffs, skills, harness, install) · `cache/` · `example/eval/`.

**SoT vs generated:** polish this tree; `system/install/company_os.sh` writes
adapters wherever each harness `[paths]` says.

**Budget at create:** `{{BUDGET}}` — seeded into `system/harness/*.toml` tiers.

**Tech seed notes:** `{{TECH_HINTS}}`

**Language:** SoT English; user chat = user’s language. User channel: `ceo` + `ba-user`.

**Dispatch:** product asks → `product-lead` first. Cross-team → always
**## Result / Escalate up to CEO**, then CEO spawns down with slim brief
(`goal` + `paths` + optional `plan_dir` + `read`) — never ship full plan
bodies through the staff chain.

**Packages under this project root** (e.g. `frontend/`, `backend/`) are **teams**
in this company unless holding created sibling companies (`companies` topology
with separate roots). See `cache/WORKSPACE.md` when present.
