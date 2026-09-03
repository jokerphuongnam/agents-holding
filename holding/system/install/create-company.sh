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
TOPOLOGY="teams"
PACKAGES=""
DRY=0

usage() {
  cat <<'USAGE'
Create a subsidiary Company OS tree from templates/company.

  create-company.sh --name <slug> --budget low|medium|high […] \
    [--tech "a,b,c"] [--project-root <path>] \
    [--topology teams|companies] [--packages "frontend:react,backend:nestjs"] \
    [--dry-run]

Result:
  (default)           <agents-home>/<slug>-company/
  --project-root DIR  DIR/.agents/<slug>-company/

Topology (workspace layout):
  teams (default)  One company; --packages become tech teams + hop routes
                   under the same --project-root (monorepo-friendly).
  companies        Do not use this script alone for multi-package splits —
                   run create-workspace.sh --topology companies instead
                   (one --project-root per package; avoids adapter clobber).

Holding may live in-repo (.agents/holding) or system (~/.agents/holding).
Call path: shortage/budget → holding-ceo → holding-hr ↔ user → this script
  (or create-workspace.sh for multi-package parents).

Always-on staffs: ceo, cto, product-lead, ba-lead (+ ba-user, ba-workflow),
po-new/po-modify (optional po-lead), git, qc-lead, tech-lead (on seeded tech team).
Leads = dispatch/low; ba-user/ba-workflow = medium; po-* writers = xhigh.
Product: ceo→product-lead→ba-user→product-lead→(po-*)?→Result→ceo→eng.
Cross-team: always up to CEO; slim plan_dir+read (never paste full plans).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --budget) BUDGET="${2:-}"; shift 2 ;;
    --tech) TECH="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --topology) TOPOLOGY="${2:-}"; shift 2 ;;
    --packages) PACKAGES="${2:-}"; shift 2 ;;
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

TOPOLOGY="$(echo "$TOPOLOGY" | tr '[:upper:]' '[:lower:]')"
case "$TOPOLOGY" in
  teams) ;;
  companies)
    echo "error: --topology companies needs create-workspace.sh (one project-root per package)" >&2
    echo "hint: $HOLDING_INSTALL/create-workspace.sh --topology companies --parent <dir> --package …" >&2
    exit 2
    ;;
  *)
    echo "error: --topology must be teams|companies" >&2
    exit 2
    ;;
esac

# Merge package tech tags into TECH when user only passed --packages
if [[ -n "$PACKAGES" ]]; then
  PKG_TECH_EXTRA=""
  IFS=',' read -r -a _PKG_TECH_ARR <<< "$PACKAGES"
  for part in "${_PKG_TECH_ARR[@]}"; do
    part="$(echo "$part" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$part" ]] && continue
    if [[ "$part" == *:* ]]; then
      bit="${part#*:}"
    else
      bit="$(basename "$part")"
    fi
    if [[ -n "$PKG_TECH_EXTRA" ]]; then
      PKG_TECH_EXTRA="${PKG_TECH_EXTRA},${bit}"
    else
      PKG_TECH_EXTRA="$bit"
    fi
  done
  if [[ -n "$PKG_TECH_EXTRA" ]]; then
    if [[ -n "$TECH" ]]; then
      TECH="${TECH},${PKG_TECH_EXTRA}"
    else
      TECH="$PKG_TECH_EXTRA"
    fi
  fi
fi

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
echo "[create-company] topology=$TOPOLOGY packages=${PACKAGES:-—}"
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
# --packages path names force teams even when tech tags are thin
if [[ -n "$PACKAGES" ]]; then
  IFS=',' read -r -a _PKG_ARR <<< "$PACKAGES"
  for part in "${_PKG_ARR[@]}"; do
    part="$(echo "$part" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$part" ]] && continue
    path_part="${part%%:*}"
    path_part="$(echo "$path_part" | sed 's#^/*##;s#/*$##')"
    base="$(basename "$path_part" | tr '[:upper:]' '[:lower:]')"
    case "$base" in
      frontend|web|client|ui|app)
        seed_eng frontend-engineer "Frontend app code per CTO seed. Not design system." "frontend"
        ;;
      backend|server|api|services)
        seed_eng backend-engineer "Backend/API services per CTO seed. Cross-company API via holding." "backend"
        ;;
      mobile|ios|android)
        seed_eng mobile-engineer "Mobile app code per CTO seed. Not design system." "mobile"
        ;;
    esac
  done
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
  SEED_ARGS=(
    --dest "$DEST"
    --budget "$BUDGET"
    --tech "$TECH"
    --budget-json "$BUDGET_JSON"
  )
  if [[ -n "$PACKAGES" ]]; then
    SEED_ARGS+=(--packages "$PACKAGES")
  fi
  python3 "$HOLDING_INSTALL/seed_company_hop_data.py" "${SEED_ARGS[@]}"
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
**Topology:** $TOPOLOGY (packages under this root are **teams**, not sibling companies)
**Hints from holding/user:** ${TECH:-_(none)_}
**Packages:** ${PACKAGES:-_(none — infer from tech / CTO)_}
**Skills tags used:** ${SKILLS_TECH:-_(none)_}

