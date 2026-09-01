#!/usr/bin/env python3
"""Grep one team graph. Replaces reading .agents/marlin-language-company/cache/graphs/<team>.md whole."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home


def main() -> int:
    ap = argparse.ArgumentParser(description="Slice a team graph by substring")
    ap.add_argument("--team", required=True, help="marlin|libraries|sdk|communication|mpm|tools|qa|infra-engineer")
    ap.add_argument("-q", "--query", required=True, help="case-insensitive substring")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()
    graph = agents_home() / "graphs" / f"{args.team}.md"
    if not graph.is_file():
        print(f"need-graph: {args.team}")
        return 2
    q = args.query.lower()
    hits: list[str] = []
    section = ""
    for line in graph.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if q in line.lower():
            prefix = f"[{section}] " if section else ""
            hits.append(prefix + line.rstrip())
            if len(hits) >= args.limit:
                break
    if not hits:
        print(f"no-match: {args.team} q={args.query!r}")
        print("do_not: grep the repo; return need-graph if the symbol should exist")
        return 1
    print(f"graph: .agents/marlin-language-company/cache/graphs/{args.team}.md")
    print(f"hits: {len(hits)} (limit {args.limit})")
    for h in hits:
        print(h)
    print("do_not: read the whole graph file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
