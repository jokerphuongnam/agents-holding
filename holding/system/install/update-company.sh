#!/usr/bin/env bash
# Sync safe template defaults into existing subsidiary Company OS trees.
# Keeps staffs/, customs/, hop data/, COMPANY*.md. See update_company_defaults.py.
#
# Usage:
#   update-company.sh --dest /path/to/.agents/<slug>-company [--dry-run]
#   update-company.sh --all [--dry-run]
#   update-company.sh --dest … --force
#   update-company.sh --dest … --force-file FORMULA.md
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
PY="$HOLDING_INSTALL/update_company_defaults.py"

usage() {
  cat <<'USAGE'
Sync template defaults into existing companies (keep customs).

  update-company.sh --dest <company-path> [options]
  update-company.sh --all [options]

Options:
  --dry-run              Report only
  --force                Overwrite diverge/review managed files
  --force-file REL       Force one relative path (repeatable)
  --skip-harness         Do not sync system/harness/
  --budget LEVEL         Override budget for harness render
  --agents-home DIR      Default: parent of holding (…/holding/..)
  -h, --help             This help

Managed: hop scripts + SKILL.md, company_os.sh, FORMULA.md, harness (rendered).
Never touches: staffs/, customs/, hop data/, COMPANY*.md, CTO_TECH_SEED.md, cache/
(except cache/template_sync.json).

After a real update, re-run: <company>/system/install/company_os.sh all
USAGE
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --agents-home)
      AGENTS_HOME="$(cd "${2:-}" && pwd)"
      shift 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -f "$PY" ]]; then
  echo "error: missing $PY" >&2
  exit 1
fi

export PYTHONPATH="$HOLDING_INSTALL${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$PY" --agents-home "$AGENTS_HOME" "${ARGS[@]}"
