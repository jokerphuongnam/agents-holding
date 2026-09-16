#!/usr/bin/env bash
# Create a **child company** under any parent Company OS (recursive).
#
# Same relationship as holding → company, nested:
#   holding → company → child → grandchild → …
# Each node only escalates to its immediate parent (never siblings).
# Children get read-only grants from the parent; created by parent ceo/cto
# (not holding-hr).
#
# Usage:
#   create-child-company.sh --parent .agents/pilot-company --name sdk-ios \
#     --budget low --project-root /path/to/package \
#     --grant-path documents/ [--placement nested|external]
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
CREATE_COMPANY="$HOLDING_INSTALL/create-company.sh"
CHILDREN_REG="$HOLDING_INSTALL/children_registry.py"
TMPL_CHILDREN="$AGENTS_HOME/templates/company/children"

PARENT=""
NAME=""
BUDGET="medium"
TECH=""
PROJECT_ROOT=""
PLACEMENT="nested"
DRY=0
GRANT_PATHS=()
GRANT_ARTIFACTS=()

usage() {
  cat <<'USAGE'
Create a child Company OS under a parent company (scoped context).

  create-child-company.sh --parent <parent-company-path> --name <slug> \
    --budget low|medium|high --project-root <code-root> \
    [--tech "a,b"] [--grant-path PATH]… [--grant-artifact FILE]… \
    [--placement nested|external] [--dry-run]

Layout (nested, default):
  <parent>/children/<stem>/
    GRANTS.toml
    META.toml
    <stem>-company/          # full Company OS

external: Company OS at <project-root>/.agents/<stem>-company/
          GRANTS/META still under parent/children/<stem>/

Invariants:
  - Full formula (own ceo, BA, PO, …)
  - No sibling hops — escalate to parent ceo
  - Context = own project-root + GRANTS read-only slices
  - Not registered in holding companies.sqlite (parent children.sqlite instead)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --budget) BUDGET="${2:-}"; shift 2 ;;
    --tech) TECH="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --placement) PLACEMENT="${2:-}"; shift 2 ;;
    --grant-path) GRANT_PATHS+=("${2:-}"); shift 2 ;;
    --grant-artifact) GRANT_ARTIFACTS+=("${2:-}"); shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$PARENT" || -z "$NAME" || -z "$PROJECT_ROOT" ]]; then
  echo "error: --parent, --name, and --project-root are required" >&2
  usage
  exit 2
fi

PARENT="$(cd "$PARENT" && pwd)"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if [[ ! -d "$PARENT/system" ]]; then
  echo "error: --parent is not a Company OS tree: $PARENT" >&2
  exit 1
fi

PLACEMENT="$(echo "$PLACEMENT" | tr '[:upper:]' '[:lower:]')"
case "$PLACEMENT" in
  nested|external) ;;
  *) echo "error: --placement must be nested|external" >&2; exit 2 ;;
esac

STEM="$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]/-/g')"
STEM="${STEM%-company}"
SLUG="${STEM}-company"
PARENT_SLUG="$(basename "$PARENT")"
CHILD_META_DIR="$PARENT/children/$STEM"
GRANTS_FILE="$CHILD_META_DIR/GRANTS.toml"
META_FILE="$CHILD_META_DIR/META.toml"

if [[ "$PLACEMENT" == "nested" ]]; then
  DEST="$CHILD_META_DIR/$SLUG"
else
  DEST="$PROJECT_ROOT/.agents/$SLUG"
fi

echo "[create-child] parent=$PARENT ($PARENT_SLUG)"
echo "[create-child] child=$SLUG placement=$PLACEMENT"
echo "[create-child] dest=$DEST"
echo "[create-child] project-root=$PROJECT_ROOT"
echo "[create-child] grants=${GRANT_PATHS[*]:-none} artifacts=${GRANT_ARTIFACTS[*]:-none}"

