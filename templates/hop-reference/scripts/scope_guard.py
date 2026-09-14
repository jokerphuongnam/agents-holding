#!/usr/bin/env python3
"""Enforce child-company filesystem scope (tool-level check).

Own roots (company folder + package): read/write.
GRANTS.toml paths/artifacts from parent: **read-only**.
Anything else: deny → escalate to parent ceo.

  python3 …/scope_guard.py check --path <path> [--write]
  python3 …/scope_guard.py roots
  python3 …/scope_guard.py grants
  python3 …/scope_guard.py write-scope-md

Exit 0 = allow (rw or ro); exit 2 = deny.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home  # type: ignore

# allow_rw | allow_ro | deny
AllowLevel = str


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


def meta_file(home: Path) -> Path:
    return home.parent / "META.toml"


def grants_file(home: Path) -> Path:
    return home.parent / "GRANTS.toml"


def meta_project_root(home: Path) -> Path | None:
    """Read siblings META.toml (…/children/<stem>/META.toml)."""
    meta = meta_file(home)
    if not meta.is_file():
        return None
    for ln in meta.read_text(encoding="utf-8").splitlines():
        if ln.strip().startswith("project_root"):
            _, _, val = ln.partition("=")
            val = val.strip().strip('"').strip("'")
            if val:
                p = Path(val).expanduser()
                return p.resolve() if p.is_absolute() else (home / val).resolve()
    return None


def parent_project_root(home: Path) -> Path:
    """Directory that owns `.agents/` (parent product root for grant paths)."""
    for d in [home, *home.parents]:
        if d.name == ".agents":
            return d.parent
    return home.parent


def _parse_toml_str_list(text: str, key: str) -> list[str]:
    """Minimal parse for `key = [ \"a\", \"b\" ]` (no full TOML dependency)."""
    m = re.search(
        rf"(?m)^{re.escape(key)}\s*=\s*\[(.*?)\]",
        text,
        flags=re.S,
    )
    if not m:
        return []
    body = m.group(1)
    return [s.strip() for s in re.findall(r'"([^"]*)"|\'([^\']*)\'', body) for s in s if s]


def load_grant_targets(home: Path) -> list[Path]:
    """Resolve GRANTS.toml paths_readonly + artifacts under parent project root."""
    gf = grants_file(home)
    if not gf.is_file():
        return []
    text = gf.read_text(encoding="utf-8")
    rels = _parse_toml_str_list(text, "paths_readonly") + _parse_toml_str_list(
        text, "artifacts"
    )
    root = parent_project_root(home)
    out: list[Path] = []
    for rel in rels:
        rel = rel.strip()
        if not rel or rel.startswith("#"):
            continue
        p = Path(rel).expanduser()
        target = p.resolve() if p.is_absolute() else (root / rel).resolve()
        out.append(target)
    # dedup
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        k = str(p)
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq


def allowed_roots(home: Path | None = None) -> list[Path]:
    """Read/write roots: child company OS + package."""
    home = (home or agents_home()).resolve()
    roots = [home]
    pkg = meta_project_root(home)
    if pkg is not None:
        roots.append(pkg.resolve())
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
        cwd_try = Path.cwd() / p
        if cwd_try.exists() or str(p).startswith(".."):
            try:
                return cwd_try.resolve()
            except OSError:
                pass
        # Also try against parent project root (grant-relative paths)
        try:
            return (parent_project_root(home) / p).resolve()
        except OSError:
            return (home / p).resolve()
    return p.resolve()


def is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def classify_path(
    raw: str, home: Path | None = None, *, want_write: bool = False
) -> tuple[AllowLevel, str]:
    """Return (allow_rw|allow_ro|deny, detail_tsv)."""
    home = (home or agents_home()).resolve()
    parent = load_parent_meta(home)
    prefixes = load_scope_prefixes(home)
    if not parent and not prefixes:
        return "allow_rw", "allow_rw\tunfenced"

    cand = resolve_candidate(raw, home)

    # 1) Own roots — read/write
    for root in allowed_roots(home):
        if is_under(cand, root):
            return "allow_rw", f"allow_rw\tunder\t{root}"

    norm = raw.strip().replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    for pref in prefixes:
        pref_n = pref.rstrip("/")
        if norm == pref_n or norm.startswith(pref) or norm.startswith(pref_n + "/"):
            joined = (home / norm).resolve()
            if any(is_under(joined, r) for r in allowed_roots(home)):
                return "allow_rw", f"allow_rw\tprefix\t{pref}"

    # 2) Parent grants — read-only
    grants = load_grant_targets(home)
    for g in grants:
        if cand == g or is_under(cand, g) or (g.is_file() and cand == g):
            if want_write:
                return (
                    "deny",
                    f"deny\tgrant_readonly\tgrant={g}\tpath={cand}\t"
                    f"hint=ask parent ceo to widen grants or copy into child",
                )
            return "allow_ro", f"allow_ro\tgrant\t{g}"

    # Relative grant match (e.g. documents/x.md)
    for g in grants:
        try:
            rel = str(g.relative_to(parent_project_root(home))).replace("\\", "/")
        except ValueError:
            rel = g.name
        if norm == rel or norm.rstrip("/") == rel.rstrip("/") or norm.startswith(
            rel.rstrip("/") + "/"
        ):
            if want_write:
                return (
                    "deny",
                    f"deny\tgrant_readonly\tgrant={g}\tpath={cand}",
                )
            return "allow_ro", f"allow_ro\tgrant_rel\t{g}"

    slug = parent.get("slug", "(parent)")
    cpath = parent.get("company_path", "")
    channel = parent.get("channel", "ceo")
    detail = (
        f"deny\thandoff:parent\tparent_slug={slug}\t"
        f"parent_channel={channel}\tparent_company={cpath}\t"
        f"path={cand}"
    )
    return "deny", detail


def check_path(raw: str, home: Path | None = None) -> tuple[bool, str]:
    level, detail = classify_path(raw, home, want_write=False)
    return level != "deny", detail


def write_scope_md(home: Path | None = None) -> Path:
    home = (home or agents_home()).resolve()
    parent = load_parent_meta(home)
    roots = allowed_roots(home)
    prefixes = load_scope_prefixes(home)
    grants = load_grant_targets(home)
    lines = [
        "# SCOPE — child company fence",
        "",
        "This Company OS is a **child**.",
        "",
        "## Read/write roots (own)",
        "",
    ]
    for r in roots:
        lines.append(f"- `{r}`")
    lines += [
        "",
        "## Read-only grants (from parent `GRANTS.toml`)",
        "",
    ]
    if grants:
        for g in grants:
            lines.append(f"- `{g}` *(RO)*")
    else:
        lines.append("- *(none — ask parent ceo to add grants)*")
    lines += ["", "## Hop allow prefixes (own work)", ""]
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
            "Need a path **not** listed above → parent ceo (more grants/info).",
            "Do **not** open sibling children or ungated parent trees.",
            "",
            "```bash",
            "python3 system/skills/defaults/marlin-hop/scripts/scope_guard.py check --path <path>",
            "python3 system/skills/defaults/marlin-hop/scripts/scope_guard.py check --path <path> --write",
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
    chk.add_argument(
        "--write",
        action="store_true",
        help="Require write access (grant paths will deny)",
    )

    sub.add_parser("roots", help="Print read/write roots")
    sub.add_parser("grants", help="Print read-only grant targets")
    sub.add_parser("write-scope-md", help="Write/refresh SCOPE.md")

    args = ap.parse_args()
    home = Path(args.company).resolve() if args.company else agents_home()

    if args.cmd == "roots":
        for r in allowed_roots(home):
            print(r)
        return 0
    if args.cmd == "grants":
        for g in load_grant_targets(home):
            print(g)
        return 0
    if args.cmd == "write-scope-md":
        path = write_scope_md(home)
        print(f"wrote\t{path}")
        return 0
    if args.cmd == "check":
        level, detail = classify_path(
            args.path, home, want_write=bool(args.write)
        )
        print(detail)
        if level == "allow_rw":
            print("rule\tagent may read/write this path")
            return 0
        if level == "allow_ro":
            print(
                "rule\tagent may READ only (parent grant) — do not write; "
                "do not treat as work root"
            )
            return 0
        print(
            "rule\tdeny — spawn parent ceo only; ask grants/info; "
            "do not open parent/sibling trees"
        )
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
