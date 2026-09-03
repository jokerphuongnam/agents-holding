#!/usr/bin/env bash
# Create a subsidiary company from .agents/templates/company/
# Usage:
#   create-company.sh --name my-app --budget medium --tech "typescript,react"
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
# Holding lives at <agents-home>/holding — agents-home is repo `.agents` or `~/.agents`
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
TEMPLATE="$AGENTS_HOME/templates/company"
BUDGET_JSON="$HOLDING_INSTALL/budget_tiers.json"
# Hop reference: prefer templates/hop-reference (system install); else Marlin company hop
REF_HOP="$AGENTS_HOME/templates/hop-reference"
if [[ ! -d "$REF_HOP/scripts" ]]; then
  REF_HOP="$AGENTS_HOME/marlin-language-company/system/skills/defaults/marlin-hop"
fi
REF_INSTALL="$AGENTS_HOME/templates/install"
if [[ ! -f "$REF_INSTALL/company_os.sh" ]]; then
  REF_INSTALL="$AGENTS_HOME/marlin-language-company/system/install"
fi

NAME=""
BUDGET="medium"
TECH=""
PROJECT_ROOT=""
DRY=0

usage() {
  cat <<'USAGE'
Create a subsidiary Company OS tree from templates/company.

  create-company.sh --name <slug> --budget low|medium|high […] \
    [--tech "a,b,c"] [--project-root <path>] [--dry-run]

Result:
  (default)           <agents-home>/<slug>-company/
  --project-root DIR  DIR/.agents/<slug>-company/

Holding may live in-repo (.agents/holding) or system (~/.agents/holding).
Call path: shortage/budget → holding-ceo → holding-hr ↔ user → this script.

Always-on staffs: ceo, cto, ba-lead (+ ba-user, ba-workflow), po-lead (+ po-*),
git, qc-lead, tech-lead (on seeded tech team, not cross-cut).
Leads = dispatch/low; ba-user/ba-workflow = medium; po-* writers = xhigh.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --budget) BUDGET="${2:-}"; shift 2 ;;
    --tech) TECH="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$NAME" ]]; then
  echo "error: --name required" >&2
  exit 2
fi
# Normalize budget aliases → low|medium|high via budget_tiers.json policy
BUDGET="$(python3 "$HOLDING_INSTALL/apply_budget_harness.py" \
  --budget "$BUDGET" --budget-json "$BUDGET_JSON" --normalize-only)"
case "$BUDGET" in
  low|medium|high) ;;
  *) echo "error: --budget must be low|medium|high " >&2; exit 2 ;;
esac

SLUG="$NAME"
[[ "$SLUG" == *-company ]] || SLUG="${SLUG}-company"
SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]/-/g')"
TITLE="$(echo "$SLUG" | sed 's/-company$//; s/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')"

if [[ -n "$PROJECT_ROOT" ]]; then
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
  mkdir -p "$PROJECT_ROOT/.agents"
  DEST="$PROJECT_ROOT/.agents/$SLUG"
else
  DEST="$AGENTS_HOME/$SLUG"
fi

if [[ ! -d "$TEMPLATE" || ! -f "$BUDGET_JSON" ]]; then
  echo "error: missing template ($TEMPLATE) or budget_tiers.json" >&2
  echo "hint: run holding system/install/install_holding_system.sh if using ~/.agents" >&2
  exit 1
fi

echo "[create-company] slug=$SLUG budget=$BUDGET tech=${TECH:-—}"
echo "[create-company] agents-home=$AGENTS_HOME"
echo "[create-company] dest=$DEST"

if [[ "$DRY" -eq 1 ]]; then
  echo "[create-company] dry-run OK (no write)"
  exit 0
fi

if [[ -e "$DEST" ]]; then
  echo "error: already exists: $DEST" >&2
  exit 1
fi

mkdir -p "$DEST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude '.DS_Store' "$TEMPLATE/" "$DEST/"
else
  cp -R "$TEMPLATE/." "$DEST/"
fi

