#!/usr/bin/env bash
# Shared Company OS launcher — every company (parent + children).
#
# User-facing agents in a room: ceo | ba-user only (everyone else = sub-agent).
# Default workspace = the PROJECT that contains the company (--cwd there).
#   - A room is one branch of <company>/cache/work-history
#     under <project-parent>/.company-rooms/<name>
#   - The project does not need its own git repository.
# Never use harness --worktree / Grove clone into system trees.
#
#   launch_company.sh --company-dir DIR --root DIR <harness|merge> \
#     [--agent ceo|ba-user] [--room-name NAME] [--no-room] [--continue] \
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

User channels in the room: ceo | ba-user only (other roles = sub-agents).

  # Start (new company room as CEO):
  launch_company.sh --company-dir … --root … grok "…"

  # Call BA in the SAME room:
  launch_company.sh --company-dir … --root … grok --room-name NAME --agent ba-user "…"

  # Return to CEO in that room:
  launch_company.sh --company-dir … --root … grok --room-name NAME --agent ceo "…"

Options:
  --agent ceo|ba-user   User-facing agent (default: ceo)
  --room-name NAME      Name/join room under ../.company-rooms/NAME
  --no-room             Stay in --root (no new room)
  --continue NAME       Resume that room: switch to its branch and open the agent

Rooms are branches of the company work history at cache/work-history, not of the
project repository. Each room branch is checked out as the CEO worktree. Another
staff gets a worktree only when that staff is launched in this room, and that
worktree is linked to the CEO worktree. The project does not have to be a git
repo. Ignored overlays (.agents/.grok/…) are symlinked from --root into the
worktree when missing.
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
    --continue|-c)
      CONTINUE=1
      if [[ -n "${2:-}" && "${2:-}" != -* ]]; then
        WT_NAME="${2:-}"
        shift 2
      else
        echo "error: --continue needs the room name" >&2
        exit 2
      fi
      ;;
    --no-room|--no-worktree) NO_WORKTREE=1; shift ;;
    --room-name|--worktree-name|--worktree)
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

WORK_HISTORY="$(cd "$(dirname "$0")" && pwd)/work_history.py"

room_dest_parent() {
  echo "$(dirname "$ROOT")/.company-rooms"
}

