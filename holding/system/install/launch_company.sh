#!/usr/bin/env bash
# Shared Company OS launcher — every company (parent + children).
#
# User-facing agents in a worktree: ceo | ba-user only (everyone else = sub-agent).
# Default: NEW git worktree as ceo. Switch BA/CEO by reusing --worktree-name.
#
#   launch_company.sh --company-dir DIR --root DIR <harness|merge> \
#     [--agent ceo|ba-user] [--worktree-name NAME] [--no-worktree] [--continue] \
#     ["prompt…"]
#
set -euo pipefail

COMPANY_DIR=""
ROOT=""
CONTINUE=0
NO_WORKTREE=0
WT_NAME=""
AGENT="ceo"
ARGS=()

usage() {
  cat <<'USAGE'
launch_company.sh --company-dir DIR --root DIR <harness|merge> [options] ["prompt…"]

User channels in the worktree: ceo | ba-user only (other roles = sub-agents).

  # Start (new worktree as CEO):
  launch_company.sh --company-dir … --root … grok "…"

  # Call BA in the SAME worktree:
  launch_company.sh --company-dir … --root … grok --worktree-name NAME --agent ba-user "…"

  # Return to CEO in that worktree:
  launch_company.sh --company-dir … --root … grok --worktree-name NAME --agent ceo "…"

Options:
  --agent ceo|ba-user   User-facing agent (default: ceo)
  --worktree-name NAME  Worktree/branch name (required to switch agent in-place)
  --no-worktree         Stay in --root (no new worktree)
  --continue            Continue prior session (implies join existing / no new worktree)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --agent)
      AGENT="$(printf '%s' "${2:-}" | tr '[:upper:]' '[:lower:]')"
      shift 2
      ;;
    --continue|-c) CONTINUE=1; NO_WORKTREE=1; shift ;;
    --no-worktree) NO_WORKTREE=1; shift ;;
    --worktree-name|--worktree)
      if [[ "${2:-}" == -* || -z "${2:-}" ]]; then
        WT_NAME=""
        shift
      else
        WT_NAME="${2:-}"
        shift 2
      fi
      ;;
    --fresh) shift ;; # legacy
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

case "$AGENT" in
  ceo|ba-user) ;;
  *)
    echo "error: --agent must be ceo or ba-user (user channels only; others are sub-agents)" >&2
    exit 2
    ;;
esac

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

resolve_worktree_path() {
  # Prefer git worktree list match by branch/path basename
  local name="$1" repo="$2"
  git -C "$repo" worktree list --porcelain 2>/dev/null | python3 - "$name" <<'PY'
import sys
name = sys.argv[1]
lines = sys.stdin.read().splitlines()
cur = {}
rows = []
for line in lines + [""]:
    if not line.strip():
        if cur:
            rows.append(cur)
        cur = {}
        continue
    if line.startswith("worktree "):
        cur["path"] = line.split(" ", 1)[1]
    elif line.startswith("branch "):
        cur["branch"] = line.split(" ", 1)[1].removeprefix("refs/heads/")
for r in rows:
    path = r.get("path", "")
    branch = r.get("branch", "")
    if branch == name or path.rstrip("/").endswith("/" + name) or path.rstrip("/").endswith(name):
        print(path)
        break
PY
}

HARNESS="$MODE"
if [[ "$MODE" == "merge" ]]; then
  echo "[launch] merge → company_os all + CEO/BA on router default" >&2
  bash "$OS_SH" all
  HARNESS="$(default_runtime "$ROUTER")"
  echo "[launch] merge runtime=$HARNESS" >&2
else
  if [[ ! -f "$COMPANY_DIR/system/harness/${HARNESS}.toml" ]]; then
    echo "error: unknown harness '$HARNESS' (or use merge)" >&2
    exit 2
  fi
  case "$HARNESS" in
    grok) [[ -e "$ROOT/.grok/agents/ceo.md" || -e "$ROOT/.grok/agents/${AGENT}.md" ]] || bash "$OS_SH" grok ;;
    claude) [[ -d "$ROOT/.claude/agents" ]] || bash "$OS_SH" claude ;;
    codex) [[ -f "$ROOT/.codex/AGENTS.md" ]] || bash "$OS_SH" codex ;;
    *) bash "$OS_SH" "$HARNESS" ;;
  esac
fi

# Ensure user-facing agent card exists when possible
if [[ "$HARNESS" == "grok" && ! -e "$ROOT/.grok/agents/${AGENT}.md" ]]; then
  bash "$OS_SH" grok || true
fi

