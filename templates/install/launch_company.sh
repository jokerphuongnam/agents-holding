#!/usr/bin/env bash
# Shared Company OS launcher — used by every company (parent + children).
# Always talks to CEO directly. First prompt = remaining args.
#
# Default: start in a **new git worktree** (do not reuse the current checkout).
#
#   launch_company.sh --company-dir <abs> --root <abs> <harness|merge> \
#     [--continue] [--no-worktree] [--worktree-name NAME] ["prompt…"]
#
set -euo pipefail

COMPANY_DIR=""
ROOT=""
CONTINUE=0
NO_WORKTREE=0
WT_NAME=""
ARGS=()

usage() {
  cat <<'USAGE'
launch_company.sh --company-dir DIR --root DIR <harness|merge> [options] ["prompt…"]

Always: CEO chat for that company.
  grok|claude|codex  → that CLI as ceo
  merge              → company_os all + CEO on runtime_router default

Worktree (default = NEW worktree, not the current checkout):
  (default)            grok/claude: --worktree; codex: git worktree add
  --worktree-name NAME optional worktree/branch name
  --no-worktree        stay in --root (current tree)
  --continue           continue prior session (implies --no-worktree)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --continue|-c) CONTINUE=1; NO_WORKTREE=1; shift ;;
    --no-worktree) NO_WORKTREE=1; shift ;;
    --worktree-name|--worktree)
      if [[ "${2:-}" == -* || -z "${2:-}" ]]; then
        WT_NAME=""
        [[ "$1" == "--worktree" ]] && shift || shift
      else
        WT_NAME="${2:-}"
        shift 2
      fi
      ;;
    --fresh)
      # legacy alias: new session in new worktree (already default)
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    --) shift; ARGS+=("$@"); break ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

if [[ -z "$COMPANY_DIR" || -z "$ROOT" || $# -lt 1 ]]; then
  usage
  exit 2
fi

OS_SH="$COMPANY_DIR/system/install/company_os.sh"
ROUTER="$COMPANY_DIR/system/harness/runtime_router.toml"
MODE="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
shift
PROMPT="$*"

default_runtime() {
  python3 - "$1" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
rt = "grok"
if p.is_file():
    m = re.search(r'\[default\][^\[]*?runtime\s*=\s*"([^"]+)"', p.read_text(encoding="utf-8"), re.S)
    if m:
        rt = m.group(1)
print(rt)
PY
}

slug_from_company() {
  basename "$COMPANY_DIR"
  # desk-garden-company → desk-garden
}

HARNESS="$MODE"
if [[ "$MODE" == "merge" ]]; then
  echo "[launch] merge → company_os all + CEO on router default" >&2
  bash "$OS_SH" all
  HARNESS="$(default_runtime "$ROUTER")"
  echo "[launch] merge runtime=$HARNESS" >&2
  if [[ -f "$ROUTER" ]] && grep -q 'enabled = false' "$ROUTER"; then
    echo "[launch] note: set runtime_router enabled=true for cross-vendor Assign" >&2
  fi
else
  if [[ ! -f "$COMPANY_DIR/system/harness/${HARNESS}.toml" ]]; then
    echo "error: unknown harness '$HARNESS' (or use merge)" >&2
    ls "$COMPANY_DIR/system/harness/"*.toml 2>/dev/null | xargs -n1 basename | sed 's/\.toml$//;s/^/  /' >&2
    echo "  merge" >&2
    exit 2
  fi
  case "$HARNESS" in
    grok) [[ -e "$ROOT/.grok/agents/ceo.md" ]] || bash "$OS_SH" grok ;;
    claude) [[ -d "$ROOT/.claude/agents" ]] || bash "$OS_SH" claude ;;
    codex) [[ -f "$ROOT/.codex/AGENTS.md" ]] || bash "$OS_SH" codex ;;
    *) bash "$OS_SH" "$HARNESS" ;;
  esac
fi

# --- worktree ---
# For grok/claude, prefer CLI --worktree (Grove-aware). For codex, git worktree add.
USE_WT=1
[[ "$NO_WORKTREE" -eq 1 ]] && USE_WT=0

STEM="$(basename "$COMPANY_DIR")"
STEM="${STEM%-company}"
if [[ -z "$WT_NAME" && "$USE_WT" -eq 1 ]]; then
  WT_NAME="${STEM}-$(date +%Y%m%d-%H%M%S)"
fi

LAUNCH_ROOT="$ROOT"
if [[ "$USE_WT" -eq 1 && "$HARNESS" == "codex" ]]; then
  # Codex: create a plain git worktree beside the repo, then run there
  REPO_GIT="$(cd "$ROOT" && git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "$REPO_GIT" ]]; then
    echo "[launch] warn: not a git repo at $ROOT — launching without worktree" >&2
    USE_WT=0
  else
    WT_PARENT="$(dirname "$REPO_GIT")/.grok-worktrees"
    mkdir -p "$WT_PARENT"
    LAUNCH_ROOT="$WT_PARENT/$WT_NAME"
    if [[ ! -d "$LAUNCH_ROOT" ]]; then
      echo "[launch] git worktree add $LAUNCH_ROOT ($WT_NAME)" >&2
      git -C "$REPO_GIT" worktree add -b "$WT_NAME" "$LAUNCH_ROOT" HEAD
    fi
  fi
fi

echo "[launch] ceo=direct harness=$HARNESS worktree=$([[ $USE_WT -eq 1 ]] && echo "$WT_NAME" || echo none) continue=$CONTINUE root=$LAUNCH_ROOT company=$COMPANY_DIR" >&2
[[ -n "$PROMPT" ]] && echo "[launch] first_prompt=${PROMPT:0:160}" >&2

cd "$LAUNCH_ROOT"

case "$HARNESS" in
  grok)
    GOPTS=(--agent ceo)
    if [[ "$USE_WT" -eq 1 ]]; then
      GOPTS+=(--worktree "$WT_NAME")
    else
      GOPTS+=(--cwd "$LAUNCH_ROOT")
      [[ "$CONTINUE" -eq 1 ]] && GOPTS+=(--continue)
    fi
    if [[ -n "$PROMPT" ]]; then exec grok "${GOPTS[@]}" "$PROMPT"
    else exec grok "${GOPTS[@]}"; fi
    ;;
  claude)
    COPTS=(--agent ceo)
    if [[ "$USE_WT" -eq 1 ]]; then
      COPTS+=(--worktree "$WT_NAME")
    else
      [[ "$CONTINUE" -eq 1 ]] && COPTS+=(--continue)
    fi
    if [[ -n "$PROMPT" ]]; then exec claude "${COPTS[@]}" "$PROMPT"
    else exec claude "${COPTS[@]}"; fi
    ;;
  codex)
    if [[ "$CONTINUE" -eq 1 ]]; then
      if [[ -n "$PROMPT" ]]; then exec codex resume --last "$PROMPT" 2>/dev/null || exec codex "$PROMPT"
      else exec codex resume --last 2>/dev/null || exec codex; fi
    else
      if [[ -n "$PROMPT" ]]; then exec codex "$PROMPT"
      else exec codex; fi
    fi
    ;;
  *)
    echo "error: no CEO launch wiring for harness='$HARNESS'" >&2
    exit 2
    ;;
esac
