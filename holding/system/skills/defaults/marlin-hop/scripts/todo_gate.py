#!/usr/bin/env python3
"""Structural QA for the todo-list MPM Service eval.

Pass = MPM Application service backend with Service + ServiceDatabase +
UnitTest + a Service test. Used as the 'when is it done' gate.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def scan(root: Path) -> dict:
    root = root.resolve()
    marlin = list(root.rglob("*.marlin"))
    headers = list(root.rglob("*.marlinheader"))
    texts = {p: _read(p) for p in marlin + headers}
    blob = "\n".join(texts.values())

    def any_re(pat: str) -> bool:
        return re.search(pat, blob, re.I | re.M) is not None

    checks = {
        "application_manifest": any(
            "@manifest" in t and "Application" in t for t in texts.values()
        ),
        "service_product": any_re(r"application\(\s*\.service\s*\)|\.service\b"),
        "import_service": any_re(r"^import Service\b"),
        "import_service_database": any_re(r"^import ServiceDatabase\b"),
        "http_get": any_re(r"\bGET\s*\("),
        "http_post": any_re(r"\bPOST\s*\("),
        "todo_surface": any_re(r"todo"),
        "is_test_target": any_re(r"isTestTarget:\s*true"),
        "unittest_import": any_re(r"^import UnitTest\b"),
        "testcase": any_re(r":\s*(TestCase|MarloutineTestCase)\b"),
        "service_test": any(
            re.search(r"^import Service\b", t, re.M)
            and re.search(r"TestCase|ServiceTestApplication", t)
            for t in texts.values()
        ),
    }
    missing = [k for k, v in checks.items() if not v]
    files = sorted(str(p.relative_to(root)) for p in marlin + headers)
    n_tests = len(re.findall(r"func test\w*\s*\(", blob))
    crud = sum(bool(re.search(rf"\b{v}\s*\(", blob)) for v in ("GET", "POST", "PUT", "PATCH", "DELETE"))
    uses_sql_string = bool(re.search(r"CREATE TABLE|INSERT INTO", blob, re.I))
    uses_entity = bool(re.search(r"\b(Entity|registerTable|FetchRequest)\b", blob))
    quality = {
        "layout_sources_tests": (root / "Sources").is_dir() and (
            (root / "Tests").is_dir() or checks["is_test_target"]
        ),
        "rest_methods": crud,
        "test_funcs": n_tests,
        "prefer_entity_over_raw_sql": uses_entity and not uses_sql_string,
        "file_count": len(files),
    }
    score = 0.0
    score += 6.0 * (len(checks) - len(missing)) / len(checks)
    score += 1.0 if quality["layout_sources_tests"] else 0
    score += min(1.5, 0.3 * n_tests)
    score += min(1.0, 0.2 * crud)
    score += 0.5 if quality["prefer_entity_over_raw_sql"] else 0
    return {
        "pass": not missing,
        "missing": missing,
        "checks": checks,
        "files": files,
        "quality": quality,
        "score_0_10": round(min(10.0, score), 2),
        "follow_up": (
            "Missing: " + ", ".join(missing) + ". Continue in the same project; do not re-ask."
            if missing
            else "QA gate pass."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    args = ap.parse_args()
    report = scan(Path(args.root))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
