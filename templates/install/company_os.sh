#!/usr/bin/env bash
# Generate harness adapters from Company SoT (.agents/marlin-language-company/).
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_DIR="$(cd "$INSTALL_DIR/.." && pwd)"
COMPANY_DIR="$(cd "$SYSTEM_DIR/.." && pwd)"
# Company = <repo>/.agents/marlin-language-company
if [[ "$(basename "$(dirname "$COMPANY_DIR")")" == ".agents" ]]; then
  ROOT="$(cd "$COMPANY_DIR/../.." && pwd)"
else
  ROOT="$(cd "$COMPANY_DIR/.." && pwd)"
fi
EXPORT="$SYSTEM_DIR/skills/defaults/marlin-hop/scripts/export_harness.py"
HARNESS_DIR="$SYSTEM_DIR/harness"

usage() {
  cat <<'USAGE'
Generate Company OS views for a harness (setup which harness → generate that one).

Usage:
  .agents/marlin-language-company/system/install/company_os.sh <harness|all>
  .agents/marlin-language-company/system/install/company_os.sh --list
  .agents/marlin-language-company/system/install/company_os.sh -h

Examples:
  .agents/marlin-language-company/system/install/company_os.sh grok
  .agents/marlin-language-company/system/install/company_os.sh all

Harness = system/harness/<id>.toml — [paths] say where that agent reads adapters.
USAGE
  echo
  echo "Available harnesses:"
  python3 "$EXPORT" --list | sed 's/^/  /'
}

if [[ "${1:-}" == "--list" || "${1:-}" == "list" ]]; then
  python3 "$EXPORT" --list
  exit $?
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

echo "[company_os] repo=$ROOT"
echo "[company_os] company=$COMPANY_DIR"
echo "[company_os] generate harness=$1"
cd "$ROOT"
python3 "$EXPORT" --to "$1"
echo "[company_os] done — see .agents/marlin-language-company/README.md"
