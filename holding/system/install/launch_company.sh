#!/usr/bin/env bash
# Shared Company OS launcher — used by every company (parent + children).
# Always talks to CEO directly. First prompt = remaining args.
#
#   launch_company.sh --company-dir <abs> --root <abs> <harness|merge> [--fresh] ["prompt…"]
#
set -euo pipefail

COMPANY_DIR=""
ROOT=""
FRESH=0
ARGS=()

usage() {
  cat <<'USAGE'
launch_company.sh --company-dir DIR --root DIR <harness|merge> [--fresh] ["prompt…"]

Always: CEO chat for that company. Default continues prior session.
  grok|claude|codex  → that CLI as ceo
  merge              → company_os all + CEO on runtime_router default
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    --fresh) FRESH=1; shift ;;
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

echo "[launch] ceo=direct harness=$HARNESS fresh=$FRESH root=$ROOT company=$COMPANY_DIR" >&2
[[ -n "$PROMPT" ]] && echo "[launch] first_prompt=${PROMPT:0:160}" >&2
cd "$ROOT"

case "$HARNESS" in
  grok)
    GOPTS=(--agent ceo --cwd "$ROOT")
    [[ "$FRESH" -eq 0 ]] && GOPTS+=(--continue)
    if [[ -n "$PROMPT" ]]; then exec grok "${GOPTS[@]}" "$PROMPT"
    else exec grok "${GOPTS[@]}"; fi
    ;;
  claude)
    COPTS=(--agent ceo)
    [[ "$FRESH" -eq 0 ]] && COPTS+=(--continue)
    if [[ -n "$PROMPT" ]]; then exec claude "${COPTS[@]}" "$PROMPT"
    else exec claude "${COPTS[@]}"; fi
    ;;
  codex)
    if [[ "$FRESH" -eq 0 ]]; then
      if [[ -n "$PROMPT" ]]; then exec codex resume --last "$PROMPT" 2>/dev/null || exec codex "$PROMPT"
      else exec codex resume --last 2>/dev/null || exec codex; fi
    else
      if [[ -n "$PROMPT" ]]; then exec codex "$PROMPT"; else exec codex; fi
    fi
    ;;
  *)
    echo "error: no CEO launch wiring for harness='$HARNESS'" >&2
    exit 2
    ;;
esac
