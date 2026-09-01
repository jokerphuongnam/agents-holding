#!/usr/bin/env python3
"""Quality rubric for TodoListAB. Gate (todo_gate) is pass/fail only.

Scores 0-10. Near-clone trees can share a score — that is a finding, not a
checklist trick.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def blob(root: Path) -> str:
    parts = []
    for p in sorted(root.rglob("*.marlin")):
        parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def score(root: Path) -> dict:
    text = blob(root)
    n_lines = text.count("\n") + 1 if text else 0
    handlers = len(re.findall(r"\b(GET|POST|PUT|PATCH|DELETE)\s*\(", text))
    catch500 = text.count("status: 500")
    scratch = "TodoRequestScratch" in text or "static var" in text
    entity = bool(re.search(r"\b(Entity|registerTable|FetchRequest)\b", text))
    raw_sql = bool(re.search(r"CREATE TABLE|SELECT .+ FROM", text, re.I))
    mixed = ("database.sql()" in text) and (".insert(" in text or ".fetch(" in text)
    secret = 'password: "marlin"' in text or "password: \"marlin\"" in text
    wrapper_noise = len(re.findall(r"public func \w+Path\(\)", text))
    tests = len(re.findall(r"func test\w*\s*\(", text))
    sut = "ServiceTestApplication" in text and "tearDown" in text
    god = any(
        p.name == "main.marlin" and p.read_text().count("\n") > 200
        for p in root.rglob("*.marlin")
    )

    # Heuristic 0-10. Same smells → same numbers (clones are allowed to tie).
    clean = 10.0
    clean -= 2.5 if catch500 >= 8 else 0  # copy-paste error paths
    clean -= 2.0 if scratch else 0  # global mutable request scratch
    clean -= 1.5 if mixed else 0
    clean -= 1.0 if secret else 0
    clean -= 0.5 if wrapper_noise >= 3 else 0
    clean = max(0.0, min(10.0, clean))

    extend = 10.0
    extend -= 3.0 if not entity and raw_sql else 0
    extend -= 2.0 if god else 0
    extend -= 1.5 if scratch else 0  # cannot add fields without touching globals
    extend -= 1.0 if mixed else 0
    extend = max(0.0, min(10.0, extend))

    read = 10.0
    read -= 2.0 if god else 0
    read -= 1.0 if wrapper_noise >= 3 else 0
    read -= 1.0 if catch500 >= 8 else 0
    read += 0.5 if "TodoItem" in text else 0
    read = max(0.0, min(10.0, read))

    write = 10.0
    write -= 2.5 if catch500 >= 8 else 0  # add route = paste 40 lines
    write -= 2.0 if scratch else 0
    write -= 1.5 if not entity else 0
    write = max(0.0, min(10.0, write))

    test_q = 10.0
    test_q -= 3.0 if tests < 3 else 0
    test_q += 1.0 if sut else 0
    test_q -= 1.0 if "testTodoPathHelpers" in text and tests <= 2 else 0
    test_q = max(0.0, min(10.0, test_q))

    overall = round((clean + extend + read + write + test_q) / 5.0, 2)
    return {
        "clean_code": round(clean, 2),
        "extensibility": round(extend, 2),
        "readability": round(read, 2),
        "easy_to_change": round(write, 2),
        "tests": round(test_q, 2),
        "overall": overall,
        "smells": {
            "lines": n_lines,
            "http_handlers": handlers,
            "duplicated_500": catch500,
            "static_request_scratch": scratch,
            "entity_orm": entity,
            "raw_sql": raw_sql,
            "mixed_sql_and_typed": mixed,
            "hardcoded_db_secret": secret,
            "god_main": god,
            "test_funcs": tests,
            "service_sut_lifecycle": sut,
        },
        "notes": [
            "Static TodoRequestScratch is shared mutable state across requests.",
            "CRUD handlers copy the same try/catch/500 block (~13 times).",
            "List uses raw SQL; create/update use typed insert/fetch — mixed persistence.",
            "No Entity/registerTable; schema is a SQL string.",
            "MySQL password hardcoded.",
            "main.marlin is a god handler (>200 lines) — adding a field touches every route.",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    print(json.dumps(score(Path(args.root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
