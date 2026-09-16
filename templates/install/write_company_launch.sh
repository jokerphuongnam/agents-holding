#!/usr/bin/env bash
# Write launch.sh on the **company** only (SoT under …/<slug>-company/).
# Do NOT write a package-root launch.sh — .agents/ is already gitignored.
#
# Usage:
#   write_company_launch.sh --company-dir DEST --package-root PKG
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE="$HOLDING_INSTALL/launch_company.sh"
TMPL="$HOLDING_INSTALL/launch.sh.tmpl"
COMPANY_DIR=""
PKG_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --package-root) PKG_ROOT="${2:-}"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$COMPANY_DIR" || ! -f "$CORE" || ! -f "$TMPL" ]]; then
  echo "error: need --company-dir, $CORE, and $TMPL" >&2
  exit 2
fi
if [[ -z "$PKG_ROOT" ]]; then
  echo "error: --package-root is required (project root that owns .grok/)" >&2
  exit 2
fi

COMPANY_DIR="$(cd "$COMPANY_DIR" && pwd)"
PKG_ROOT="$(cd "$PKG_ROOT" && pwd)"
REL_COMP="$(python3 -c "import os; print(os.path.relpath('$COMPANY_DIR', '$PKG_ROOT'))")"
OUT="$COMPANY_DIR/launch.sh"

python3 -c "
from pathlib import Path
tmpl = Path('$TMPL').read_text(encoding='utf-8')
text = (tmpl
  .replace('@@PKG@@', '$PKG_ROOT')
  .replace('@@CORE@@', '$CORE')
  .replace('@@REL@@', '$REL_COMP'))
Path('$OUT').write_text(text, encoding='utf-8')
import os
os.chmod('$OUT', 0o755)
print('[write_company_launch] company SoT:', '$OUT')
print('[write_company_launch] package root (adapters):', '$PKG_ROOT')
print('[write_company_launch] run: ./$REL_COMP/launch.sh <harness> [prompt]')
"
