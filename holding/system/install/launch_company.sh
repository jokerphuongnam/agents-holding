#!/usr/bin/env bash
# Shared Company OS launcher — every company (parent + children).
#
# User-facing agents in a worktree: ceo | ba-user only (everyone else = sub-agent).
# Default workspace = the PROJECT that contains the company (--cwd there).
#   - Company at repo root → sibling git worktree <repo-parent>/.company-worktrees/<name>
#   - Company nested in a monorepo package → live package cwd (avoids empty HEAD checkouts)
# Never use harness --worktree / Grove clone into system trees.
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

  # Start (new git worktree of the project as CEO):
  launch_company.sh --company-dir … --root … grok "…"

  # Call BA in the SAME worktree:
  launch_company.sh --company-dir … --root … grok --worktree-name NAME --agent ba-user "…"

  # Return to CEO in that worktree:
  launch_company.sh --company-dir … --root … grok --worktree-name NAME --agent ceo "…"

Options:
  --agent ceo|ba-user   User-facing agent (default: ceo)
  --worktree-name NAME  Name/join worktree under ../.company-worktrees/NAME
  --no-worktree         Stay in --root (no new worktree)
  --continue            Continue prior session (implies join existing / no new worktree)

Worktrees are always `git worktree add` from the project repo that contains the
company — never a harness system clone. Ignored overlays (.agents/.grok/…) are
symlinked from --root into the worktree when missing.
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

# Link company/harness overlays that are gitignored (not present in a fresh worktree).
link_company_overlays() {
  local src="$1" dest="$2"
  [[ -n "$src" && -n "$dest" && "$src" != "$dest" ]] || return 0
  local d
  for d in .agents .grok .claude .codex; do
    if [[ -e "$src/$d" && ! -e "$dest/$d" ]]; then
      ln -s "$src/$d" "$dest/$d"
      echo "[launch] symlink $dest/$d → $src/$d" >&2
    fi
  done
}

ensure_project_worktree() {
  # Create or reuse: <parent-of-repo>/.company-worktrees/<name>
  local repo="$1" name="$2"
  local parent dest found
  found="$(resolve_worktree_path "$name" "$repo" || true)"
  if [[ -n "$found" && -d "$found" ]]; then
    printf '%s\n' "$found"
    return 0
  fi
  parent="$(dirname "$repo")/.company-worktrees"
  mkdir -p "$parent"
  dest="$parent/$name"
  if [[ -d "$dest" ]]; then
    echo "error: path exists but is not a registered git worktree: $dest" >&2
    exit 2
  fi
  echo "[launch] git worktree add $dest (branch $name) from $repo" >&2
  if git -C "$repo" show-ref --verify --quiet "refs/heads/$name"; then
    git -C "$repo" worktree add "$dest" "$name"
  else
    git -C "$repo" worktree add -b "$name" "$dest" HEAD
  fi
  printf '%s\n' "$dest"
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

if [[ -z "$WT_NAME" && "$USE_WT" -eq 1 ]]; then
  WT_NAME="${STEM}-$(date +%Y%m%d-%H%M%S)"
fi

# Switching to ba-user without a worktree name is unsafe (would create a new tree as BA)
if [[ "$AGENT" == "ba-user" && -z "$WT_NAME" ]]; then
  echo "error: --agent ba-user requires --worktree-name <existing> (same tree as CEO)" >&2
  echo "hint: launch as ceo first, note the worktree name, then:" >&2
  echo "  launch.sh grok --worktree-name <name> --agent ba-user \"…\"" >&2
  exit 2
fi

LAUNCH_ROOT="$ROOT"
REPO_GIT="$(cd "$ROOT" && git rev-parse --show-toplevel 2>/dev/null || true)"
# Non-empty when company package root is nested inside a monorepo checkout.
PKG_REL=""
if [[ -n "$REPO_GIT" ]]; then
  PKG_REL="$(python3 -c "import os; print(os.path.relpath('$ROOT', '$REPO_GIT'))")"
  [[ "$PKG_REL" == "." ]] && PKG_REL=""
fi

if [[ "$USE_WT" -eq 1 ]]; then
  if [[ -z "$REPO_GIT" ]]; then
    echo "error: --root is not inside a git repo; cannot create a project worktree" >&2
    echo "hint: use --no-worktree, or run from the project that contains the company" >&2
    exit 2
  fi

  if [[ -n "$PKG_REL" ]]; then
    # Nested package (e.g. projects/desk-garden): always the live package that holds
    # the company. A monorepo git worktree from HEAD often lacks uncommitted package
    # files — and harness --worktree clones are wrong. BA handoff = same cwd + --agent.
    LAUNCH_ROOT="$ROOT"
    if [[ "$AGENT" == "ba-user" ]]; then
      echo "[launch] nested package — joining live project $LAUNCH_ROOT (agent=$AGENT name=$WT_NAME)" >&2
    else
      echo "[launch] nested package — cwd=$LAUNCH_ROOT (project contains company; name=$WT_NAME)" >&2
    fi
  elif [[ "$AGENT" == "ba-user" ]]; then
    FOUND="$(resolve_worktree_path "$WT_NAME" "$REPO_GIT" || true)"
    if [[ -z "$FOUND" || ! -d "$FOUND" ]]; then
      echo "error: worktree '$WT_NAME' not found under project $REPO_GIT" >&2
      echo "hint: start ceo first (creates ../.company-worktrees/$WT_NAME), then hand off" >&2
      exit 2
    fi
    LAUNCH_ROOT="$FOUND"
    echo "[launch] joining existing worktree: $LAUNCH_ROOT (agent=$AGENT)" >&2
  else
    # Company at repo root: sibling git worktree (never harness --worktree clone)
    LAUNCH_ROOT="$(ensure_project_worktree "$REPO_GIT" "$WT_NAME")"
    echo "[launch] project worktree: $LAUNCH_ROOT (agent=$AGENT)" >&2
  fi
elif [[ -n "$WT_NAME" && -n "$REPO_GIT" && -z "$PKG_REL" ]]; then
  # --continue / --no-worktree with an explicit name → prefer that checkout if registered
  FOUND="$(resolve_worktree_path "$WT_NAME" "$REPO_GIT" || true)"
  if [[ -n "$FOUND" && -d "$FOUND" ]]; then
    LAUNCH_ROOT="$FOUND"
    echo "[launch] joining existing worktree: $LAUNCH_ROOT (agent=$AGENT)" >&2
  fi
fi

link_company_overlays "$ROOT" "$LAUNCH_ROOT"

echo "[launch] agent=$AGENT harness=$HARNESS worktree=${WT_NAME:-none} root=$LAUNCH_ROOT company=$COMPANY_DIR" >&2
[[ -n "$PROMPT" ]] && echo "[launch] first_prompt=${PROMPT:0:160}" >&2

cd "$LAUNCH_ROOT"

case "$HARNESS" in
  grok)
    # Always --cwd of the project (or its git worktree). Never grok --worktree.
    GOPTS=(--agent "$AGENT" --cwd "$LAUNCH_ROOT")
    [[ "$CONTINUE" -eq 1 ]] && GOPTS+=(--continue)
    if [[ -n "$PROMPT" ]]; then exec grok "${GOPTS[@]}" "$PROMPT"
    else exec grok "${GOPTS[@]}"; fi
    ;;
  claude)
    COPTS=(--agent "$AGENT")
    [[ "$CONTINUE" -eq 1 ]] && COPTS+=(--continue)
    if [[ -n "$PROMPT" ]]; then exec claude "${COPTS[@]}" "$PROMPT"
    else exec claude "${COPTS[@]}"; fi
    ;;
  codex)
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