STEM="$(basename "$COMPANY_DIR")"
STEM="${STEM%-company}"

# Joining an existing topic worktree as ba-user/ceo (same conversation workspace)
JOIN_EXISTING=0
if [[ -n "$WT_NAME" && "$AGENT" != "ceo" ]]; then
  JOIN_EXISTING=1
  NO_WORKTREE=1
fi
if [[ -n "$WT_NAME" && "$CONTINUE" -eq 1 ]]; then
  JOIN_EXISTING=1
  NO_WORKTREE=1
fi
# Explicit: ceo with --worktree-name alone still CREATES/USES that named worktree via CLI

USE_WT=1
[[ "$NO_WORKTREE" -eq 1 ]] && USE_WT=0

if [[ -z "$WT_NAME" && "$USE_WT" -eq 1 ]]; then
  WT_NAME="${STEM}-$(date +%Y%m%d-%H%M%S)"
fi

# Switching to ba-user without a worktree name is unsafe (would create a new tree as BA)
if [[ "$AGENT" == "ba-user" && -z "$WT_NAME" && "$USE_WT" -eq 1 ]]; then
  echo "error: --agent ba-user requires --worktree-name <existing> (same tree as CEO)" >&2
  echo "hint: launch as ceo first, note the worktree name, then:" >&2
  echo "  launch.sh grok --worktree-name <name> --agent ba-user \"…\"" >&2
  exit 2
fi

LAUNCH_ROOT="$ROOT"
REPO_GIT="$(cd "$ROOT" && git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ "$JOIN_EXISTING" -eq 1 && -n "$WT_NAME" && -n "$REPO_GIT" ]]; then
  FOUND="$(resolve_worktree_path "$WT_NAME" "$REPO_GIT" || true)"
  if [[ -n "$FOUND" && -d "$FOUND" ]]; then
    LAUNCH_ROOT="$FOUND"
    USE_WT=0
    echo "[launch] joining existing worktree: $FOUND (agent=$AGENT)" >&2
  else
    # Grove may own the worktree; still pass name to CLI without creating a second one if possible
    echo "[launch] worktree '$WT_NAME' not in git worktree list — launching with named worktree/cwd hints" >&2
  fi
fi

if [[ "$USE_WT" -eq 1 && "$HARNESS" == "codex" && -n "$REPO_GIT" ]]; then
  WT_PARENT="$(dirname "$REPO_GIT")/.grok-worktrees"
  mkdir -p "$WT_PARENT"
  LAUNCH_ROOT="$WT_PARENT/$WT_NAME"
  if [[ ! -d "$LAUNCH_ROOT" ]]; then
    echo "[launch] git worktree add $LAUNCH_ROOT (branch $WT_NAME)" >&2
    git -C "$REPO_GIT" worktree add -b "$WT_NAME" "$LAUNCH_ROOT" HEAD
  fi
  USE_WT=0
fi

echo "[launch] agent=$AGENT harness=$HARNESS worktree=${WT_NAME:-none} join=$JOIN_EXISTING root=$LAUNCH_ROOT company=$COMPANY_DIR" >&2
[[ -n "$PROMPT" ]] && echo "[launch] first_prompt=${PROMPT:0:160}" >&2

cd "$LAUNCH_ROOT"

case "$HARNESS" in
  grok)
    GOPTS=(--agent "$AGENT")
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
    COPTS=(--agent "$AGENT")
    if [[ "$USE_WT" -eq 1 ]]; then
      COPTS+=(--worktree "$WT_NAME")
    else
      [[ "$CONTINUE" -eq 1 ]] && COPTS+=(--continue)
    fi
    if [[ -n "$PROMPT" ]]; then exec claude "${COPTS[@]}" "$PROMPT"
    else exec claude "${COPTS[@]}"; fi
    ;;
  codex)
    # Codex has no portable agent switch like grok; document limitation
    if [[ "$AGENT" != "ceo" ]]; then
      echo "[launch] warn: codex path has limited agent cards — prefer grok/claude for ba-user switch" >&2
    fi
    if [[ "$CONTINUE" -eq 1 ]]; then
      if [[ -n "$PROMPT" ]]; then exec codex resume --last "$PROMPT" 2>/dev/null || exec codex "$PROMPT"
      else exec codex resume --last 2>/dev/null || exec codex; fi
    else
      if [[ -n "$PROMPT" ]]; then exec codex "$PROMPT"
      else exec codex; fi
    fi
    ;;
  *)
    echo "error: no launch wiring for harness='$HARNESS'" >&2
    exit 2
    ;;
esac