# Link company/harness overlays that are gitignored (not present in a fresh room).
# Also symlink other top-level live paths missing from dest (empty/sparse HEAD, e.g. Pilot).
link_company_overlays() {
  local src="$1" dest="$2"
  [[ -n "$src" && -n "$dest" && "$src" != "$dest" ]] || return 0
  local d base
  for d in .agents .grok .claude .codex; do
    if [[ -e "$src/$d" && ! -e "$dest/$d" ]]; then
      ln -s "$src/$d" "$dest/$d"
      echo "[launch] symlink $dest/$d → $src/$d" >&2
    fi
  done
  # Untracked / nested package trees are absent from an empty-commit room.
  shopt -s nullglob dotglob
  for d in "$src"/*; do
    base="$(basename "$d")"
    case "$base" in
      .|..|.git) continue ;;
    esac
    if [[ -e "$d" && ! -e "$dest/$base" ]]; then
      ln -s "$d" "$dest/$base"
      echo "[launch] symlink $dest/$base → $d" >&2
    fi
  done
  shopt -u nullglob dotglob
}

ensure_company_room() {
  # stdout = path only. A missing room is created.
  local name="$1"
  local parent
  parent="$(room_dest_parent)"
  echo "[launch] company room $parent/$name" >&2
  python3 "$WORK_HISTORY" ensure-room \
    --company "$COMPANY_DIR" \
    --source "$ROOT" \
    --room-name "$name" \
    --dest-parent "$parent"
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

USE_WT=1
[[ "$NO_WORKTREE" -eq 1 ]] && USE_WT=0

if [[ "$CONTINUE" -eq 1 && -z "$WT_NAME" ]]; then
  echo "error: --continue needs the room name" >&2
  exit 2
fi

if [[ "$CONTINUE" -eq 0 && -z "$WT_NAME" && "$USE_WT" -eq 1 ]]; then
  WT_NAME="${STEM}-$(date +%Y%m%d-%H%M%S)"
fi

# Switching to ba-user without a room name is unsafe (would create a new room as BA)
if [[ "$AGENT" == "ba-user" && -z "$WT_NAME" ]]; then
  echo "error: --agent ba-user requires --room-name <existing> (same room as CEO)" >&2
  echo "hint: launch as ceo first, note the room name, then:" >&2
  echo "  launch.sh grok --room-name <name> --agent ba-user \"…\"" >&2
  exit 2
fi

LAUNCH_ROOT="$ROOT"

if [[ "$USE_WT" -eq 1 || -n "$WT_NAME" ]]; then
  # The room branch stays on the CEO worktree. Other staff attach beside it.
  if [[ "$AGENT" == "ceo" ]]; then
    LAUNCH_ROOT="$(ensure_company_room "$WT_NAME")"
  else
    parent="$(room_dest_parent)"
    echo "[launch] activate $AGENT on room $WT_NAME" >&2
    LAUNCH_ROOT="$(python3 "$WORK_HISTORY" activate-staff \
      --company "$COMPANY_DIR" \
      --source "$ROOT" \
      --room-name "$WT_NAME" \
      --dest-parent "$parent" \
      --staff "$AGENT")"
  fi
  echo "[launch] company room: $LAUNCH_ROOT (agent=$AGENT)" >&2
fi

link_company_overlays "$ROOT" "$LAUNCH_ROOT"

echo "[launch] agent=$AGENT harness=$HARNESS room=${WT_NAME:-none} root=$LAUNCH_ROOT company=$COMPANY_DIR" >&2
[[ -n "$PROMPT" ]] && echo "[launch] first_prompt=${PROMPT:0:160}" >&2

cd "$LAUNCH_ROOT"

# The user line is written before staff work. File commits wait until the round is closed.
if [[ -n "$WT_NAME" && -n "$PROMPT" ]]; then
  python3 "$WORK_HISTORY" say \
    --company "$COMPANY_DIR" \
    --room-name "$WT_NAME" \
    --who user \
    --message "$PROMPT" \
    --thread ceo
fi

set +e
case "$HARNESS" in
  grok)
    # Always --cwd of the project or its room. Never grok --worktree.
    GOPTS=(--agent "$AGENT" --cwd "$LAUNCH_ROOT")
    [[ "$CONTINUE" -eq 1 ]] && GOPTS+=(--continue)
    if [[ -n "$PROMPT" && ! -t 0 ]]; then
      # The app has no terminal. One turn, then the reply is stored on the talk branch.
      reply="$(grok "${GOPTS[@]}" --always-approve --single "$PROMPT" || true)"
      reply="${reply#"${reply%%[![:space:]]*}"}"
      reply="${reply%"${reply##*[![:space:]]}"}"
      if [[ -n "$reply" && -n "$WT_NAME" ]]; then
        python3 "$WORK_HISTORY" say \
          --company "$COMPANY_DIR" \
          --room-name "$WT_NAME" \
          --who "$AGENT" \
          --message "$reply" \
          --thread ceo
      fi
    elif [[ -n "$PROMPT" ]]; then
      grok "${GOPTS[@]}" "$PROMPT"
    elif [[ "$CONTINUE" -eq 1 && ! -t 0 ]]; then
      echo "[launch] room ready: $LAUNCH_ROOT" >&2
    else
      grok "${GOPTS[@]}"
    fi
    ;;
  claude)
    COPTS=(--agent "$AGENT")
    [[ "$CONTINUE" -eq 1 ]] && COPTS+=(--continue)
    if [[ -n "$PROMPT" ]]; then claude "${COPTS[@]}" "$PROMPT"
    else claude "${COPTS[@]}"; fi
    ;;
  codex)
    if [[ "$AGENT" != "ceo" ]]; then
      echo "[launch] warn: codex path has limited agent cards — prefer grok/claude for ba-user switch" >&2
    fi
    if [[ "$CONTINUE" -eq 1 ]]; then
      if [[ -n "$PROMPT" ]]; then codex resume --last "$PROMPT" 2>/dev/null || codex "$PROMPT"
      else codex resume --last 2>/dev/null || codex; fi
    else
      if [[ -n "$PROMPT" ]]; then codex "$PROMPT"
      else codex; fi
    fi
    ;;
  *)
    echo "error: no launch wiring for harness='$HARNESS'" >&2
    exit 2
    ;;
esac
agent_status=$?
set -e

# The room records this turn when the agent process returns.
if [[ -n "$WT_NAME" ]]; then
  python3 "$WORK_HISTORY" capture \
    --company "$COMPANY_DIR" \
    --room "$LAUNCH_ROOT" \
    --room-name "$WT_NAME" \
    --staff "$AGENT" \
    --message "${PROMPT:-session}" || agent_status=$?
fi
exit "$agent_status"
