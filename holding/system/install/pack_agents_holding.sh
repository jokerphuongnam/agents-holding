#!/usr/bin/env bash
# Build the publishable community package into this repository
# (keeps existing .git). Name: agents-holding.
#
# Usage (from anywhere):
#   .agents/holding/system/install/pack_agents_holding.sh
#   .agents/holding/system/install/pack_agents_holding.sh --out /path/to/agents-holding
set -euo pipefail

HOLDING_INSTALL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOLDING_DIR="$(cd "$HOLDING_INSTALL/../.." && pwd)"
AGENTS_HOME="$(cd "$HOLDING_DIR/.." && pwd)"
# Canonical public checkout (with .git) lives under AGENTS_HOLDING_OUT or --out.
OUT="${AGENTS_HOLDING_OUT:-}"

usage() {
  cat <<'USAGE'
Pack holding + templates into the community git package **agents-holding**.

  pack_agents_holding.sh [--out <dir>]

Required: --out <dir> or env AGENTS_HOLDING_OUT

Package shape (git root when you push):
  agents-holding/
    README.md
    install.sh
    .gitignore
    holding/          # conglomerate Company OS
    templates/        # company formula, skills-library, hop-reference, install
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${OUT}" ]]; then
  echo "error: set --out /path/to/agents-holding or AGENTS_HOLDING_OUT" >&2
  usage
  exit 2
fi
OUT="$(mkdir -p "$OUT" && cd "$OUT" && pwd)"
echo "[pack_agents_holding] out=$OUT"

TEMPLATE_SRC="$AGENTS_HOME/templates"
HOP_SRC="$HOLDING_DIR/system/skills/defaults/marlin-hop"
GENERIC_OS="$AGENTS_HOME/marlin-language-company/system/install/company_os.sh"
[[ -f "$GENERIC_OS" ]] || GENERIC_OS="$HOLDING_INSTALL/company_os.sh"

rsync_or_cp() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__/' --exclude '*.pyc' \
      --exclude 'cache/export/' --exclude 'cache/cache/' \
      --exclude 'cache/user_habits.sqlite' --exclude 'cache/user_habits.sqlite-*' \
      --exclude 'cache/user_habits/' \
      "$src" "$dst"
  else
    rm -rf "$dst"
    mkdir -p "$dst"
    cp -R "$src" "$dst"
  fi
}

# holding/
rsync_or_cp "$HOLDING_DIR/" "$OUT/holding/"
mkdir -p "$OUT/holding/cache/export" "$OUT/holding/cache/cache" "$OUT/holding/example"

# templates/
mkdir -p "$OUT/templates"
if [[ -d "$TEMPLATE_SRC/company" ]]; then
  rsync_or_cp "$TEMPLATE_SRC/company/" "$OUT/templates/company/"
fi
if [[ -d "$TEMPLATE_SRC/skills-library" ]]; then
  rsync_or_cp "$TEMPLATE_SRC/skills-library/" "$OUT/templates/skills-library/"
fi

# hop-reference (scripts only)
mkdir -p "$OUT/templates/hop-reference"
if [[ -d "$HOP_SRC" ]]; then
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude 'data/' --exclude 'agents/' --exclude '__pycache__/' --exclude '*.pyc' \
      "$HOP_SRC/" "$OUT/templates/hop-reference/"
  else
    cp -R "$HOP_SRC/scripts" "$OUT/templates/hop-reference/" 2>/dev/null || true
    cp "$HOP_SRC/SKILL.md" "$OUT/templates/hop-reference/" 2>/dev/null || true
  fi
fi

mkdir -p "$OUT/templates/install"
cp "$GENERIC_OS" "$OUT/templates/install/company_os.sh"
chmod +x "$OUT/templates/install/company_os.sh"
chmod +x "$OUT/holding/system/install/"*.sh 2>/dev/null || true

# Community README + gitignore at package root
README_SRC="$HOLDING_INSTALL/AGENTS_HOLDING_README.md"
if [[ ! -f "$README_SRC" ]]; then
  echo "error: missing $README_SRC" >&2
  exit 1
fi
cp "$README_SRC" "$OUT/README.md"
mkdir -p "$OUT/holding/system/install"
cp "$README_SRC" "$OUT/holding/system/install/AGENTS_HOLDING_README.md"
# One-shot installer at package root
INSTALL_SRC="$HOLDING_INSTALL/AGENTS_HOLDING_INSTALL.sh"
if [[ ! -f "$INSTALL_SRC" ]]; then
  echo "error: missing $INSTALL_SRC" >&2
  exit 1
fi
cp "$INSTALL_SRC" "$OUT/install.sh"
chmod +x "$OUT/install.sh"
cp "$INSTALL_SRC" "$OUT/holding/system/install/AGENTS_HOLDING_INSTALL.sh"

cat > "$OUT/.gitignore" <<'EOF'
.DS_Store
__pycache__/
*.pyc
holding/cache/export/
holding/cache/cache/**
!holding/cache/cache/.gitkeep
holding/cache/user_habits.sqlite
holding/cache/user_habits.sqlite-*
holding/cache/user_habits/
**/cache/cache/task_memory.sqlite
**/cache/cache/task_memory.sqlite-*
*.tmp
EOF

# Ensure placeholders
touch "$OUT/holding/cache/cache/.gitkeep" 2>/dev/null || true

echo "[pack_agents_holding] done: $OUT"
echo "[pack_agents_holding] next: cd $OUT && git add -A && git commit && git push"
