#!/usr/bin/env bash
# Create a multi-package workspace as either one company (teams) or N companies.
# Usage:
#   create-workspace.sh --parent /path/to/shop --topology teams \
#     --name shop --budget medium --package frontend:react --package backend:nestjs
#   create-workspace.sh --parent /path/to/shop --topology companies --budget medium \
#     --package frontend:shop-web:react --package backend:shop-api:nestjs
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
CREATE_COMPANY="$HOLDING_INSTALL/create-company.sh"
WS_TMPL="$AGENTS_HOME/templates/workspace"

PARENT=""
TOPOLOGY="teams"
NAME=""
BUDGET="medium"
TECH=""
DRY=0
# Each entry: path[:slug[:tech]]  (teams may omit slug; companies should set slug)
PACKAGES=()

# Render templates/workspace/*.md placeholders → stdout (values may be multiline)
render_workspace_tmpl() {
  local tmpl="$1"
  local topology="$2" parent="$3" slug="$4" packages="$5" table="$6" next="$7"
  if [[ ! -f "$tmpl" ]]; then
    echo "error: missing workspace template: $tmpl" >&2
    echo "hint: install holding templates (templates/workspace/) via install_holding_system.sh" >&2
    return 1
  fi
  TOPOLOGY="$topology" PARENT="$parent" COMPANY_SLUG="$slug" PACKAGES="$packages" \
  SUBSIDIARIES_TABLE="$table" NEXT_STEPS="$next" \
  python3 - "$tmpl" <<'PY'
import os, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
for key in (
    "TOPOLOGY", "PARENT", "COMPANY_SLUG", "PACKAGES",
    "SUBSIDIARIES_TABLE", "NEXT_STEPS",
):
    text = text.replace("{{" + key + "}}", os.environ.get(key, ""))
sys.stdout.write(text)
PY
}

usage() {
  cat <<'USAGE'
Create a multi-package workspace under one parent folder.

Renders SoT from templates/workspace/ into parent .agents/WORKSPACE.md.

  create-workspace.sh --parent <dir> --topology teams|companies \
    [--name <slug>] [--budget low|medium|high] [--tech "a,b"] \
    --package <path[:slug[:tech]]> [--package …] [--dry-run]

Topology:
  teams (default)
    One company at --parent. Packages = tech teams only; shared ceo/cto/BA/PO/QC/git.
    --name required (company slug). --package form: path or path:tech
    (slug in the middle is ignored if present).

  companies
    One company per package; each package dir is its own --project-root
    (avoids .grok/.claude adapter clobber). --package form: path:slug[:tech]
    Writes parent .agents/WORKSPACE.md listing siblings.
    Cross-package product asks go holding-ceo → sibling ceo.

Examples:
  # Monorepo → one company, FE/BE teams
  create-workspace.sh --parent "$PWD" --topology teams --name shop \
    --budget medium --package frontend:react --package backend:nestjs

  # Sibling companies (separate roots)
  create-workspace.sh --parent "$PWD" --topology companies --budget medium \
    --package frontend:shop-web:react --package backend:shop-api:nestjs
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parent) PARENT="${2:-}"; shift 2 ;;
    --topology) TOPOLOGY="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --budget) BUDGET="${2:-}"; shift 2 ;;
    --tech) TECH="${2:-}"; shift 2 ;;
    --package) PACKAGES+=("${2:-}"); shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

TOPOLOGY="$(echo "$TOPOLOGY" | tr '[:upper:]' '[:lower:]')"
case "$TOPOLOGY" in
  teams|companies) ;;
  *) echo "error: --topology must be teams|companies" >&2; exit 2 ;;
esac

if [[ -z "$PARENT" ]]; then
  echo "error: --parent required" >&2
  exit 2