# Replace placeholders
while IFS= read -r -d '' f; do
  case "$f" in
    *.png|*.jpg|*.jpeg|*.gif|*.webp|*.bin) continue ;;
  esac
  if grep -q '{{' "$f" 2>/dev/null; then
    tmp="$f.tmp.$$"
    sed \
      -e "s/{{COMPANY_SLUG}}/$SLUG/g" \
      -e "s/{{COMPANY_TITLE}}/$TITLE/g" \
      -e "s/{{BUDGET}}/$BUDGET/g" \
      -e "s/{{TECH_HINTS}}/${TECH:-none}/g" \
      "$f" > "$tmp" && mv "$tmp" "$f"
  fi
done < <(find "$DEST" -type f -print0)

# First pass: fill harness {{EFFORT_*}} placeholders from budget
python3 "$HOLDING_INSTALL/apply_budget_harness.py" \
  --dest "$DEST" --budget "$BUDGET" --budget-json "$BUDGET_JSON"

# Frontend-shaped? seed design staffs from template
TECH_L="$(echo "$TECH" | tr '[:upper:]' '[:lower:]')"
if echo "$TECH_L" | grep -Eq 'react|vue|angular|ios|android|flutter|swiftui|compose|frontend|mobile|ui|ux|next'; then
  if [[ -d "$TEMPLATE/system/staffs/design" ]]; then
    mkdir -p "$DEST/system/staffs/design"
    cp -R "$TEMPLATE/system/staffs/design/." "$DEST/system/staffs/design/"
    echo "[create-company] seeded design staffs (frontend-shaped tech hints)"
  fi
fi

