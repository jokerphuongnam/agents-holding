#!/usr/bin/env bash
# Create a **child** Company OS — same as create-company.sh, plus --parent.
#
# Preferred UX (identical flags to create-company, parent first):
#   create-company.sh --parent <parent-company> --name <slug> --budget … --project-root …
#   create-child-company.sh --parent <parent-company> --name <slug> --budget … --project-root …
#
# Wires parent↔child at create time: META/GRANTS, children.sqlite, parent.tsv,
# launch.sh, company README.md. Never hand-scaffold.
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
CREATE_COMPANY="$HOLDING_INSTALL/create-company.sh"
CHILDREN_REG="$HOLDING_INSTALL/children_registry.py"
TMPL_CHILDREN="$AGENTS_HOME/templates/company/children"
BUDGET_JSON="$HOLDING_INSTALL/budget_tiers.json"

PARENT=""
NAME=""
BUDGET="medium"
TECH=""
PROJECT_ROOT=""
PLACEMENT="external"
DRY=0
PACKAGES=""
FAMILY=""
GRANT_PATHS=()
GRANT_ARTIFACTS=()

usage() {
  cat <<'USAGE'
Create a child Company OS under a parent (full company mirror).

Same as create-company.sh — only difference: --parent is required and the
parent link (META/GRANTS/registry/parent.tsv) is attached at create time.

  create-child-company.sh --parent <parent-company-path> --name <slug> \
    --budget low|medium|high --project-root <code-root> \
    [--tech "a,b"] [--packages "frontend:react,backend:nestjs"] [--family chat] \
    [--placement nested|external] \
    [--grant-path PATH]… [--grant-artifact FILE]… \
    [--dry-run]

  # Equivalent preferred entry:
  create-company.sh --parent <parent-company-path> --name <slug> … (same flags)

Defaults:
  --placement external   Company OS at <project-root>/.agents/<slug>-company/
  --placement nested     Company OS under <parent>/children/<stem>/<slug>-company/

Parent always keeps: <parent>/children/<stem>/{META.toml,GRANTS.toml}

Invariants:
  - Full formula (own ceo, BA, PO, …) — same as create-company
  - Escalate to parent ceo (not holding); no sibling hops
  - Context = project-root RW + GRANTS RO
  - Registered in parent children.sqlite (not holding companies.sqlite)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --budget) BUDGET="${2:-}"; shift 2 ;;
    --tech) TECH="${2:-}"; shift 2 ;;
    --packages) PACKAGES="${2:-}"; shift 2 ;;
    --family) FAMILY="${2:-}"; shift 2 ;;
    --project-root) PROJECT_ROOT="${2:-}"; shift 2 ;;
    --placement) PLACEMENT="${2:-}"; shift 2 ;;
    --grant-path) GRANT_PATHS+=("${2:-}"); shift 2 ;;
    --grant-artifact) GRANT_ARTIFACTS+=("${2:-}"); shift 2 ;;
    --dry-run) DRY=1; shift ;;
    # Accept create-company flags for UX parity (child layout uses --placement)
    --no-register)
      echo "[create-child] note: ignoring --no-register (child uses parent children.sqlite)" >&2
      shift
      ;;
    --dest|--topology)
      echo "[create-child] note: ignoring $1 (use --placement nested|external + --project-root)" >&2
      shift 2
      ;;
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
mkdir -p "$PROJECT_ROOT"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if [[ ! -d "$PARENT/system" ]]; then
  echo "error: --parent is not a Company OS tree: $PARENT" >&2
  exit 1
fi

BUDGET="$(python3 "$HOLDING_INSTALL/apply_budget_harness.py" \
  --budget "$BUDGET" --budget-json "$BUDGET_JSON" --normalize-only)"
case "$BUDGET" in
  low|medium|high) ;;
  *) echo "error: --budget must be low|medium|high" >&2; exit 2 ;;
esac

PLACEMENT="$(echo "$PLACEMENT" | tr '[:upper:]' '[:lower:]')"
case "$PLACEMENT" in
  nested|external) ;;
  *) echo "error: --placement must be nested|external" >&2; exit 2 ;;
esac

# Merge --packages tech tags into TECH (same as create-company)
if [[ -n "$PACKAGES" ]]; then
  IFS=',' read -r -a _PKG_TECH_ARR <<< "$PACKAGES"
  for part in "${_PKG_TECH_ARR[@]}"; do
    part="$(echo "$part" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$part" ]] && continue
    if [[ "$part" == *:* ]]; then
      bit="${part#*:}"
    else
      bit="$(basename "$part")"
    fi
    if [[ -n "$TECH" ]]; then TECH="$TECH,$bit"; else TECH="$bit"; fi
  done
