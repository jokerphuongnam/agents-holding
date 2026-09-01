#!/usr/bin/env python3
"""Compress a qa/run_all.sh or run_tests.sh log to failing sections only.

Does not pick the IC (CEO runs hop.py). Replaces stuffing the raw log.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# stdin/file only — no .agents required

SECTION = re.compile(r"═+\s*(.+?)\s*═+")
LESSON = re.compile(r"▸\s+(\S+)")
FAIL = re.compile(
    r"(?i)(\bFAIL\b|\bFAILED\b|error:|fatal error:|exit code [1-9]|SIGKILL|killed|timeout)"
)
FILE_HIT = re.compile(
    r"((?:src|libraries|communication|mpm|sdk|qa|tools|reports)/[^\s:]+)"
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract QA failures from a log")
    ap.add_argument("log", nargs="?", help="log file; stdin if omitted")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()
    if args.log:
        text = Path(args.log).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("empty log")
        return 1

    current_section = ""
    current_lesson = ""
    blocks: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for line in text.splitlines():
        sm = SECTION.search(line)
        if sm:
            current_section = sm.group(1).strip()
            current_lesson = ""
            continue
        lm = LESSON.search(line)
        if lm:
            current_lesson = lm.group(1).strip()
        if not FAIL.search(line):
            continue
        files = FILE_HIT.findall(line)
        file_s = files[0] if files else ""
        key = (current_section, current_lesson, file_s)
        if key in seen:
            continue
        seen.add(key)
        blocks.append(
            {
                "section": current_section,
                "lesson": current_lesson,
                "file": file_s,
                "line": line.strip()[:240],
            }
        )
        if len(blocks) >= args.limit:
            break

    if not blocks:
        print("no FAIL/error lines — do not dump the log into context")
        return 0

    print(f"fails: {len(blocks)} (limit {args.limit})")
    for i, b in enumerate(blocks, 1):
        print(f"{i}. section: {b['section'] or '?'}")
        if b["lesson"]:
            print(f"   lesson: {b['lesson']}")
        if b["file"]:
            print(f"   file: {b['file']}")
        print(f"   hit: {b['line']}")
        if b["file"]:
            print(f"   next: python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --path {b['file']}")
        elif b["lesson"]:
            print(f"   next: python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --lesson {b['lesson']}")
        elif b["section"]:
            print(f"   next: python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --section {b['section']!r}")
    print("do_not: read ORG.md, grep source, or pick the IC before hop.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
