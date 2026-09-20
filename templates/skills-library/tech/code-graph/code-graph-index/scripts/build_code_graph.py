#!/usr/bin/env python3
"""Build a lightweight code graph for fast agent indexing.

Walks a project root, records files + crude import/include edges, writes:
  graph.json   — full snapshot
  graph.jsonl  — one file record per line (stream-friendly)
  GRAPH.md     — short human summary

Not an LSP/SCIP indexer — good enough to avoid re-walking the whole tree
on every hop. Refresh when the tree changes a lot.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

IGNORE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".jj",
    "node_modules",
    ".build",
    "build",
    "DerivedData",
    "dist",
    "vendor",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "Pods",
    "Carthage",
    "xcuserdata",
    ".gradle",
    "target",
    "out",
    "coverage",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    "Package.resolved",  # file name also filtered below
}

IGNORE_FILE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".bz2",
    ".7z",
    ".rar",
    ".dmg",
    ".app",
    ".framework",
    ".dylib",
    ".so",
    ".a",
    ".o",
    ".class",
    ".jar",
    ".wasm",
    ".mp3",
    ".mp4",
    ".mov",
    ".wav",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".lock",
    ".sum",
}

LANG_BY_EXT = {
    ".swift": "swift",
    ".m": "objc",
    ".mm": "objcpp",
    ".h": "c-header",
    ".hpp": "cpp-header",
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".py": "python",
    ".rb": "ruby",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vue": "vue",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".php": "php",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".marlin": "marlin",
    ".rhai": "rhai",
}

# Crude import/include extractors: (compiled regex, group index of target)
IMPORT_PATTERNS: List[Tuple[re.Pattern[str], int]] = [
    (re.compile(r"^\s*import\s+(?:[\w.]+\s+)?([A-Za-z0-9_./\"'-]+)"), 1),  # swift/java/go-ish
    (re.compile(r"^\s*from\s+([A-Za-z0-9_.]+)\s+import\b"), 1),  # python
    (re.compile(r"^\s*import\s+([A-Za-z0-9_.]+)\b"), 1),  # python
    (re.compile(r"""^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]"""), 1),  # c/c++
    (re.compile(r"""^\s*using\s+([A-Za-z0-9_.]+)\s*;"""), 1),  # csharp
    (re.compile(r"""^\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)"""), 1),  # js
    (re.compile(r"""^\s*from\s+['\"]([^'\"]+)['\"]\s*;?"""), 1),  # js/ts
    (re.compile(r"""^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]"""), 1),  # esm
]

MAX_FILE_BYTES = 1_500_000
MAX_FILES = 20_000


def lang_for(path: Path) -> str:
    return LANG_BY_EXT.get(path.suffix.lower(), "other")


def should_skip_dir(name: str) -> bool:
    return name in IGNORE_DIR_NAMES or name.startswith(".")


def should_skip_file(path: Path) -> bool:
    name = path.name
    if name.startswith(".") and name not in {".env.example"}:
        # keep ordinary dotfiles out of the graph
        if name not in {".gitignore", ".editorconfig"}:
            return True
    if name in {"Package.resolved", "Cargo.lock", "yarn.lock", "package-lock.json", "pnpm-lock.yaml"}:
        return True
    suf = path.suffix.lower()
    if suf in IGNORE_FILE_SUFFIXES:
        return True
    return False


def extract_imports(text: str) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("//") or s.startswith("#") and "include" not in s[:20]:
            # still allow #include via patterns
            pass
        for cre, gi in IMPORT_PATTERNS:
            m = cre.match(line)
            if not m:
                continue
            target = m.group(gi).strip().strip("\"'")
            if not target or target in seen:
                continue
            seen.add(target)
            out.append(target)
            break
    return out


def iter_files(root: Path) -> Iterable[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # prune in-place
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for fn in filenames:
            p = Path(dirpath) / fn
            if should_skip_file(p):
                continue
            yield p
            count += 1
            if count >= MAX_FILES:
                return


def rel_posix(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def build_graph(root: Path) -> Dict:
    root = root.resolve()
    files: List[Dict] = []
    edges: List[Dict] = []
    lang_counts: Counter[str] = Counter()
    errors = 0

    for path in iter_files(root):
        try:
            st = path.stat()
        except OSError:
            errors += 1
            continue
        if st.st_size > MAX_FILE_BYTES:
            continue
        if not path.is_file():
            continue

        rel = rel_posix(root, path)
        lang = lang_for(path)
        lang_counts[lang] += 1
        imports: List[str] = []
        try:
            # binary sniff
            raw = path.read_bytes()[:8192]
            if b"\0" in raw:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            imports = extract_imports(text)
        except OSError:
            errors += 1
            continue

        files.append(
            {
                "path": rel,
                "lang": lang,
                "bytes": st.st_size,
                "mtime": int(st.st_mtime),
                "imports": imports,
            }
        )
        for target in imports:
            edges.append({"from": rel, "to": target, "kind": "import"})

    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "file_count": len(files),
        "edge_count": len(edges),
        "lang_counts": dict(sorted(lang_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "errors": errors,
        "files": files,
        "edges": edges,
    }


def write_outputs(graph: Dict, out_dir: Path) -> Tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "graph.json"
    jsonl_path = out_dir / "graph.jsonl"
    md_path = out_dir / "GRAPH.md"

    json_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in graph["files"]:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Fan-out / fan-in for summary
    fan_out: Counter[str] = Counter()
    fan_in: Counter[str] = Counter()
    for e in graph["edges"]:
        fan_out[e["from"]] += 1
        fan_in[e["to"]] += 1

    lines = [
        f"# Code graph",
        "",
        f"- Generated: `{graph['generated_at']}`",
        f"- Root: `{graph['root']}`",
        f"- Files: **{graph['file_count']}**",
        f"- Import edges: **{graph['edge_count']}**",
        f"- Read errors skipped: {graph['errors']}",
        "",
        "## Languages",
        "",
    ]
    for lang, n in list(graph["lang_counts"].items())[:20]:
        lines.append(f"- `{lang}`: {n}")

    lines += ["", "## Top fan-out (imports many)", ""]
    for path, n in fan_out.most_common(15):
        lines.append(f"- `{path}` → {n}")

    lines += ["", "## Top fan-in targets (imported often)", ""]
    for target, n in fan_in.most_common(15):
        lines.append(f"- `{target}` ← {n}")

    lines += [
        "",
        "## How agents should use this",
        "",
        "1. Read `GRAPH.md` / `graph.json` **before** walking the whole repo.",
        "2. Prefer path + import neighbors from the graph for hop briefs.",
        "3. Ask `code-graph` to refresh after large refactors.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, jsonl_path, md_path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build lightweight code graph for fast indexing")
    ap.add_argument("--root", type=Path, default=Path("."), help="Project root to scan")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: <root>/.agents/code-graph or ./cache/code-graph)",
    )
    args = ap.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    out = args.out
    if out is None:
        agents = root / ".agents"
        if agents.is_dir():
            out = agents / "code-graph"
        else:
            out = root / "cache" / "code-graph"
    out = out.resolve()

    graph = build_graph(root)
    json_path, jsonl_path, md_path = write_outputs(graph, out)
    print(f"code-graph: files={graph['file_count']} edges={graph['edge_count']}")
    print(f"  {json_path}")
    print(f"  {jsonl_path}")
    print(f"  {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