fi

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
echo "[create-child] tech=${TECH:-none} family=${FAMILY:-none}"
echo "[create-child] grants=${GRANT_PATHS[*]:-none} artifacts=${GRANT_ARTIFACTS[*]:-none}"

if [[ "$DRY" -eq 1 ]]; then
  echo "[create-child] dry-run — no writes"
  exit 0
fi

# Gate: parent must have hr + manage-children
HR_STAFF="$PARENT/system/staffs/cross-cut/hr.md"
HR_SKILL_NEW="$PARENT/system/skills/customs/cross-cut/hr/manage-children/SKILL.md"
HR_SKILL_OLD="$PARENT/system/skills/customs/cross-cut/hr/hire-children/SKILL.md"
if [[ ! -f "$HR_STAFF" ]]; then
  echo "error: parent lacks hr staff ($HR_STAFF)" >&2
  echo "escalate: hire hr + manage-children on parent first" >&2
  echo "dev_only: python3 $HOLDING_INSTALL/seed_parent_hr.py --parent $PARENT" >&2
  exit 1
fi
if [[ ! -f "$HR_SKILL_NEW" && ! -f "$HR_SKILL_OLD" ]]; then
  echo "error: parent lacks manage-children skill" >&2
  echo "dev_only: python3 $HOLDING_INSTALL/seed_parent_hr.py --parent $PARENT" >&2
  exit 1
fi

mkdir -p "$CHILD_META_DIR"
mkdir -p "$(dirname "$DEST")"

# Seed children README once
if [[ ! -f "$PARENT/children/README.md" && -f "$TMPL_CHILDREN/README.md" ]]; then
  cp "$TMPL_CHILDREN/README.md" "$PARENT/children/README.md"
fi

# GRANTS.toml
{
  echo "# Child RO grants from parent — edit with hr+ceo lock"
  echo ""
  echo "[grants]"
  echo "paths_readonly = ["
  for g in "${GRANT_PATHS[@]+"${GRANT_PATHS[@]}"}"; do
    echo "  \"$g\","
  done
  echo "]"
  echo "artifacts = ["
  for a in "${GRANT_ARTIFACTS[@]+"${GRANT_ARTIFACTS[@]}"}"; do
    echo "  \"$a\","
  done
  echo "]"
  echo ""
  echo "[policy]"
  echo "sibling_hop = false"
  echo "parent_channel = \"ceo\""
  echo "scan_parent_tree = false"
} > "$GRANTS_FILE"

# META.toml — parent attached at create time
{
  echo "# Child metadata (SoT pointer)"
  echo "slug = \"$SLUG\""
  echo "parent_slug = \"$PARENT_SLUG\""
  echo "placement = \"$PLACEMENT\""
  echo "budget = \"$BUDGET\""
  echo "project_root = \"$PROJECT_ROOT\""
  echo "company_path = \"$DEST\""
  echo "created_at = \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\""
} > "$META_FILE"

# Full company tree — same create-company path
CREATE_ARGS=(
  --name "$STEM"
  --budget "$BUDGET"
  --dest "$DEST"
  --project-root "$PROJECT_ROOT"
  --no-register
)
[[ -n "$TECH" ]] && CREATE_ARGS+=(--tech "$TECH")
[[ -n "$PACKAGES" ]] && CREATE_ARGS+=(--packages "$PACKAGES")
[[ -n "$FAMILY" ]] && CREATE_ARGS+=(--family "$FAMILY")

"$CREATE_COMPANY" "${CREATE_ARGS[@]}"

# --- Attach parent into child hop / docs (same moment as create) ---
CHILD_DATA="$DEST/system/skills/defaults/marlin-hop/data"
mkdir -p "$CHILD_DATA"
PKG_BASENAME="$(basename "$PROJECT_ROOT")"

# scope_allow + parent.tsv (fence → parent ceo)
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
  echo -e "PARENT.md"
  echo -e "SCOPE.md"
} > "$CHILD_DATA/scope_allow.tsv"

REL_PARENT="$(python3 -c "import os; print(os.path.relpath('$PARENT', '$DEST'))")"
{
  echo -e "key\tvalue"
  echo -e "slug\t$PARENT_SLUG"
  echo -e "company_path\t$REL_PARENT"
  echo -e "channel\tceo"
} > "$CHILD_DATA/parent.tsv"

