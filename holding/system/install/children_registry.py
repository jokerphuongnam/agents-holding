#!/usr/bin/env python3
"""Parent-local registry of child companies (sqlite, gitignored).

Analogy: holding/company_registry.py inventories subsidiaries of holding.
This inventories **children of one parent company** — same idea, one level down.

Store (default):
  <parent-company>/cache/children.sqlite
  override: CHILDREN_REGISTRY_DB=…  or  --db

Agents read CLI TSV stdout only — never open *.sqlite.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATUS_ACTIVE = "active"
STATUS_MISSING = "missing"
STATUS_ARCHIVED = "archived"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def abs_path(p: str | Path) -> Path:
    return Path(p).expanduser().resolve()


def make_id(parent_slug: str, child_slug: str, project_root: Path) -> str:
    raw = f"{parent_slug}\0{child_slug}\0{project_root.as_posix()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def ensure_parent(parent: Path) -> Path:
    parent = abs_path(parent)
    if not parent.is_dir() or not (parent / "system").is_dir():
        raise SystemExit(f"error: not a Company OS parent tree: {parent}")
    return parent


def default_db(parent: Path) -> Path:
    env = os.environ.get("CHILDREN_REGISTRY_DB", "").strip()
    if env:
        return Path(env).expanduser()
    return parent / "cache" / "children.sqlite"


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS children (
            id TEXT PRIMARY KEY,
            parent_slug TEXT NOT NULL,
            slug TEXT NOT NULL,
            project_root TEXT NOT NULL,
            company_path TEXT NOT NULL,
            grants_path TEXT NOT NULL DEFAULT '',
            meta_path TEXT NOT NULL DEFAULT '',
            budget TEXT NOT NULL DEFAULT '',
            placement TEXT NOT NULL DEFAULT 'nested',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            UNIQUE (parent_slug, slug, project_root)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_children_slug ON children(slug)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_children_parent ON children(parent_slug)"
    )
    conn.commit()
    return conn


def normalize_slug(name: str) -> str:
    s = (name or "").strip().lower()
    if not s:
        raise SystemExit("error: empty slug")
    if not s.endswith("-company"):
        s = f"{s}-company"
    return s


def stem_of(slug: str) -> str:
    s = slug.strip().lower()
    if s.endswith("-company"):
        return s[: -len("-company")]
    return s


def upsert_child(
    conn: sqlite3.Connection,
    *,
    parent_slug: str,
    slug: str,
    project_root: Path,
    company_path: Path,
    grants_path: str = "",
    meta_path: str = "",
    budget: str = "",
    placement: str = "nested",
    note: str = "",
    quiet: bool = False,
) -> tuple[str, str]:
    slug = normalize_slug(slug)
    parent_slug = normalize_slug(parent_slug) if parent_slug else parent_slug
    now = utc_now()
    cid = make_id(parent_slug, slug, project_root)
    row = conn.execute(
        "SELECT id, status FROM children WHERE parent_slug = ? AND slug = ? AND project_root = ?",
        (parent_slug, slug, project_root.as_posix()),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE children SET
              company_path = ?, grants_path = ?, meta_path = ?,
              budget = ?, placement = ?, status = ?,
              updated_at = ?, last_seen_at = ?, note = ?
            WHERE id = ?
            """,
            (
                company_path.as_posix(),
                grants_path,
                meta_path,
                budget,
                placement,
                STATUS_ACTIVE,
                now,
                now,
                note,
                row["id"],
            ),
        )
        conn.commit()
        if not quiet:
            print(f"updated\t{row['id']}\t{slug}\t{company_path}")
        return "updated", row["id"]

    conn.execute(
        """
        INSERT INTO children(
          id, parent_slug, slug, project_root, company_path,
          grants_path, meta_path, budget, placement, status,
          created_at, updated_at, last_seen_at, note
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            cid,
            parent_slug,
            slug,
            project_root.as_posix(),
            company_path.as_posix(),
            grants_path,
            meta_path,
            budget,
            placement,
            STATUS_ACTIVE,
            now,
            now,
            now,
            note,
        ),
    )
    conn.commit()
    if not quiet:
        print(f"registered\t{cid}\t{slug}\t{company_path}")
    return "registered", cid


def refresh_missing(conn: sqlite3.Connection, row: sqlite3.Row) -> str:
    st = row["status"]
    if st == STATUS_ARCHIVED:
        return st
    path = Path(row["company_path"])
    now = utc_now()
    if path.is_dir() and (path / "system").is_dir():
        if st != STATUS_ACTIVE:
            conn.execute(
                "UPDATE children SET status = ?, updated_at = ?, last_seen_at = ? WHERE id = ?",
                (STATUS_ACTIVE, now, now, row["id"]),
            )
            conn.commit()
        else:
            conn.execute(
                "UPDATE children SET last_seen_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()
        return STATUS_ACTIVE
    if st != STATUS_MISSING:
        conn.execute(
            "UPDATE children SET status = ?, updated_at = ? WHERE id = ?",
            (STATUS_MISSING, now, row["id"]),
        )
        conn.commit()
    return STATUS_MISSING


def cmd_register(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    parent = ensure_parent(Path(args.parent))
    parent_slug = parent.name
    slug = normalize_slug(args.slug)
    project_root = abs_path(args.project_root) if args.project_root else parent.parent.parent
    company_path = abs_path(args.company_path) if args.company_path else (
        parent / "children" / stem_of(slug) / slug
    )
    grants = args.grants_path or str(parent / "children" / stem_of(slug) / "GRANTS.toml")
    meta = args.meta_path or str(parent / "children" / stem_of(slug) / "META.toml")
    upsert_child(
        conn,
        parent_slug=parent_slug,
        slug=slug,
        project_root=project_root,
        company_path=company_path,
        grants_path=grants,
        meta_path=meta,
        budget=args.budget or "",
        placement=args.placement or "nested",
        note=args.note or "",
    )
    return 0


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    parent = ensure_parent(Path(args.parent))
    parent_slug = parent.name
    rows = conn.execute(
        """
        SELECT * FROM children
        WHERE parent_slug = ?
        ORDER BY slug, project_root
        """,
        (parent_slug,),
    ).fetchall()
    print(
        "cols\tid\tslug\tstatus\tbudget\tplacement\tproject_root\tcompany_path\tgrants_path"
    )
    for r in rows:
        st = refresh_missing(conn, r)
        r2 = conn.execute("SELECT * FROM children WHERE id = ?", (r["id"],)).fetchone()
        print(
            f"row\t{r2['id']}\t{r2['slug']}\t{st}\t{r2['budget']}\t{r2['placement']}\t"
            f"{r2['project_root']}\t{r2['company_path']}\t{r2['grants_path']}"
        )
    print(f"count\t{len(rows)}")
    print(f"parent\t{parent_slug}\t{parent}")
    print("rule\tagents read TSV stdout only — never open sqlite")
    return 0


def cmd_show(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    parent = ensure_parent(Path(args.parent))
    parent_slug = parent.name
    slug = normalize_slug(args.slug) if args.slug else ""
    if args.id:
        row = conn.execute(
            "SELECT * FROM children WHERE id = ? OR id LIKE ?",
            (args.id, args.id + "%"),
        ).fetchone()
    elif slug:
        row = conn.execute(
            "SELECT * FROM children WHERE parent_slug = ? AND slug = ? ORDER BY updated_at DESC",
            (parent_slug, slug),
        ).fetchone()
    else:
        print("error: --slug or --id required", file=sys.stderr)
        return 2
    if row is None:
        print("error: not found", file=sys.stderr)
        return 1
    st = refresh_missing(conn, row)
    row = conn.execute("SELECT * FROM children WHERE id = ?", (row["id"],)).fetchone()
    for k in row.keys():
        val = st if k == "status" else row[k]
        print(f"{k}\t{val}")
    return 0


def cmd_scan(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    parent = ensure_parent(Path(args.parent))
    parent_slug = parent.name
    children_root = parent / "children"
    found = 0
    registered = 0
    if not children_root.is_dir():
        print("cols\tslug\tcompany_path\taction")
        print("count\t0")
        return 0
    print("cols\tslug\tcompany_path\taction")
    for stem_dir in sorted(children_root.iterdir()):
        if not stem_dir.is_dir() or stem_dir.name.startswith("."):
            continue
        if stem_dir.name == "README.md":
            continue
        # nested: children/<stem>/<stem>-company
        nested = stem_dir / f"{stem_dir.name}-company"
        company_path = None
        if nested.is_dir() and (nested / "system").is_dir():
            company_path = nested
            slug = nested.name
        else:
            # look for any *-company under stem
            for cand in sorted(stem_dir.glob("*-company")):
                if cand.is_dir() and (cand / "system").is_dir():
                    company_path = cand
                    slug = cand.name
                    break
        if company_path is None:
            continue
        found += 1
        action = "seen"
        if args.register:
            grants = stem_dir / "GRANTS.toml"
            meta = stem_dir / "META.toml"
            # project_root from META if present
            project_root = parent.parent.parent
            if meta.is_file():
                for line in meta.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("project_root"):
                        _, _, val = line.partition("=")
                        val = val.strip().strip('"').strip("'")
                        if val:
                            project_root = abs_path(val)
                        break
            upsert_child(
                conn,
                parent_slug=parent_slug,
                slug=slug,
                project_root=project_root,
                company_path=company_path,
                grants_path=str(grants) if grants.is_file() else "",
                meta_path=str(meta) if meta.is_file() else "",
                placement="nested",
                note="scan",
                quiet=True,
            )
            action = "upsert"
            registered += 1
        print(f"scan\t{slug}\t{company_path}\t{action}")
    print(f"count\t{found}")
    if args.register:
        print(f"registered\t{registered}")
    return 0


def cmd_prune(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    parent = ensure_parent(Path(args.parent))
    parent_slug = parent.name
    rows = conn.execute(
        "SELECT * FROM children WHERE parent_slug = ? AND status != ?",
        (parent_slug, STATUS_ARCHIVED),
    ).fetchall()
    stale = []
    for r in rows:
        st = refresh_missing(conn, r)
        if st == STATUS_MISSING:
            stale.append(r)
    print("cols\tid\tslug\tcompany_path\tstatus")
    for r in stale:
        print(f"stale\t{r['id']}\t{r['slug']}\t{r['company_path']}\tmissing")
    print(f"count\t{len(stale)}")
    if args.forget and stale:
        if not args.i_am_human:
            print("error: --forget needs --i-am-human", file=sys.stderr)
            return 2
        for r in stale:
            conn.execute("DELETE FROM children WHERE id = ?", (r["id"],))
        conn.commit()
        print(f"forgotten\t{len(stale)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="children_registry.py",
        description=(
            "Inventory of child companies under one parent Company OS "
            "(like holding company_registry, one level down)."
        ),
    )
    p.add_argument(
        "--parent",
        required=True,
        help="Path to parent …/<slug>-company/",
    )
    p.add_argument("--db", default="", help="Override sqlite path")
    sub = p.add_subparsers(dest="cmd", required=True)

    reg = sub.add_parser("register", help="Upsert one child")
    reg.add_argument("--slug", required=True)
    reg.add_argument("--project-root", default="")
    reg.add_argument("--company-path", default="")
    reg.add_argument("--grants-path", default="")
    reg.add_argument("--meta-path", default="")
    reg.add_argument("--budget", default="")
    reg.add_argument("--placement", default="nested")
    reg.add_argument("--note", default="")

    ls = sub.add_parser("list", help="List children of parent")
    sh = sub.add_parser("show", help="Show one child")
    sh.add_argument("--slug", default="")
    sh.add_argument("--id", default="")

    sc = sub.add_parser("scan", help="Discover children/ on disk")
    sc.add_argument("--register", action="store_true")

    pr = sub.add_parser("prune", help="List missing SoT rows")
    pr.add_argument("--forget", action="store_true")
    pr.add_argument("--i-am-human", action="store_true")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    parent = ensure_parent(Path(args.parent))
    db = Path(args.db).expanduser() if args.db else default_db(parent)
    conn = connect(db)
    try:
        if args.cmd == "register":
            return cmd_register(conn, args)
        if args.cmd == "list":
            return cmd_list(conn, args)
        if args.cmd == "show":
            return cmd_show(conn, args)
        if args.cmd == "scan":
            return cmd_scan(conn, args)
        if args.cmd == "prune":
            return cmd_prune(conn, args)
        print(f"error: unknown cmd {args.cmd}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