# Gate: only companies with hr may own / run child-org flows (hr manages the portfolio).
# If missing: escalate to the HR *above* to hire hr (+ manage-children) here first.
HR_STAFF="$PARENT/system/staffs/cross-cut/hr.md"
HR_SKILL_NEW="$PARENT/system/skills/customs/cross-cut/hr/manage-children/SKILL.md"
HR_SKILL_OLD="$PARENT/system/skills/customs/cross-cut/hr/hire-children/SKILL.md"
if [[ ! -f "$HR_STAFF" ]]; then
  echo "error: parent has no hr — no child-org flows until hr owns this portfolio" >&2
  echo "escalate: HR one level up must hire role \`hr\` (+ manage-children) into: $PARENT" >&2
  if [[ "$PARENT" == */children/*/*-company ]]; then
    echo "escalate_to: parent company hr (ceo → hr)" >&2
  else
    echo "escalate_to: holding-hr (via holding-ceo)" >&2
  fi
  echo "after_lock: upper HR writes staffs/cross-cut/hr.md + customs/…/hr/manage-children/" >&2
  echo "note: hr manages children (approve/create/grants/staff) — not hiring only" >&2
  echo "dev_only: python3 $HOLDING_INSTALL/seed_parent_hr.py --parent $PARENT" >&2
  exit 1
fi
if [[ ! -f "$HR_SKILL_NEW" && ! -f "$HR_SKILL_OLD" ]]; then
  echo "error: parent hr missing manage-children skill (child portfolio skill)" >&2
  echo "escalate: install manage-children under customs/cross-cut/hr/" >&2
  echo "dev_only: python3 $HOLDING_INSTALL/seed_parent_hr.py --parent $PARENT" >&2
  exit 1
fi
echo "[create-child] parent hr OK (child portfolio owner)"

if [[ "$DRY" -eq 1 ]]; then
  echo "[create-child] dry-run OK (no write)"
  exit 0
fi

if [[ -e "$DEST" ]]; then
  echo "error: already exists: $DEST" >&2
  exit 1
fi

mkdir -p "$CHILD_META_DIR"
# Seed children README once
if [[ ! -f "$PARENT/children/README.md" && -f "$TMPL_CHILDREN/README.md" ]]; then
  cp "$TMPL_CHILDREN/README.md" "$PARENT/children/README.md"
fi

# Write GRANTS.toml (SoT)
{
  echo "# Generated by create-child-company.sh — edit grants as needed."
  echo
  echo "[grants]"
  echo "paths_readonly = ["
  if [[ ${#GRANT_PATHS[@]} -eq 0 ]]; then
    echo "  # add paths relative to parent project root"
  else
    for p in "${GRANT_PATHS[@]}"; do
      printf '  "%s",\n' "$p"
    done
  fi
  echo "]"
  echo "artifacts = ["
  if [[ ${#GRANT_ARTIFACTS[@]} -gt 0 ]]; then
    for a in "${GRANT_ARTIFACTS[@]}"; do
      printf '  "%s",\n' "$a"
    done
  fi
  echo "]"
  echo
  echo "[policy]"
  echo "sibling_hop = false"
  echo "parent_channel = \"ceo\""
  echo "scan_parent_tree = false"
} > "$GRANTS_FILE"

NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
{
  echo "# Child metadata (SoT pointer)"
  echo "slug = \"$SLUG\""
  echo "parent_slug = \"$PARENT_SLUG\""
  echo "placement = \"$PLACEMENT\""
  echo "budget = \"$BUDGET\""
  echo "project_root = \"$PROJECT_ROOT\""
  echo "company_path = \"$DEST\""
  echo "created_at = \"$NOW\""
} > "$META_FILE"

# Create full Company OS via factory (skip holding registry)
CREATE_ARGS=(
  --name "$STEM"
  --budget "$BUDGET"
  --dest "$DEST"
  --project-root "$PROJECT_ROOT"
  --no-register
)
if [[ -n "$TECH" ]]; then
  CREATE_ARGS+=(--tech "$TECH")
fi
"$CREATE_COMPANY" "${CREATE_ARGS[@]}"

# Child hop routes + hard scope fence: ONLY child company folder + package.
# Grants are RO reference — not hop targets. Out-of-scope hop → parent ceo.
CHILD_DATA="$DEST/system/skills/defaults/marlin-hop/data"
mkdir -p "$CHILD_DATA"
PKG_BASENAME="$(basename "$PROJECT_ROOT")"
ROUTE="$CHILD_DATA/route.tsv"
{
  echo -e "prefix\tagent"
  echo -e "src/\ttech-lead"
  echo -e "${PKG_BASENAME}/\ttech-lead"
  echo -e "system/\tceo"
  echo -e "cache/plans/\tpo-modify"
} > "$ROUTE"
# Allowlist enforced by hop.py (scope_allow.tsv + parent.tsv)
{
  echo -e "prefix"
  echo -e "src/"
  echo -e "${PKG_BASENAME}/"
  echo -e "system/"
  echo -e "cache/"
  echo -e "COMPANY_BOOT.md"
  echo -e "COMPANY.md"
  echo -e "CTO_TECH_SEED.md"
  echo -e "FORMULA.md"
  echo -e "README.md"
} > "$CHILD_DATA/scope_allow.tsv"
REL_PARENT="$PARENT"
if REL_TRY="$(python3 -c "import os; print(os.path.relpath('$PARENT', '$DEST'))" 2>/dev/null)"; then
  REL_PARENT="$REL_TRY"
fi
{
  echo -e "key\tvalue"
  echo -e "slug\t$PARENT_SLUG"
  echo -e "company_path\t$REL_PARENT"
  echo -e "channel\tceo"
} > "$CHILD_DATA/parent.tsv"
echo "[create-child] scoped route + scope_allow + parent.tsv (fence → escalate parent)"

# Tool-level SCOPE.md + ensure scope_guard.py present on child hop scripts
REF_SCOPE="$AGENTS_HOME/templates/hop-reference/scripts/scope_guard.py"
CHILD_SCRIPTS="$DEST/system/skills/defaults/marlin-hop/scripts"
if [[ -f "$REF_SCOPE" ]]; then
  cp "$REF_SCOPE" "$CHILD_SCRIPTS/scope_guard.py"
  cp "$AGENTS_HOME/templates/hop-reference/scripts/common.py" "$CHILD_SCRIPTS/common.py" 2>/dev/null || true
fi
if [[ -f "$CHILD_SCRIPTS/scope_guard.py" ]]; then
  python3 "$CHILD_SCRIPTS/scope_guard.py" --company "$DEST" write-scope-md \
    || echo "[create-child] warn: SCOPE.md not written" >&2
fi

# Parent children.tsv — token-cheap hop: path → child ceo handoff (not child ICs)
PARENT_DATA="$PARENT/system/skills/defaults/marlin-hop/data"
mkdir -p "$PARENT_DATA"
CHILDREN_TSV="$PARENT_DATA/children.tsv"
# Relative pointers from parent company root when possible
REL_CHILD="$DEST"
if REL_TRY="$(python3 -c "import os; print(os.path.relpath('$DEST', '$PARENT'))" 2>/dev/null)"; then
  REL_CHILD="$REL_TRY"
fi
if [[ ! -f "$CHILDREN_TSV" ]]; then
  echo -e "prefix\tslug\tcompany_path" > "$CHILDREN_TSV"
fi
# Upsert rows for this child (package prefix + children/<stem>/)
python3 - "$CHILDREN_TSV" "$PKG_BASENAME" "$STEM" "$SLUG" "$REL_CHILD" <<'PY'
import sys
from pathlib import Path
path, pkg, stem, slug, cpath = sys.argv[1:6]
p = Path(path)
lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
header = lines[0] if lines else "prefix\tslug\tcompany_path"
rows = [ln for ln in lines[1:] if ln.strip()]
keep = []
for ln in rows:
    cols = ln.split("\t")
    if len(cols) >= 2 and cols[1] == slug:
        continue
    keep.append(ln)
for pref in (f"{pkg}/", f"children/{stem}/"):
    keep.append(f"{pref}\t{slug}\t{cpath}")
p.write_text(header + "\n" + "\n".join(keep) + "\n", encoding="utf-8")
PY
echo "[create-child] parent children.tsv ← $SLUG"

# Ensure parent hop.py knows children handoff (refresh from templates if stale)
HOP_PY="$PARENT/system/skills/defaults/marlin-hop/scripts/hop.py"
REF_HOP="$AGENTS_HOME/templates/hop-reference/scripts/hop.py"
if [[ -f "$REF_HOP" ]]; then
  cp "$REF_HOP" "$HOP_PY"
  REF_SCRIPTS="$(dirname "$REF_HOP")"
  cp "$REF_SCRIPTS/common.py" "$(dirname "$HOP_PY")/common.py" 2>/dev/null || true
  cp "$REF_SCRIPTS/scope_guard.py" "$(dirname "$HOP_PY")/scope_guard.py" 2>/dev/null || true
  # Keep generic self_test if seed softened it
  if [[ -f "$HOLDING_INSTALL/seed_company_hop_data.py" ]]; then
    PYTHONPATH="$HOLDING_INSTALL${PYTHONPATH:+:$PYTHONPATH}" python3 - <<PY
from pathlib import Path
from seed_company_hop_data import soften_hop_self_test
p = Path("$HOP_PY")
t = p.read_text(encoding="utf-8")
n = soften_hop_self_test(t)
if n != t:
    p.write_text(n, encoding="utf-8")
PY
  fi
  echo "[create-child] refreshed parent hop.py (child handoff)"
fi

# Child boot addendum
BOOT="$DEST/COMPANY_BOOT.md"
if [[ -f "$BOOT" ]]; then
  cat >> "$BOOT" <<EOF

---

## Child of \`$PARENT_SLUG\` (scoped)

Same relationship as a **company under holding**, nested (you may own further children).

### Flow (token-cheap)

1. **Parent ceo** hops here with a short goal only (handoff → you, the child ceo).
2. **You (child ceo)** hop your own staffs for work **inside this company folder**
   (\`$DEST\`) and your package root (\`$PROJECT_ROOT\`).
3. Need more parent docs/API/context → escalate to **parent ceo** (\`$PARENT_SLUG\`)
   and ask for additional **grants/info** — do not crawl the parent tree yourself.
4. Need more **people** (or your own children / hr) → escalate to parent ceo →
   parent **hr** (\`manage-children\`). Do not hire into your own staffs without lock.

### Scope (hard fence)

- Allowed roots: see \`SCOPE.md\` (company folder + package root only).
- **Before** reading any path outside cwd:
  \`python3 system/skills/defaults/marlin-hop/scripts/scope_guard.py check --path <path>\`
  - Own roots → read/write
  - Paths in \`$GRANTS_FILE\` → **read-only** (\`handoff: grant_read\`)
  - Else deny (\`handoff: parent\`) → spawn parent ceo for more grants/info
- Do **not** write under grant paths; do **not** open ungated parent/sibling trees.
- No sibling hops. No holding-ceo unless the product-root parent escalates upward.

Create deeper children: \`create-child-company.sh --parent $DEST …\`
Parent inventory: \`children_registry.py --parent $PARENT list\`
EOF
  echo "[create-child] patched COMPANY_BOOT.md"
fi

# Parent boot pointer (once)
PBOOT="$PARENT/COMPANY_BOOT.md"
if [[ -f "$PBOOT" ]] && ! grep -q '## Children (scoped)' "$PBOOT" 2>/dev/null; then
  cat >> "$PBOOT" <<EOF

---

## Children (scoped)

Same relationship as **holding → company**, nested under this company.

### Flow (max token savings)

1. You (**ceo**) run hop on the path/ask.
2. If \`handoff: child\` → spawn **only that child company's ceo** with a short goal.
   Do **not** open child ORG/staffs or spawn child ICs from here.
3. Child ceo hops its own staffs inside the child folder; may escalate back to you
   to request more grants/info for its coding team.

- Inventory: \`python3 $CHILDREN_REG --parent $PARENT list\`
- Table: \`system/skills/defaults/marlin-hop/data/children.tsv\`
- Create: \`create-child-company.sh --parent $PARENT --name …\`
- **HR owns the child portfolio:** role \`hr\` + skill \`manage-children\` required
  first (\`seed_parent_hr.py\` or upper HR hire). Without hr there is **no**
  create/read/approve-child flow. Org asks (new child, grants, staffing) → Assign **hr**.
  Product path hop still handoffs to **child ceo** (token-cheap).
EOF
  echo "[create-child] patched parent COMPANY_BOOT.md"
elif [[ -f "$PBOOT" ]] && ! grep -q 'handoff: child' "$PBOOT" 2>/dev/null; then
  cat >> "$PBOOT" <<EOF

### Child handoff (token-cheap)

Hop may print \`handoff: child\` + \`child_company\`. Spawn **only** that child ceo
with a short goal — never deep-spawn child staffs from the parent.
Child **org** (create/grants/staff) → Assign \`hr\` (\`manage-children\`).
EOF
fi

if [[ -f "$PBOOT" ]] && grep -q '## Children (scoped)' "$PBOOT" && ! grep -q 'manage-children' "$PBOOT" 2>/dev/null; then
  cat >> "$PBOOT" <<EOF

### Parent HR (portfolio)

Child-org flows exist only with \`hr\` + \`manage-children\`. HR approves/creates
children, reads inventory, coordinates grants, and staffs children — not hiring only.
EOF
fi

# Register in parent children.sqlite
python3 "$CHILDREN_REG" --parent "$PARENT" register \
  --slug "$SLUG" \
  --project-root "$PROJECT_ROOT" \
  --company-path "$DEST" \
  --grants-path "$GRANTS_FILE" \
  --meta-path "$META_FILE" \
  --budget "$BUDGET" \
  --placement "$PLACEMENT" \
  --note "create-child-company" \
  || echo "[create-child] warn: children_registry register failed" >&2

# Fingerprint defaults for later update-company
UPD="$HOLDING_INSTALL/update_company_defaults.py"
if [[ -f "$UPD" ]]; then
  PYTHONPATH="$HOLDING_INSTALL${PYTHONPATH:+:$PYTHONPATH}" \
    python3 "$UPD" --write-manifest-only "$DEST" --agents-home "$AGENTS_HOME" --budget "$BUDGET" \
    || true
fi

# Company SoT: launch.sh + README.md (usage how-to). No package-root launcher.
STEM="${SLUG%-company}"
WRITE_LAUNCH="$HOLDING_INSTALL/write_company_launch.sh"
WRITE_README="$HOLDING_INSTALL/write_company_readme.sh"
if [[ -x "$WRITE_LAUNCH" ]]; then
  bash "$WRITE_LAUNCH" --company-dir "$DEST" --package-root "$PROJECT_ROOT" || true
fi
if [[ -x "$WRITE_README" ]]; then
  bash "$WRITE_README" --company-dir "$DEST" --package-root "$PROJECT_ROOT" --title "$STEM company" || true
fi
# Seed empty aliases file for parent→child fuzzy launch
ALIAS="$DEST/system/skills/defaults/marlin-hop/data/children_aliases.tsv"
if [[ ! -f "$ALIAS" ]]; then
  mkdir -p "$(dirname "$ALIAS")"
  printf 'alias\tslug\n' > "$ALIAS"
fi

echo "[create-child] done: $DEST"
echo "[create-child] grants: $GRANTS_FILE"
echo "[create-child] placement: ${PLACEMENT:-nested}"
echo "[create-child] next: $DEST/system/install/company_os.sh all"
echo "[create-child] then (company SoT): $DEST/launch.sh grok|claude|codex|merge \"prompt\""
echo "[create-child] parent wake child: <parent>/launch.sh grok $STEM \"prompt\""
echo "[create-child] docs: agents-holding docs/ceo-launch-and-children.md"
echo "[create-child] list: python3 $CHILDREN_REG --parent $PARENT list"
