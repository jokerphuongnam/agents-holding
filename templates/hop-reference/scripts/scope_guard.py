#!/usr/bin/env python3
"""Enforce child-company filesystem scope (tool-level check).

Child agents MUST call this before reading/writing paths outside the company
cwd. Out of scope → deny + escalate to parent ceo (grants/info).

  python3 …/scope_guard.py check --path <path>
  python3 …/scope_guard.py roots
  python3 …/scope_guard.py write-scope-md   # refresh SCOPE.md

Exit 0 = allow; exit 2 = deny (stdout still prints handoff hints).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home  # type: ignore


def data_dir(home: Path | None = None) -> Path:
    home = home or agents_home()
    return home / "system" / "skills" / "defaults" / "marlin-hop" / "data"


def load_parent_meta(home: Path) -> dict[str, str]:
    path = data_dir(home) / "parent.tsv"
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return out
    header = lines[0].split("\t")
    if "key" not in header or "value" not in header:
        return out
    ik, iv = header.index("key"), header.index("value")
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = ln.split("\t")
        while len(cells) <= max(ik, iv):
            cells.append("")
        if cells[ik]:
            out[cells[ik]] = cells[iv]
    return out


def load_scope_prefixes(home: Path) -> list[str]:
    path = data_dir(home) / "scope_allow.tsv"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    if "prefix" not in header:
        return []
    ip = header.index("prefix")
    out: list[str] = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = ln.split("\t")
        if len(cells) > ip and cells[ip].strip():
            out.append(cells[ip].strip())
    return out


def meta_project_root(home: Path) -> Path | None:
    """Read siblings META.toml (…/children/<stem>/META.toml)."""
    meta = home.parent / "META.toml"
    if not meta.is_file():
        return None
    for ln in meta.read_text(encoding="utf-8").splitlines():
        if ln.strip().startswith("project_root"):
            _, _, val = ln.partition("=")
            val = val.strip().strip('"').strip("'")
            if val:
                p = Path(val).expanduser()
                return p if p.is_absolute() else (home / val).resolve()
    return None


def allowed_roots(home: Path | None = None) -> list[Path]:
    home = (home or agents_home()).resolve()
    roots = [home]
    pkg = meta_project_root(home)
    if pkg is not None:
        roots.append(pkg.resolve())
    # Dedup
    out: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        key = str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def resolve_candidate(raw: str, home: Path) -> Path:
    p = Path(raw).expanduser()
    if not p.is_absolute():
        # Prefer resolve against cwd, then against company home
        cwd_try = (Path.cwd() / p)
        if cwd_try.exists() or str(p).startswith(".."):
            try:
                return cwd_try.resolve()
            except OSError:
                pass
        return (home / p).resolve()
    return p.resolve()


def is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def check_path(raw: str, home: Path | None = None) -> tuple[bool, str]:
    home = (home or agents_home()).resolve()
    parent = load_parent_meta(home)
    prefixes = load_scope_prefixes(home)
    # Not a fenced child → allow
    if not parent and not prefixes:
        return True, "allow\tunfenced"

    cand = resolve_candidate(raw, home)
    for root in allowed_roots(home):
        if is_under(cand, root):
            return True, f"allow\tunder\t{root}"

    # Relative prefix match when path is still relative-ish
    norm = raw.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    for pref in prefixes:
        pref_n = pref.rstrip("/")
        if norm == pref_n or norm.startswith(pref) or norm.startswith(pref_n + "/"):
            # Still require it doesn't escape via .. after join
            joined = (home / norm).resolve()
            if any(is_under(joined, r) for r in allowed_roots(home)):
                return True, f"allow\tprefix\t{pref}"

    slug = parent.get("slug", "(parent)")
    cpath = parent.get("company_path", "")
    channel = parent.get("channel", "ceo")
    detail = (
        f"deny\thandoff:parent\tparent_slug={slug}\t"
        f"parent_channel={channel}\tparent_company={cpath}\t"
        f"path={cand}"
    )
    return False, detail


def write_scope_md(home: Path | None = None) -> Path:
    home = (home or agents_home()).resolve()
    parent = load_parent_meta(home)
    roots = allowed_roots(home)
    prefixes = load_scope_prefixes(home)
    lines = [
        "# SCOPE — child company fence",
        "",
        "This Company OS is a **child**. Agents may only read/write under the",
        "roots below. Anything else → escalate to **parent ceo** for grants/info",
        "(do not open parent/sibling trees).",
        "",
        "## Allowed roots",
        "",
    ]
    for r in roots:
        lines.append(f"- `{r}`")
    lines += ["", "## Hop allow prefixes", ""]
    for p in prefixes:
        lines.append(f"- `{p}`")
    if parent:
        lines += [
            "",
            "## Escalate",
            "",
            f"- Parent slug: `{parent.get('slug', '')}`",
            f"- Parent path: `{parent.get('company_path', '')}`",
            f"- Channel: `{parent.get('channel', 'ceo')}`",
            "",
            "```bash",
            "python3 system/skills/defaults/marlin-hop/scripts/scope_guard.py check --path <path>",
            "python3 system/skills/defaults/marlin-hop/scripts/hop.py --path <path>",
            "```",
            "",
        ]
    out = home / "SCOPE.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Child company scope guard")
    ap.add_argument("--company", default="", help="Company OS root (default: discover)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    chk = sub.add_parser("check", help="Allow/deny a path")
    chk.add_argument("--path", required=True)

    sub.add_parser("roots", help="Print allowed roots")
    sub.add_parser("write-scope-md", help="Write/refresh SCOPE.md")

    args = ap.parse_args()
    home = Path(args.company).resolve() if args.company else agents_home()

    if args.cmd == "roots":
        for r in allowed_roots(home):
            print(r)
        return 0
    if args.cmd == "write-scope-md":
        path = write_scope_md(home)
        print(f"wrote\t{path}")
        return 0
    if args.cmd == "check":
        # Temporarily pretend data_dir via chdir to company for load_tsv callers
        ok, detail = check_path(args.path, home)
        print(detail)
        if ok:
            print("rule\tagent may read/write this path")
            return 0
        print(
            "rule\tdeny — spawn parent ceo only; ask grants/info; "
            "do not open parent/sibling trees"
        )
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
