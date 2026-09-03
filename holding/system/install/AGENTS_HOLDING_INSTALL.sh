#!/usr/bin/env bash
# One-line install (recommended):
#   curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/agents-holding/main/install.sh | bash
#
# Fetches the repo from GitHub → installs into ~/.agents → runs company_os.
# Authoring copy = your git clone of this repo (edit + push separately).
set -euo pipefail

# When piped via curl|bash, keep git/other tools from consuming stdin.
exec </dev/null

REPO_URL="${AGENTS_HOLDING_REPO:-https://github.com/jokerphuongnam/agents-holding.git}"
REPO_REF="${AGENTS_HOLDING_REF:-main}"
DEST="${HOME}/.agents"
FETCH_DIR="${AGENTS_HOLDING_FETCH:-$HOME/.cache/agents-holding}"
FROM_LOCAL=""
SKIP_OS=0

usage() {
  cat <<'USAGE'
Install agents-holding into ~/.agents.

  curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/agents-holding/main/install.sh | bash

Options (with bash -s):
  curl -fsSL …/install.sh | bash -s -- --dest ~/.agents
  curl -fsSL …/install.sh | bash -s -- --ref main
  curl -fsSL …/install.sh | bash -s -- --from-local /path/to/agents-holding
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest) DEST="${2:-}"; shift 2 ;;
    --repo) REPO_URL="${2:-}"; shift 2 ;;
    --ref) REPO_REF="${2:-}"; shift 2 ;;
    --fetch-dir) FETCH_DIR="${2:-}"; shift 2 ;;
    --from-local) FROM_LOCAL="${2:-}"; shift 2 ;;
    --skip-company-os) SKIP_OS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: need '$1' on PATH" >&2
    exit 1
  }
}

resolve_pkg() {
  local root="$1"
  [[ -d "$root/holding/system/install" && -d "$root/templates" ]] || return 1
  echo "$root"
}

PKG=""
if [[ -n "$FROM_LOCAL" ]]; then
  FROM_LOCAL="$(cd "$FROM_LOCAL" && pwd)"
  PKG="$(resolve_pkg "$FROM_LOCAL" || true)"
  [[ -n "$PKG" ]] || {
    echo "error: --from-local is not an agents-holding package: $FROM_LOCAL" >&2
    exit 1
  }
  echo "[install] source=local $PKG"
else
  need_cmd git
  mkdir -p "$(dirname "$FETCH_DIR")"
  if [[ -d "$FETCH_DIR/.git" ]]; then
    echo "[install] updating $FETCH_DIR ($REPO_REF)"
    git -C "$FETCH_DIR" remote set-url origin "$REPO_URL" 2>/dev/null || true
    git -C "$FETCH_DIR" fetch --depth 1 origin "$REPO_REF"
    git -C "$FETCH_DIR" checkout -q "$REPO_REF"
    git -C "$FETCH_DIR" reset --hard "origin/$REPO_REF"
  else
    echo "[install] cloning $REPO_URL ($REPO_REF)"
    rm -rf "$FETCH_DIR"
    git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$FETCH_DIR"
  fi
  PKG="$(resolve_pkg "$FETCH_DIR" || true)"
  [[ -n "$PKG" ]] || {
    echo "error: cloned tree missing holding/ + templates/: $FETCH_DIR" >&2
    exit 1
  }
  echo "[install] source=git $(git -C "$FETCH_DIR" rev-parse --short HEAD)"
fi

PROMOTE="$PKG/holding/system/install/install_holding_system.sh"
[[ -f "$PROMOTE" ]] || {
  echo "error: missing $PROMOTE" >&2
  exit 1
}

echo "[install] → $DEST"
bash "$PROMOTE" --dest "$DEST"

HOLDING_OS="$DEST/holding/system/install/company_os.sh"
if [[ "$SKIP_OS" -eq 0 && -x "$HOLDING_OS" ]]; then
  echo "[install] company_os all…"
  bash "$HOLDING_OS" all || {
    echo "[install] warn: company_os failed — run: $HOLDING_OS all" >&2
  }
fi

echo
echo "[install] done → $DEST/holding"
echo "Create a company:"
echo "  $DEST/holding/system/install/create-company.sh \\"
echo "    --name my-app --budget medium --tech \"react,nestjs\" \\"
echo "    --project-root /path/to/project \\"
echo "    --packages \"frontend:react,backend:nestjs\""
echo "  # multi-package: $DEST/holding/system/install/create-workspace.sh --parent … --topology teams|companies …"
