#!/usr/bin/env bash
# Write launch.sh wrappers that call launch_company.sh (always CEO).
# Usage:
#   write_company_launch.sh --company-dir DEST [--package-root PKG]
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE="$HOLDING_INSTALL/launch_company.sh"
COMPANY_DIR=""
PKG_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --package-root) PKG_ROOT="${2:-}"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$COMPANY_DIR" || ! -f "$CORE" ]]; then
  echo "error: need --company-dir and $CORE" >&2
  exit 2
fi

# Company-tree launcher
cat > "$COMPANY_DIR/launch.sh" <<EOF
#!/usr/bin/env bash
# Always CEO — see agents-holding docs/ceo-launch-and-children.md
set -euo pipefail
COMP="\$(cd "\$(dirname "\$0")" && pwd)"
if [[ "\$(basename "\$(dirname "\$COMP")" )" == ".agents" ]]; then
  ROOT="\$(cd "\$COMP/../.." && pwd)"
else
  ROOT="\$(cd "\$COMP/../.." && pwd)"
fi
CORE="$CORE"
HOP="\$COMP/system/skills/defaults/marlin-hop/scripts/handoff_child.py"
FRESH_ARGS=()
POS=()
for a in "\$@"; do
  case "\$a" in
    --fresh) FRESH_ARGS+=(--fresh) ;;
    -h|--help)
      echo "Usage: ./launch.sh <grok|claude|codex|merge> [--fresh] [child?] [\\\"prompt…\\\"]"
      exit 0
      ;;
    *) POS+=("\$a") ;;
  esac
done
set -- "\${POS[@]+"\${POS[@]}"}"
[[ \$# -ge 1 ]] || { echo "Usage: ./launch.sh <grok|claude|codex|merge> [--fresh] [child?] [\\\"prompt…\\\"]" >&2; exit 2; }
MODE="\$1"; shift
if [[ \$# -ge 1 && -f "\$HOP" ]] && python3 "\$HOP" "\$1" --print-path >/dev/null 2>&1; then
  CDIR="\$(python3 "\$HOP" "\$1" --print-path)"
  shift
  if [[ "\$(basename "\$(dirname "\$CDIR")" )" == ".agents" ]]; then
    ROOT="\$(cd "\$CDIR/../.." && pwd)"
    COMP="\$CDIR"
  fi
fi
PROMPT="\$*"
exec bash "\$CORE" --company-dir "\$COMP" --root "\$ROOT" "\${FRESH_ARGS[@]+"\${FRESH_ARGS[@]}"}" "\$MODE" \${PROMPT:+"\$PROMPT"}
EOF
chmod +x "$COMPANY_DIR/launch.sh"
echo "[write_company_launch] wrote $COMPANY_DIR/launch.sh"

if [[ -n "$PKG_ROOT" ]]; then
  mkdir -p "$PKG_ROOT"
  cat > "$PKG_ROOT/launch.sh" <<EOF
#!/usr/bin/env bash
# Always CEO for this package — docs/ceo-launch-and-children.md
set -euo pipefail
PKG="\$(cd "\$(dirname "\$0")" && pwd)"
COMP="$COMPANY_DIR"
CORE="$CORE"
FRESH_ARGS=()
POS=()
for a in "\$@"; do
  case "\$a" in
    --fresh) FRESH_ARGS+=(--fresh) ;;
    -h|--help)
      echo "Usage: ./launch.sh <grok|claude|codex|merge> [--fresh] [\\\"prompt…\\\"]"
      exit 0
      ;;
    *) POS+=("\$a") ;;
  esac
done
set -- "\${POS[@]+"\${POS[@]}"}"
[[ \$# -ge 1 ]] || { echo "Usage: ./launch.sh <grok|claude|codex|merge> [--fresh] [\\\"prompt…\\\"]" >&2; exit 2; }
MODE="\$1"; shift
PROMPT="\$*"
exec bash "\$CORE" --company-dir "\$COMP" --root "\$PKG" "\${FRESH_ARGS[@]+"\${FRESH_ARGS[@]}"}" "\$MODE" \${PROMPT:+"\$PROMPT"}
EOF
  chmod +x "$PKG_ROOT/launch.sh"
  echo "[write_company_launch] wrote $PKG_ROOT/launch.sh"
fi
