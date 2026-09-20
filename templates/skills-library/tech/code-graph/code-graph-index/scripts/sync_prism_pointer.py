#!/usr/bin/env python3
"""Write a thin company cache/code-graph pointer to Code Prism system SoT.

Does not re-implement indexing — calls `prism analyze` (optional) and records
where MCP should look. Homemade build_code_graph.py is deprecated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sanitize_name(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
    return s or "project"


def project_slug(root: Path) -> str:
    real = root.resolve()
    digest = hashlib.sha256(str(real).encode()).hexdigest()[:16]
    return f"{sanitize_name(real.name)}-{digest}"


def cache_root() -> Path:
    return Path.home() / "Library" / "Caches" / "code-prism"


def which_prism() -> str | None:
    return shutil.which("prism")


def run_analyze(root: Path) -> subprocess.CompletedProcess[str] | None:
    prism = which_prism()
    if not prism:
        return None
    return subprocess.run(
        [prism, "analyze", "--root", str(root)],
        capture_output=True,
        text=True,
    )


def lang_folders(slug_dir: Path) -> list[Path]:
    if not slug_dir.is_dir():
        return []
    return sorted(p for p in slug_dir.iterdir() if p.is_dir() and p.name.endswith("-prism"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="Project source root")
    ap.add_argument("--out", required=True, help="Company cache/code-graph dir")
    ap.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Only write pointer from existing system cache",
    )
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not root.is_dir():
        print(f"error: root not found: {root}", file=sys.stderr)
        return 2

    analyze_ok = None
    analyze_out = ""
    if not args.skip_analyze:
        if not which_prism():
            print(
                "error: `prism` not on PATH.\n"
                "  curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/code-prism-cli/main/install.sh | bash",
                file=sys.stderr,
            )
            return 3
        proc = run_analyze(root)
        assert proc is not None
        analyze_out = (proc.stdout or "") + (proc.stderr or "")
        analyze_ok = proc.returncode == 0
        if not analyze_ok:
            print(analyze_out, file=sys.stderr)
            print(f"error: prism analyze exited {proc.returncode}", file=sys.stderr)
            return proc.returncode or 1

    slug = project_slug(root)
    slug_dir = cache_root() / slug
    langs = lang_folders(slug_dir)

    out.mkdir(parents=True, exist_ok=True)
    pointer = {
        "engine": "code-prism",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(root),
        "projectSlug": slug,
        "systemCacheDir": str(slug_dir),
        "languages": [p.name.replace("-prism", "") for p in langs],
        "langCaches": {
            p.name: {
                "dir": str(p),
                "json": str(p / "prism-context.json") if (p / "prism-context.json").exists() else None,
                "sqlite": str(p / "graph.sqlite") if (p / "graph.sqlite").exists() else None,
            }
            for p in langs
        },
        "mcp": {
            "command": "prism-mcp",
            "args_path": [str(root)],
            "args_short_name": [root.name],
            "tools": [
                "get_project_summary",
                "search_symbols",
                "resolve_symbol",
                "ask_graph",
                "get_node_info",
                "get_smart_context",
            ],
        },
        "analyzeOk": analyze_ok,
        "deprecated": "Do not use build_code_graph.py — SoT is Code Prism system cache.",
    }
    (out / "prism-pointer.json").write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")

    lang_lines = "\n".join(f"- `{p.name}` → `{p}`" for p in langs) or "- _(no lang cache yet — run prism analyze)_"
    md = f"""# Code graph (Code Prism)

Project: `{root}`  
Slug: `{slug}`  
System SoT: `{slug_dir}`

## Languages

{lang_lines}

## Refresh

```bash
prism analyze --root "{root}"
```

## Query (MCP)

```bash
prism-mcp "{root}"
# or: prism-mcp {root.name}
```

Prefer tools: `ask_graph`, `resolve_symbol`, `search_symbols`, `get_project_summary`, `get_node_info`, `get_smart_context`.

This folder is a **pointer only**. Do not treat old `graph.json` from `build_code_graph.py` as source of truth.
"""
    (out / "GRAPH.md").write_text(md, encoding="utf-8")

    # Leave a stub so old callers notice deprecation
    deprecated = out / "DEPRECATED_build_code_graph.txt"
    deprecated.write_text(
        "build_code_graph.py is deprecated. Use Code Prism:\n"
        "  curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/code-prism-cli/main/install.sh | bash\n"
        "  prism analyze --root <project>\n"
        "  prism-mcp <project>\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "out": str(out), "slug": slug, "langs": pointer["languages"]}, indent=2))
    print(str(out / "GRAPH.md"))
    print(str(out / "prism-pointer.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
