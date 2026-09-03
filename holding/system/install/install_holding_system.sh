#!/usr/bin/env bash
# Promote holding + templates to system agents home (default ~/.agents)
# Usage: install_holding_system.sh [--dest ~/.agents]
# Copies:
#   holding/ → $DEST/holding/
#   templates/ → $DEST/templates/  (from repo .agents/templates)
#   Also copies hop scripts into $DEST/templates/hop-reference/ from marlin-hop
#   and company_os.sh into $DEST/templates/install/
# Prints next steps: company_os.sh all; create-company --project-root …
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
DEST="${HOME}/.agents"

usage() {
  cat <<'USAGE'
Promote holding + templates to a system agents home.

Usage:
  install_holding_system.sh [--dest ~/.agents]
  install_holding_system.sh -h

Copies:
  holding/                  → $DEST/holding/
  templates/                → $DEST/templates/
  marlin-hop (scripts+SKILL)→ $DEST/templates/hop-reference/
  company_os.sh             → $DEST/templates/install/company_os.sh
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest) DEST="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

DEST="$(cd "$(dirname "$DEST")" && pwd)/$(basename "$DEST")"
mkdir -p "$DEST"

TEMPLATE_SRC="$AGENTS_HOME/templates"
if [[ ! -d "$TEMPLATE_SRC" ]]; then
  echo "error: missing templates at $TEMPLATE_SRC" >&2
  exit 1
fi

# Prefer hop already under this holding; else marlin-language-company reference
HOP_SRC="$HOLDING_DIR/system/skills/defaults/marlin-hop"
if [[ ! -d "$HOP_SRC/scripts" ]]; then
  HOP_SRC="$AGENTS_HOME/marlin-language-company/system/skills/defaults/marlin-hop"
fi

# Generic company_os for subsidiaries: prefer Marlin company script (messages say company)
GENERIC_OS="$AGENTS_HOME/marlin-language-company/system/install/company_os.sh"
if [[ ! -f "$GENERIC_OS" ]]; then
  GENERIC_OS="$HOLDING_INSTALL/company_os.sh"
fi

echo "[install_holding_system] agents-home-src=$AGENTS_HOME"
echo "[install_holding_system] dest=$DEST"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__/' --exclude '*.pyc' \
    "$HOLDING_DIR/" "$DEST/holding/"
  rsync -a --exclude '.DS_Store' "$TEMPLATE_SRC/" "$DEST/templates/"
else
  rm -rf "$DEST/holding"
  mkdir -p "$DEST/holding"
  cp -R "$HOLDING_DIR/." "$DEST/holding/"
  mkdir -p "$DEST/templates"
  cp -R "$TEMPLATE_SRC/." "$DEST/templates/"
fi

mkdir -p "$DEST/templates/hop-reference"
if [[ -d "$HOP_SRC" ]]; then
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude 'data/' \
      --exclude 'agents/' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      "$HOP_SRC/" "$DEST/templates/hop-reference/"
  else
    rm -rf "$DEST/templates/hop-reference"
    mkdir -p "$DEST/templates/hop-reference"
    cp -R "$HOP_SRC/scripts" "$DEST/templates/hop-reference/" 2>/dev/null || true
    cp "$HOP_SRC/SKILL.md" "$DEST/templates/hop-reference/" 2>/dev/null || true
  fi
  echo "[install_holding_system] hop-reference ← $HOP_SRC"
else
  echo "[install_holding_system] warn: no hop source at $HOP_SRC" >&2
fi

mkdir -p "$DEST/templates/install"
cp "$GENERIC_OS" "$DEST/templates/install/company_os.sh"
chmod +x "$DEST/templates/install/company_os.sh"
chmod +x "$DEST/holding/system/install/"*.sh 2>/dev/null || true

cat <<EOF
[install_holding_system] done.

Next steps:
  1) Generate holding adapters:
       $DEST/holding/system/install/company_os.sh all

  2) Create a subsidiary in a project:
       $DEST/holding/system/install/create-company.sh \\
         --name my-app --budget medium --tech "react,nestjs" \\
         --project-root /path/to/project \\
         --packages "frontend:react,backend:nestjs"

     Multi-package parent (teams | companies):
       $DEST/holding/system/install/create-workspace.sh \\
         --parent /path/to/parent --topology teams --name my-app \\
         --budget medium --package frontend:react --package backend:nestjs

  3) Then in that project:
       .agents/<slug>-company/system/install/company_os.sh all
EOF