# Parent children.tsv for hop handoff
PARENT_DATA="$PARENT/system/skills/defaults/marlin-hop/data"
mkdir -p "$PARENT_DATA"
CHILDREN_TSV="$PARENT_DATA/children.tsv"
if [[ ! -f "$CHILDREN_TSV" ]]; then
  echo -e "prefix\tslug\tcompany_path" > "$CHILDREN_TSV"
fi
REL_CHILD="$(python3 -c "import os; print(os.path.relpath('$DEST', '$PARENT'))")"
# upsert-ish: append if slug missing
if ! grep -q $'\t'"$SLUG"$'\t' "$CHILDREN_TSV" 2>/dev/null; then
  {
    echo -e "${PKG_BASENAME}/\t$SLUG\t$REL_CHILD"
    echo -e "children/${STEM}/\t$SLUG\t$REL_CHILD"
    echo -e "projects/${STEM}/\t$SLUG\t$REL_CHILD"
  } >> "$CHILDREN_TSV"
fi

# PARENT.md inside child
cat > "$DEST/PARENT.md" <<EOF
# Parent link

This company is a **full Company OS** (same formula as create-company).

| | |
|--|--|
| Parent | \`$PARENT_SLUG\` |
| Parent portfolio | \`$CHILD_META_DIR\` (\`META.toml\`, \`GRANTS.toml\`) |
| Parent channel | \`ceo\` |
| Placement | \`$PLACEMENT\` |
| Company path | \`$DEST\` |
| Package root | \`$PROJECT_ROOT\` |

Escalate missing docs/grants/hire → parent **ceo** (not holding).
Product work: parent \`launch.sh grok $STEM "…"\` or this company's \`launch.sh\`.
EOF

# SCOPE.md
cat > "$DEST/SCOPE.md" <<EOF
# SCOPE — $SLUG

## allow_rw
- \`$PROJECT_ROOT\`
- This company OS: \`$DEST\`

## allow_ro
See parent portfolio \`$GRANTS_FILE\`.

## deny
- Parent ungated trees; sibling children
- Parent \`src/\` unless granted

## Escalation
Child ceo → parent **$PARENT_SLUG** ceo (not holding).
EOF

# launch.sh + company README (usage)
WRITE_LAUNCH="$HOLDING_INSTALL/write_company_launch.sh"
WRITE_README="$HOLDING_INSTALL/write_company_readme.sh"
[[ -x "$WRITE_LAUNCH" ]] && bash "$WRITE_LAUNCH" --company-dir "$DEST" --package-root "$PROJECT_ROOT" || true
[[ -x "$WRITE_README" ]] && bash "$WRITE_README" --company-dir "$DEST" --package-root "$PROJECT_ROOT" --title "$STEM company" || true

ALIAS="$DEST/system/skills/defaults/marlin-hop/data/children_aliases.tsv"
if [[ ! -f "$ALIAS" ]]; then
  mkdir -p "$(dirname "$ALIAS")"
  printf 'alias\tslug\n' > "$ALIAS"
fi
# seed fuzzy aliases for this child on the parent
PARENT_ALIAS="$PARENT_DATA/children_aliases.tsv"
if [[ ! -f "$PARENT_ALIAS" ]]; then
  printf 'alias\tslug\n' > "$PARENT_ALIAS"
fi
{
  echo -e "${STEM}\t${SLUG}"
  echo -e "$(echo "$STEM" | tr '-' ' ')\t${SLUG}"
} >> "$PARENT_ALIAS"

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

# Fingerprint defaults
UPD="$HOLDING_INSTALL/update_company_defaults.py"
if [[ -f "$UPD" ]]; then
  PYTHONPATH="$HOLDING_INSTALL${PYTHONPATH:+:$PYTHONPATH}" \
    python3 "$UPD" --write-manifest-only "$DEST" --agents-home "$AGENTS_HOME" --budget "$BUDGET" \
    || true
fi

echo "[create-child] done: $DEST"
echo "[create-child] parent link: $META_FILE + $GRANTS_FILE"
echo "[create-child] placement: $PLACEMENT"
echo "[create-child] next: $DEST/system/install/company_os.sh all"
echo "[create-child] then: $DEST/launch.sh grok|claude|codex|merge \"prompt\""
echo "[create-child] parent wake child: $PARENT/launch.sh grok $STEM \"prompt\""
echo "[create-child] docs: agents-holding docs/ceo-launch-and-children.md"
echo "[create-child] list: python3 $CHILDREN_REG --parent $PARENT list"