CTO: propose tech teams and \`system/skills/customs/<team>/<role>/\` skills next.
If UI-heavy, keep design staffs (design-lead, ux-writer, ui-designer) and
use ba-user for design intake → canonical brief.
Do not invent stack the user did not ask for.

When **Packages** is set, treat each path as a team-owned slice (hop \`route.tsv\`
already maps those prefixes). Cross-package work stays **in-company**
(cto / tech-lead) — escalate to holding only for true multi-**company** work.

## Budget policy

- **low:** prefer Express+Vite starter if seeded; **one** API unit suite + **one** FE RTL smoke; **no e2e** unless user asks. Load **one** customs skill per IC.
- **medium/high:** Nest or richer stacks OK; more tests OK.
EOF

# Workspace registry (teams topology under this project root)
PARENT_FOR_WS=""
if [[ -n "$PROJECT_ROOT" ]]; then
  PARENT_FOR_WS="$PROJECT_ROOT"
else
  PARENT_FOR_WS="$(cd "$DEST/.." && pwd)"
fi
mkdir -p "$DEST/cache"
WS_COMPANY_TMPL="$AGENTS_HOME/templates/workspace/COMPANY_CACHE_WORKSPACE.md"
if [[ -f "$WS_COMPANY_TMPL" ]]; then
  TOPOLOGY="$TOPOLOGY" PARENT="$PARENT_FOR_WS" COMPANY_SLUG="$SLUG" \
  PACKAGES="${PACKAGES:-_(none)_}" \
  python3 - "$WS_COMPANY_TMPL" <<'PY' > "$DEST/cache/WORKSPACE.md"
import os, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
for key in ("TOPOLOGY", "PARENT", "COMPANY_SLUG", "PACKAGES"):
    text = text.replace("{{" + key + "}}", os.environ.get(key, ""))
sys.stdout.write(text)
PY
else
  cat > "$DEST/cache/WORKSPACE.md" <<EOF
# Workspace — $TITLE

| Field | Value |
| --- | --- |
| Topology | \`$TOPOLOGY\` |
| Company | \`$SLUG\` |
| Project root | \`$PARENT_FOR_WS\` |
| Packages | ${PACKAGES:-_(none)_} |

**teams:** one shared ceo/cto/BA/PO/QC/git; packages = tech teams only.
EOF
fi

cat > "$DEST/COMPANY_BOOT.md" <<EOF
# $TITLE — boot (keep short)

User channel: \`ceo\` / \`ba-user\` only.

Scripts: \`.agents/$SLUG/system/skills/defaults/marlin-hop/scripts/\`

0. **Always** \`task_cache.py show\` first. Same goal → resume. New goal → \`clear\` then set.
1. **Product:** CEO → **\`product-lead\`** first → \`ba-user\` (user talk) →
   \`product-lead\` → (\`po-new\`|\`po-modify\` if needed) → **## Result → CEO** → eng.
   Product-lead does **not** spawn eng.
2. **Cross-team (all roles):** need another team → always **up to CEO**, then CEO
   spawns down. Slim brief = goal + paths + optional \`plan_dir\` + \`read\` loci —
   **never** paste the full plan through the chain. Strict lane per staff.
3. **Memory (parent prefetch — required for savings):**
   \`\`\`bash
   python3 …/task_memory.py resolve --staff <ic> --path <file> [--goal '…'] --brief
   \`\`\`
   Paste that stdout into the IC brief.
   - \`mode=new\` → IC implements; **MUST** slim \`record-done\` (fails/fixes/refs only).
   - \`mode=reuse\` → IC applies fails/fixes/refs from the brief; **MUST NOT** call
     \`task_memory\` again; **SKIP** \`record-done\` unless a new fail/fix/refs was learned.
   - Each IC only \`--staff\` = own \`name:\`. Never full-file cache.
4. Assign **one** IC. Do **not** read all of ORG or all customs.
5. IC loads **at most one** customs \`SKILL.md\`. Prefer seeded \`backend/\` + \`frontend/\`.
6. After assign: \`task_cache.py set --goal '...' --path '...' --role <ic>\`
7. Multi-company / hire → holding \`holding-ceo\`.
8. Budget **low** tests: minimal API unit + one RTL smoke; skip e2e unless asked.

\`task_cache\` = active pointer. \`task_memory\` = per-staff SQLite
\`cache/cache/task_memory.sqlite\` (local/gitignored).

**Savings target:** after ~3 equivalent tasks, expect on the order of **~40%**
fewer tokens vs no-memory hops when CEO prefetches \`--brief\` and ICs skip
re-resolve/re-record (measured playground; first task still pays a small record cost).

**Staff I/O:** stdout TSV only. Forbidden: open \`*.sqlite\` / other staff tables / \`dump\`.
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

Purpose: cut tokens/time on *later equivalent* tasks (~40% after ~3 similar
hops when used correctly — first hop still pays a small record cost).

## Correct usage (do this)

1. CEO/lead: `task_memory.py resolve --staff <ic> --path … --goal … --brief`
2. Paste that brief into the IC spawn prompt.
3. `mode=reuse` → IC applies fails/fixes/refs only; **no** task_memory CLI;
   **SKIP** `record-done` unless a new fail/fix/refs was learned.
4. `mode=new` → IC implements; slim `record-done` with
   `fails|fixes|refs=file:start-end` and a *pattern* `short_descript`
   (e.g. Screens+List+nav empty-state) — never full files / unrelated chrome.

## Wrong usage (kills savings)

- IC re-runs resolve/record every hop
- Caching whole sibling files into `work`

SQLite: `task_memory.sqlite` (per-staff tables). Local/gitignored.
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