fi
if [[ ${#PACKAGES[@]} -eq 0 ]]; then
  echo "error: at least one --package required" >&2
  exit 2
fi
if [[ ! -x "$CREATE_COMPANY" && ! -f "$CREATE_COMPANY" ]]; then
  echo "error: missing create-company.sh at $CREATE_COMPANY" >&2
  exit 1
fi

mkdir -p "$PARENT"
PARENT="$(cd "$PARENT" && pwd)"

parse_package() {
  # Sets: PKG_PATH PKG_SLUG PKG_TECH
  local raw="$1"
  local a="" b="" c=""
  IFS=':' read -r a b c <<< "$raw"
  PKG_PATH="$(echo "${a:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s#^/*##;s#/*$##')"
  PKG_SLUG=""
  PKG_TECH=""
  if [[ -n "${c:-}" ]]; then
    PKG_SLUG="$(echo "${b:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    PKG_TECH="$(echo "${c:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  elif [[ -n "${b:-}" ]]; then
    # Ambiguous: path:tech (teams) OR path:slug (companies). Prefer tech-looking tokens.
    local mid
    mid="$(echo "${b:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')"
    case "$mid" in
      react|vue|angular|next|nuxt|svelte|nestjs|express|node|fastapi|django|rails|spring|ios|android|flutter|swiftui|compose|typescript|javascript|frontend|backend|mobile)
        PKG_TECH="$mid"
        ;;
      *)
        PKG_SLUG="$(echo "${b:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        ;;
    esac
  fi
}

echo "[create-workspace] parent=$PARENT topology=$TOPOLOGY budget=$BUDGET"
echo "[create-workspace] packages=${PACKAGES[*]}"

if [[ "$TOPOLOGY" == "teams" ]]; then
  if [[ -z "$NAME" ]]; then
    echo "error: --name required for --topology teams" >&2
    exit 2
  fi
  PKG_CSV=""
  for raw in "${PACKAGES[@]}"; do
    parse_package "$raw"
    if [[ -z "$PKG_PATH" ]]; then
      echo "error: bad --package '$raw' (need path)" >&2
      exit 2
    fi
    mkdir -p "$PARENT/$PKG_PATH"
    entry="$PKG_PATH"
    [[ -n "$PKG_TECH" ]] && entry="${PKG_PATH}:${PKG_TECH}"
    if [[ -n "$PKG_CSV" ]]; then
      PKG_CSV="${PKG_CSV},${entry}"
    else
      PKG_CSV="$entry"
    fi
  done

  CMD=(bash "$CREATE_COMPANY"
    --name "$NAME"
    --budget "$BUDGET"
    --project-root "$PARENT"
    --topology teams
    --packages "$PKG_CSV"
  )
  [[ -n "$TECH" ]] && CMD+=(--tech "$TECH")
  [[ "$DRY" -eq 1 ]] && CMD+=(--dry-run)

  echo "[create-workspace] → ${CMD[*]}"
  "${CMD[@]}"

  if [[ "$DRY" -eq 0 ]]; then
    mkdir -p "$PARENT/.agents"
    SLUG="$NAME"
    [[ "$SLUG" == *-company ]] || SLUG="${SLUG}-company"
    SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]/-/g')"
    NEXT="\`.agents/$SLUG/system/install/company_os.sh all\`"
    render_workspace_tmpl \
      "$WS_TMPL/WORKSPACE.teams.md" \
      "teams" "$PARENT" "$SLUG" "$PKG_CSV" "" "$NEXT" \
      > "$PARENT/.agents/WORKSPACE.md"
    echo "[create-workspace] wrote $PARENT/.agents/WORKSPACE.md (from templates/workspace)"
    echo "[create-workspace] next: $PARENT/.agents/$SLUG/system/install/company_os.sh all"
  fi
  exit 0
fi

# --- companies topology ---
CREATED=()
ROOTS_SEEN=()
for raw in "${PACKAGES[@]}"; do
  parse_package "$raw"
  if [[ -z "$PKG_PATH" ]]; then
    echo "error: bad --package '$raw' (need path:slug[:tech])" >&2
    exit 2
  fi
  if [[ -z "$PKG_SLUG" ]]; then
    # default slug from path basename
    PKG_SLUG="$(basename "$PKG_PATH")"
  fi
  PKG_ROOT="$PARENT/$PKG_PATH"
  mkdir -p "$PKG_ROOT"

  for seen in "${ROOTS_SEEN[@]:-}"; do
    if [[ "$seen" == "$PKG_ROOT" ]]; then
      echo "error: two packages share project-root $PKG_ROOT (adapter collision)" >&2
      exit 2
    fi
  done
  ROOTS_SEEN+=("$PKG_ROOT")

  CMD=(bash "$CREATE_COMPANY"
    --name "$PKG_SLUG"
    --budget "$BUDGET"
    --project-root "$PKG_ROOT"
    --topology teams
  )
  # single-package company: path basename is the team slice under that root
  if [[ -n "$PKG_TECH" ]]; then
    CMD+=(--packages "${PKG_PATH##*/}:${PKG_TECH}")
  elif [[ -n "$TECH" ]]; then
    CMD+=(--tech "$TECH" --packages "${PKG_PATH##*/}")
  else
    CMD+=(--packages "${PKG_PATH##*/}")
  fi
  [[ "$DRY" -eq 1 ]] && CMD+=(--dry-run)

  echo "[create-workspace] → ${CMD[*]}"
  "${CMD[@]}"

  SLUG="$PKG_SLUG"
  [[ "$SLUG" == *-company ]] || SLUG="${SLUG}-company"
  SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]/-/g')"
  CREATED+=("$PKG_PATH|$SLUG|$PKG_ROOT")
done

if [[ "$DRY" -eq 1 ]]; then
  echo "[create-workspace] dry-run OK (companies)"
  exit 0
fi

mkdir -p "$PARENT/.agents"
TABLE=""
NEXT=""
for row in "${CREATED[@]}"; do
  IFS='|' read -r p s r <<< "$row"
  TABLE+="| \`$p\` | \`$s\` | \`$r\` |
"
  NEXT+="- \`$r/.agents/$s/system/install/company_os.sh all\`
"
done
render_workspace_tmpl \
  "$WS_TMPL/WORKSPACE.companies.md" \
  "companies" "$PARENT" "" "" "$TABLE" "$NEXT" \
  > "$PARENT/.agents/WORKSPACE.md"

echo "[create-workspace] wrote $PARENT/.agents/WORKSPACE.md (from templates/workspace)"
echo "[create-workspace] done (${#CREATED[@]} companies). Run each company_os.sh all (see WORKSPACE.md)."