# Tech engineer stub cards (thin) when hints match
TECH_LEAD_DIR=""
seed_tech_lead_once() {
  local dir="$1"
  if [[ -n "$TECH_LEAD_DIR" ]]; then
    return 0
  fi
  TECH_LEAD_DIR="$dir"
  mkdir -p "$DEST/system/staffs/$dir"
  cat > "$DEST/system/staffs/$dir/tech-lead.md" <<EOF
---
name: tech-lead
description: Slice design. Not CTO. Not a default coder.
tier: dispatch
permission_mode: plan
capability_mode: read-only
---
Slice design inside **${dir}**. Escalate architecture to \`cto\`. Dispatch
engineers on this team. Do not implement product.
EOF
}

seed_eng() {
  local role="$1" blurb="$2" dir="$3"
  mkdir -p "$DEST/system/staffs/$dir"
  seed_tech_lead_once "$dir"
  cat > "$DEST/system/staffs/$dir/${role}.md" <<EOF
---
name: ${role}
description: ${blurb}
tier: medium
permission_mode: default
capability_mode: all
---
${blurb}

Follow CTO_TECH_SEED.md and design brief when UI-shaped. Load only skills named
in the brief (customs under system/skills/customs/). Escalate cross-company API
needs to company ceo → holding-ceo.
EOF
}

# Prefer mobile → frontend → backend for where tech-lead card lives
if echo "$TECH_L" | grep -Eq 'ios|android|flutter|swiftui|compose|mobile'; then
  seed_eng mobile-engineer "Mobile app code per CTO seed. Not design system." "mobile"
fi
if echo "$TECH_L" | grep -Eq 'react|vue|angular|frontend|next|typescript|javascript'; then
  seed_eng frontend-engineer "Frontend app code per CTO seed. Not design system." "frontend"
fi
if echo "$TECH_L" | grep -Eq 'node|express|nestjs|backend|fastapi|django|rails|spring'; then
  seed_eng backend-engineer "Backend/API services per CTO seed. Cross-company API via holding." "backend"
fi
# No stack hint yet: keep tech-lead reachable under cross-cut until CTO seeds a team
if [[ -z "$TECH_LEAD_DIR" ]]; then
  seed_tech_lead_once "cross-cut"
fi

# Bootstrap hop: scripts/SKILL only — then seed company-local hop data (no Marlin roster)
if [[ -d "$REF_HOP" ]]; then
  mkdir -p "$DEST/system/skills/defaults/marlin-hop"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude 'data/' \
      --exclude 'agents/' \
      --exclude '__pycache__/' \
      "$REF_HOP/" "$DEST/system/skills/defaults/marlin-hop/"
  else
    rm -rf "$DEST/system/skills/defaults/marlin-hop"
    mkdir -p "$DEST/system/skills/defaults/marlin-hop"
    cp -R "$REF_HOP/scripts" "$DEST/system/skills/defaults/marlin-hop/" 2>/dev/null || true
    cp "$REF_HOP/SKILL.md" "$DEST/system/skills/defaults/marlin-hop/" 2>/dev/null || true
  fi
  python3 "$HOLDING_INSTALL/seed_company_hop_data.py" \
    --dest "$DEST" \
    --budget "$BUDGET" \
    --tech "$TECH" \
    --budget-json "$BUDGET_JSON"
  # Re-apply so agents.tsv gets budget overrides + always-max plan/doc roles
  python3 "$HOLDING_INSTALL/apply_budget_harness.py" \
    --dest "$DEST" --budget "$BUDGET" --budget-json "$BUDGET_JSON"
  echo "[create-company] bootstrapped hop scripts + company-local hop data"
else
  echo "[create-company] warn: no reference hop at $REF_HOP" >&2
fi

# Budget low: prefer Express over Nest for skills tags unless user only asked nest
SKILLS_TECH="$TECH"
if [[ "$BUDGET" == "low" ]]; then
  SKILLS_TECH="$(echo "$TECH" | sed -E 's/(^|[, ])nestjs([, ]|$)/\1express\2/g; s/(^|[, ])nest([, ]|$)/\1express\2/g')"
  echo "[create-company] budget=low skills-tech remapped: $SKILLS_TECH"
fi

# Copy matching skills-library customs by --tech (+ ba/po/qc/design baselines)
python3 "$HOLDING_INSTALL/copy_library_skills.py" \
  --dest "$DEST" \
  --tech "$SKILLS_TECH" \
  --library "$AGENTS_HOME/templates/skills-library"

# Seed express-react starter into project root when budget=low and UI+backend-ish
STARTER="$AGENTS_HOME/templates/starters/express-react"
if [[ "$BUDGET" == "low" && -d "$STARTER" ]]; then
  if echo "$TECH_L" | grep -Eq 'react|frontend|typescript|javascript|express|nestjs|node|backend'; then
    PROJECT_DIR="$(cd "$DEST/../.." && pwd)"
    # Only seed if project looks empty of app code
    if [[ ! -d "$PROJECT_DIR/backend" && ! -d "$PROJECT_DIR/apps" && ! -d "$PROJECT_DIR/frontend" ]]; then
      if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude '.DS_Store' "$STARTER/" "$PROJECT_DIR/"
      else
        cp -R "$STARTER/." "$PROJECT_DIR/"
      fi
      echo "[create-company] seeded starter express-react into $PROJECT_DIR"
    fi
  fi
fi

if [[ -f "$REF_INSTALL/company_os.sh" ]]; then
  cp "$REF_INSTALL/company_os.sh" "$DEST/system/install/company_os.sh"
  chmod +x "$DEST/system/install/company_os.sh"
  echo "[create-company] installed company_os.sh"
fi

# Frontend customs stub only if library seed did not already write TASK_SKILLS
if [[ -d "$DEST/system/staffs/frontend" ]]; then
  CUST="$DEST/system/skills/customs/frontend/frontend-engineer"
  mkdir -p "$CUST"
  if [[ ! -f "$CUST/TASK_SKILLS.json" ]]; then
    cat > "$CUST/TASK_SKILLS.json" <<EOF
{
  "role": "frontend-engineer",
  "default_skill": "",
  "customs_root": ".agents/${SLUG}/system/skills/customs/frontend/frontend-engineer",
  "note": "Add <skill>/SKILL.md folders freely; append tasks[] here. No script edits.",
  "tasks": []
}
EOF
  fi
fi

cat > "$DEST/CTO_TECH_SEED.md" <<EOF
# CTO tech seed — $TITLE

**Budget:** $BUDGET
**Hints from holding/user:** ${TECH:-_(none)_}
**Skills tags used:** ${SKILLS_TECH:-_(none)_}

CTO: propose tech teams and \`system/skills/customs/<team>/<role>/\` skills next.
If UI-heavy, keep design staffs (design-lead, ux-writer, ui-designer) and
use ba-user for design intake → canonical brief.
Do not invent stack the user did not ask for.

## Budget policy

- **low:** prefer Express+Vite starter if seeded; **one** API unit suite + **one** FE RTL smoke; **no e2e** unless user asks. Load **one** customs skill per IC.
- **medium/high:** Nest or richer stacks OK; more tests OK.
EOF

cat > "$DEST/COMPANY_BOOT.md" <<EOF
# $TITLE — boot (keep short)

User channel: \`ceo\` / \`ba-user\` only.

Scripts: \`.agents/$SLUG/system/skills/defaults/marlin-hop/scripts/\`

0. **Always** \`task_cache.py show\` first (active pointer). Same goal → resume
   cached role. New goal → \`clear\` then set.
1. **Memory — ALWAYS index first** (per-staff table; mandatory):
   \`\`\`bash
   python3 …/task_memory.py index --staff <ic> --path <file> [--goal '…']
   \`\`\`
   - \`mode=new\` → start fresh (no get). When finished **MUST**
     \`record-done --staff <ic> …\` (creates cache).
   - \`mode=candidates\` → pick a key whose \`short_descript\` **fits this ask**
     (equivalent tasks OK — not identical). If none fit → treat as new.
     If one fits → \`get --staff <ic> --key <key>\` → use \`work\`. If changed,
     **MUST** \`record-done\` again (upsert **overwrites**).
   - Each IC only \`--staff\` = own \`name:\` (e.g. ux-writer ≠ rest-api-dev).
2. Assign **one** IC. Do **not** read all of ORG or all customs.
3. IC loads **at most one** customs \`SKILL.md\`. Prefer seeded \`backend/\` + \`frontend/\`.
4. After assign: \`task_cache.py set --goal '...' --path '...' --role <ic>\`
5. Multi-company / hire → holding \`holding-ceo\`.
6. Budget **low** tests: minimal API unit + one RTL smoke; skip e2e unless asked.

\`task_cache\` = current task pointer (JSON).
\`task_memory\` = durable per-staff SQLite at \`cache/cache/task_memory.sqlite\`
(created on first index/record; local/gitignored).

**Why cache:** later passes reuse a **fitting** prior (equivalent ask) to cut
tokens/time on known fails/fixes. First pass ≈ normal work + a little for
\`record-done\` — not 2–3×. Never dump long essays into cache.

**Staff I/O:** stdout TSV only. Fields: \`key\`, \`short_descript\`, \`work\`.
Forbidden: open \`*.sqlite\`, other staff tables, or \`dump\` (needs \`--i-am-human\`).
EOF

# Seed task_cache pointer so CEO resume works immediately
TC="$DEST/system/skills/defaults/marlin-hop/scripts/task_cache.py"
if [[ -f "$TC" ]]; then
  python3 "$TC" set     --goal "Company ready — wait for user product ask"     --path "backend/" --path "frontend/"     --role ceo     --note "Prefer task_cache resume; do not re-browse ORG/skills each turn." >/dev/null || true
  echo "[create-company] seeded task_cache"
fi

# Ensure task_memory CLI is present + executable (from hop-reference)
TM="$DEST/system/skills/defaults/marlin-hop/scripts/task_memory.py"
if [[ -f "$TM" ]]; then
  chmod +x "$TM"
  mkdir -p "$DEST/cache/cache"
  # Touch placeholder note only — DB is created on first index/record-done
  if [[ ! -f "$DEST/cache/cache/TASK_MEMORY.md" ]]; then
    cat > "$DEST/cache/cache/TASK_MEMORY.md" <<'NOTE'
# task_memory (local)

Purpose: save tokens/time on *later* passes (known fails/fixes).
First pass ≈ normal work + cheap record-done (compact lines) — not 2–3× cost.
`mode=candidates` → pick a key whose short_descript fits (equivalent OK, not
identical); get `work` and patch. If none fit → treat as new.

SQLite `task_memory.sqlite` is created on first `index` / `record-done`.
Per-staff tables (`staff_<name>`). Agents: index → (get?) → work → record-done.
Read CLI stdout only — never open the DB.
NOTE
  fi
  echo "[create-company] task_memory ready: $TM"
else
  echo "[create-company] warn: task_memory.py missing from hop-reference" >&2
fi

echo "[create-company] done: $DEST"
echo "[create-company] next: .agents/$SLUG/system/install/company_os.sh all"
echo "[create-company] then CTO refines teams from CTO_TECH_SEED.md"
