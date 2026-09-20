#!/usr/bin/env python3
"""Tool gate: staffs that need Code Prism on PATH before spawn/work.

Used by hop.py when the routed agent is `code-graph` (hired or not — if hop
targets it, Prism must exist). Also runnable standalone:

  python3 require_prism.py              # exit 0 ready / 1 missing
  python3 require_prism.py --agent code-graph
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/code-prism-cli/main/install.sh | bash"
)

# Staff ids that must not spawn / work without Prism.
STAFF_REQUIRING_PRISM = frozenset({"code-graph"})


def resolve_bin(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    home = Path.home()
    for p in (
        home / "bin" / name,
        home / ".local" / "bin" / name,
        home / "Documents" / "Code" / "code-prism-cli" / "bin" / name,
    ):
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


def check() -> tuple[bool, str | None, str | None]:
    prism = resolve_bin("prism")
    mcp = resolve_bin("prism-mcp")
    return bool(prism and mcp), prism, mcp


def emit_gate_for_agent(agent: str) -> int:
    """Print gate lines for hop stdout. Return 0 ok, 3 blocked (do not spawn)."""
    if agent not in STAFF_REQUIRING_PRISM:
        return 0
    ready, prism, mcp = check()
    if ready:
        print(f"gate:prism=ready\tprism={prism}\tprism-mcp={mcp}")
        return 0
    print("gate:prism=missing\tASK_INSTALL")
    print(f"gate:install\t{INSTALL}")
    print(
        "gate:rule\tdo NOT spawn code-graph; ask user to install Code Prism; "
        "on yes run gate:install; re-hop only after ready"
    )
    return 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--agent",
        default="code-graph",
        help="Staff id to gate (default code-graph)",
    )
    args = ap.parse_args()
    if args.agent not in STAFF_REQUIRING_PRISM:
        print(f"ok\tno prism gate for agent={args.agent}")
        return 0
    code = emit_gate_for_agent(args.agent)
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
