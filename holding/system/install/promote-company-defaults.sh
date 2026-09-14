#!/usr/bin/env bash
# Mirror safe defaults FROM one company INTO templates/, then distribute
# with update-company.sh.
#
# Full loop:
#   1. Edit defaults in a reference company (e.g. pilot-company)
#   2. promote-company-defaults.sh --from …/pilot-company
#   3. (optional) commit + push agents-holding; install.sh on other machines
#   4. update-company.sh --all
#
# Usage:
#   promote-company-defaults.sh --from /path/to/.agents/<slug>-company [--dry-run]
#   promote-company-defaults.sh --from … --agents-home /path/to/agents-holding
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
PY="$HOLDING_INSTALL/promote_company_defaults.py"

usage() {
  cat <<'USAGE'
Promote safe defaults from one company into holding templates.

  promote-company-defaults.sh --from <company-path> [options]

Options:
  --dry-run              Report only
  --agents-home DIR      Where templates/ live (default: parent of holding)
                         Use the agents-holding git checkout to promote into git.
  -h, --help             This help

Promotes: hop scripts + SKILL.md, company_os.sh, FORMULA.md, harness
(re-generalized with {{COMPANY_SLUG}} / {{EFFORT_*}}).

Never copies: staffs/, customs/, hop data/, COMPANY*.md, CTO_TECH_SEED.md

After promote:
  update-company.sh --all --dry-run
  update-company.sh --all
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
