#!/usr/bin/env python3
"""Parent→child CEO — map fuzzy company name → path → launch or brief.

Parent ceo says which child they're working with (approx name OK). Script maps
to the child company, resolves path, then either:

  launch (default when a prompt is given)
      child .grok/launch-ceo.sh \"prompt…\"
  brief
      print spawn lines for in-session child ceo (no TUI)

Examples:
  handoff_child.py desk-garden \"spike Unity embed\"
  handoff_child.py \"desk garden\" \"Marlin tick\"
  handoff_child.py dg --brief --goal '…'
  handoff_child.py --path projects/desk-garden/Sources --goal '…'
  handoff_child.py --list
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
DATA = SCRIPTS.parent / "data"
COMPANY = SCRIPTS.parents[4]
REPO = COMPANY.parent.parent if COMPANY.parent.name == ".agents" else COMPANY.parent


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" company", "").strip()
    return s


def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(s))


def load_children_tsv() -> list[tuple[str, str, str]]:
    path = DATA / "children.tsv"
    if not path.is_file():
        return []
    rows: list[tuple[str, str, str]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip() or (i == 0 and line.lower().startswith("prefix")):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return rows


def load_aliases() -> dict[str, str]:
    path = DATA / "children_aliases.tsv"
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip() or (i == 0 and line.lower().startswith("alias")):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            out[_norm(parts[0])] = parts[1].strip()
            out[_compact(parts[0])] = parts[1].strip()
    return out


def registry_list() -> list[dict[str, str]]:
    reg = Path.home() / ".agents/holding/system/install/children_registry.py"
    if not reg.is_file():
        alt = REPO / ".agents/holding/system/install/children_registry.py"
        reg = alt if alt.is_file() else reg
    if not reg.is_file():
        return []
    try:
        out = subprocess.check_output(
            [sys.executable, str(reg), "--parent", str(COMPANY), "list"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in out.splitlines():
        if line.startswith("cols\t"):
            headers = line.split("\t")[1:]
            continue
        if line.startswith("row\t") and headers:
            vals = line.split("\t")[1:]
            rows.append(dict(zip(headers, vals)))
    return rows


def registry_row(slug: str) -> dict[str, str] | None:
    full = slug if slug.endswith("-company") else f"{slug}-company"
    for row in registry_list():
        if row.get("slug") == full or row.get("slug") == slug:
            return row
    # fallback show
    reg = Path.home() / ".agents/holding/system/install/children_registry.py"
    if not reg.is_file():
        alt = REPO / ".agents/holding/system/install/children_registry.py"
        reg = alt if alt.is_file() else reg
    if not reg.is_file():
        return None
    for cand in (full, slug):
        try:
            out = subprocess.check_output(
                [sys.executable, str(reg), "--parent", str(COMPANY), "show", "--slug", cand],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue
        row: dict[str, str] = {}
        for line in out.splitlines():
            if "\t" in line:
                k, v = line.split("\t", 1)
                row[k.strip()] = v.strip()
        if row.get("company_path"):
            return row
    return None


def resolve_slug_from_path(path: str) -> tuple[str, str] | None:
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    hits = []
    for pref, slug, cpath in load_children_tsv():
        if p == pref.rstrip("/") or p.startswith(pref) or f"/{pref}" in f"/{p}/":
            hits.append((pref, slug, cpath))
    if not hits:
        for pref, slug, cpath in load_children_tsv():
            stem = slug[: -len("-company")] if slug.endswith("-company") else slug
            if (
                f"children/{stem}/" in p
                or f"/{stem}-company/" in f"/{p}/"
                or f"projects/{stem}/" in f"/{p}/"
            ):
                hits.append((pref, slug, cpath))
    if not hits:
        return None
    hits.sort(key=lambda x: len(x[0]), reverse=True)
    _, slug, cpath = hits[0]
    return slug, cpath


def map_company(name: str) -> str:
    """Fuzzy map user company name → slug."""
    n = _norm(name)
    c = _compact(name)
    aliases = load_aliases()
    if n in aliases:
        return aliases[n] if aliases[n].endswith("-company") else f"{aliases[n]}-company"
    if c in aliases:
        a = aliases[c]
        return a if a.endswith("-company") else f"{a}-company"

    candidates: list[str] = []
    for _, slug, _ in load_children_tsv():
        candidates.append(slug)
    for row in registry_list():
        if row.get("slug"):
            candidates.append(row["slug"])
    # unique preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for s in candidates:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    exact = []
    fuzzy = []
    for slug in uniq:
        stem = slug[: -len("-company")] if slug.endswith("-company") else slug
        ns, cs = _norm(stem), _compact(stem)
        nslug, cslug = _norm(slug), _compact(slug)
        if n in (ns, nslug) or c in (cs, cslug):
            exact.append(slug)
        elif n in ns or ns in n or c in cs or cs in c or n in nslug or c in cslug:
            fuzzy.append(slug)
    hits = exact or fuzzy
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SystemExit(
            f"error: cannot map company {name!r} — known: "
            + ", ".join(sorted({u[: -len('-company')] if u.endswith('-company') else u for u in uniq}) or ["(none)"])
        )
    raise SystemExit(
        f"error: ambiguous company {name!r} → {hits}. Pass a clearer name or --slug."
    )


def abs_company(slug: str, cpath: str | None = None) -> Path:
    full = slug if slug.endswith("-company") else f"{slug}-company"
    reg = registry_row(full)
    if reg and reg.get("company_path"):
        p = Path(reg["company_path"]).expanduser().resolve()
        if p.is_dir():
            return p
    candidates: list[Path] = []
    if cpath:
        raw = Path(cpath)
        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.append((COMPANY / cpath).resolve())
            candidates.append((REPO / cpath).resolve())
            cleaned = cpath.lstrip("./")
            while cleaned.startswith("../"):
                cleaned = cleaned[3:]
            candidates.append((REPO / cleaned).resolve())
    stem = full[: -len("-company")]
    candidates.append(REPO / "projects" / stem / ".agents" / full)
    candidates.append(COMPANY / "children" / stem / full)
    for p in candidates:
        if p.is_dir():
            return p
    raise SystemExit(f"error: child company dir missing for {full}")


def launch_path(company: Path) -> Path:
    pkg = company.parent.parent if company.parent.name == ".agents" else company.parent
    for cand in (pkg / ".grok" / "launch-ceo.sh", company / ".grok" / "launch-ceo.sh"):
        if cand.is_file():
            return cand
    raise SystemExit(
        f"error: no launch-ceo.sh for {company} — run child install.sh / company_os.sh grok first"
    )


def print_brief(slug: str, company: Path, goal: str, path: str | None) -> None:
    launch = None
    try:
        launch = launch_path(company)
    except SystemExit:
        pass
    print("handoff: child")
    print(f"child_slug: {slug}")
    print(f"child_company: {company}")
    print("spawn: child ceo ONLY")
    print("subagent_type: ceo")
    print(f"cwd: {company}")
    if path:
        print(f"path: {path}")
    print(f"goal: {goal}")
    print(
        "brief: short goal only. Do not open child ORG/staffs from parent. "
        "Child ceo hops its ICs; escalate back for grants/docs/hire."
    )
    print("do_not: deep-spawn child ICs; crawl parent src/")
    if launch:
        print(f"optional_launch: {launch}")
    print("---")
    print("parent_action: spawn_subagent(subagent_type=ceo, cwd=child_company, prompt=goal)")
    print(f"or_shell: launch-child.sh {slug[: -len('-company')] if slug.endswith('-company') else slug} \"{goal}\"")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("company", nargs="?", help="Fuzzy child name (desk-garden, dg, desk garden, …)")
    ap.add_argument("prompt", nargs="*", help="Prompt for child ceo (launch mode)")
    ap.add_argument("--slug", help="Exact slug (desk-garden-company)")
    ap.add_argument("--path", help="Path under child → resolve company")
    ap.add_argument("--goal", default="", help="Goal/prompt (alt to positional prompt)")
    ap.add_argument("--brief", action="store_true", help="Print spawn brief only (no launch)")
    ap.add_argument("--launch", action="store_true", help="Force launch TUI (default if prompt given)")
    ap.add_argument("--list", action="store_true", help="List known children / aliases")
    ap.add_argument("--print-path", action="store_true", help="Print company_path only")
    args = ap.parse_args()

    if args.list:
        print("slug\tcompany_path\taliases")
        alias_by_slug: dict[str, list[str]] = {}
        for a, s in load_aliases().items():
            full = s if s.endswith("-company") else f"{s}-company"
            alias_by_slug.setdefault(full, []).append(a)
        seen: set[str] = set()
        for row in registry_list():
            slug = row.get("slug") or ""
            if not slug or slug in seen:
                continue
            seen.add(slug)
            print(f"{slug}\t{row.get('company_path','')}\t{','.join(sorted(set(alias_by_slug.get(slug, []))))}")
        for _, slug, cpath in load_children_tsv():
            if slug in seen:
                continue
            seen.add(slug)
            print(f"{slug}\t{cpath}\t{','.join(sorted(set(alias_by_slug.get(slug, []))))}")
        return 0

    slug = args.slug
    cpath = None
    if args.path:
        hit = resolve_slug_from_path(args.path)
        if not hit:
            print(f"error: no children.tsv match for path={args.path!r}", file=sys.stderr)
            return 2
        slug, cpath = hit
    elif args.company:
        slug = map_company(args.company)
    if not slug:
        print("error: pass company name, --slug, or --path (see --list)", file=sys.stderr)
        return 2
    if not slug.endswith("-company"):
        slug = f"{slug}-company"

    company = abs_company(slug, cpath)
    if args.print_path:
        print(company)
        return 0

    goal = (args.goal or " ".join(args.prompt)).strip()
    do_launch = args.launch or (bool(goal) and not args.brief)
    if args.brief:
        do_launch = False
    if not goal:
        goal = "Continue product work per COMPANY_BOOT; Result to parent ceo when done or blocked."

    if do_launch:
        launch = launch_path(company)
        print(f"[handoff_child] company={slug}", file=sys.stderr)
        print(f"[handoff_child] path={company}", file=sys.stderr)
        print(f"[handoff_child] launch={launch}", file=sys.stderr)
        os.chdir(launch.parent.parent)  # package root (…/projects/desk-garden)
        os.execv(str(launch), [str(launch), goal])

    print_brief(slug, company, goal, args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
