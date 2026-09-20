#!/usr/bin/env python3
"""Gate for hiring/using the code-graph staff (Code Prism).

Exit codes:
  0 — prism + prism-mcp on PATH (ready to hire / use)
  1 — missing one or both
  2 — usage error

Stdout (TSV): status\tprism\tprism-mcp\tmessage
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


def resolve_bin(name: str) -> str | None:
    """PATH first, then install.sh defaults (~/bin, Documents/Code checkout)."""
    found = shutil.which(name)
    if found:
        return found
    home = Path.home()
    candidates = [
        home / "bin" / name,
        home / ".local" / "bin" / name,
        home / "Documents" / "Code" / "code-prism-cli" / "bin" / name,
    ]
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of TSV",
    )
    args = ap.parse_args()

    prism = resolve_bin("prism")
    mcp = resolve_bin("prism-mcp")
    ready = bool(prism and mcp)

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "ready": ready,
                    "prism": prism,
                    "prism_mcp": mcp,
                    "install": INSTALL,
                    "message": (
                        "Code Prism ready — code-graph may be hired."
                        if ready
                        else "Code Prism not installed — ask the developer before hiring code-graph."
                    ),
                },
                indent=2,
            )
        )
    else:
        status = "ready" if ready else "missing"
        msg = (
            "ok"
            if ready
            else f"ask user to install; if yes run: {INSTALL}"
        )
        print(f"{status}\t{prism or '-'}\t{mcp or '-'}\t{msg}")

    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
