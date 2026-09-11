#!/usr/bin/env python3
"""Holding company registry (SQLite, local-only / gitignored).

Inventory of subsidiaries: slug + project_root + company SoT path.
Agents read CLI TSV stdout only — never open *.sqlite.

Store:
  <holding>/cache/companies.sqlite
  override: COMPANY_REGISTRY_DB=…
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence


STATUS_ACTIVE = "active"
STATUS_ARCHIVED = "archived"
STATUS_MISSING = "missing"

# Trailing role segment in slug: {org}-{product}-{role}[-company]
# Family key = everything before the role (e.g. chat-backend → chat).
ROLE_SUFFIXES = frozenset(
    {
        "frontend",
        "frontend-web",
        "backend",
        "backend-api",
        "mobile",
        "ios",
        "android",
        "web",
        "api",
        "admin",
        "client",
        "server",
        "desktop",
        "worker",
        "gateway",
    }
)


def slug_stem(slug: str) -> str:
    s = (slug or "").strip().lower()
    if s.endswith("-company"):
        s = s[: -len("-company")]
    return s


def family_and_role(slug: str) -> tuple[str, str]:
    """Return (family, role) from naming convention.

    Examples:
      chat-backend-company     → (chat, backend)
      retail-frontend          → (retail, frontend)
      calldemoapp-company      → ("", "")  # no role suffix
    """
    stem = slug_stem(slug)
    if not stem:
        return "", ""
    parts = stem.split("-")
    if len(parts) < 2:
        return "", ""
    # Prefer longest matching multi-segment role at the end
    for n in (2, 1):
        if len(parts) <= n:
            continue
        role = "-".join(parts[-n:])
        if role in ROLE_SUFFIXES:
            family = "-".join(parts[:-n])
            return family, role
    return "", ""


def family_key(slug: str) -> str:
    """Heuristic only — prefer explicit row['family'] via company_family()."""
    fam, _role = family_and_role(slug)
    return fam


def normalize_family(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")


def company_family(row: sqlite3.Row | dict) -> str:
    """Explicit family column first; slug heuristic only as fallback."""
    explicit = ""
    try:
        explicit = (row["family"] or "").strip()
    except (KeyError, IndexError, TypeError):
        explicit = ""
    if explicit:
        return normalize_family(explicit)
    try:
        slug = row["slug"]
    except (KeyError, IndexError, TypeError):
        slug = ""
    return family_key(slug)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def holding_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_db_path() -> Path:
    env = os.environ.get("COMPANY_REGISTRY_DB", "").strip()
    if env:
        return Path(env).expanduser()
    return holding_root() / "cache" / "companies.sqlite"


def abs_path(p: str | Path) -> Path:
    return Path(p).expanduser().resolve()


def make_id(slug: str, project_root: Path) -> str:
    raw = f"{slug}\0{project_root.as_posix()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            slug TEXT NOT NULL,
            project_root TEXT NOT NULL,
            company_path TEXT NOT NULL,
            budget TEXT NOT NULL DEFAULT '',
            topology TEXT NOT NULL DEFAULT '',
            tech TEXT NOT NULL DEFAULT '',
            packages TEXT NOT NULL DEFAULT '',
            family TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            UNIQUE (slug, project_root)
        )
        """
    )
    cols = {r[1] for r in conn.execute("PRAGMA table_info(companies)").fetchall()}
    if "packages" not in cols:
        conn.execute(
            "ALTER TABLE companies ADD COLUMN packages TEXT NOT NULL DEFAULT ''"
        )
    if "family" not in cols:
        conn.execute(
            "ALTER TABLE companies ADD COLUMN family TEXT NOT NULL DEFAULT ''"
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS company_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'related',
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            UNIQUE (from_id, to_id, kind),
            FOREIGN KEY (from_id) REFERENCES companies(id),
            FOREIGN KEY (to_id) REFERENCES companies(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_links_from ON company_links(from_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_links_to ON company_links(to_id)"
    )
    conn.commit()
    return conn


def find_company_rows(
    conn: sqlite3.Connection,
    *,
    slug: str = "",
    company_id: str = "",
    path: str = "",
    allow_multi: bool = False,
) -> list[sqlite3.Row]:
    if company_id:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ? OR id LIKE ?",
            (company_id, company_id + "%"),
        ).fetchall()
        return list(row)
    if path:
        p = abs_path(path).as_posix()
        return list(
            conn.execute(
                "SELECT * FROM companies WHERE company_path = ? OR project_root = ?",
                (p, p),
            ).fetchall()
        )
    if slug:
        s = slug.strip()
        s_full = s if s.endswith("-company") else f"{s}-company"
        exact = list(
            conn.execute(
                "SELECT * FROM companies WHERE slug = ? ORDER BY updated_at DESC",
                (s_full,),
            ).fetchall()
        )
        if exact:
            return exact if allow_multi else [exact[0]]
        # Fuzzy: substring on slug
        fuzzy = list(
            conn.execute(
                "SELECT * FROM companies WHERE slug LIKE ? ORDER BY updated_at DESC",
                (f"%{s}%",),
            ).fetchall()
        )
        if not fuzzy:
            return []
        return fuzzy if allow_multi else [fuzzy[0]]
    return []


def require_one_company(
    conn: sqlite3.Connection,
    *,
    slug: str = "",
    company_id: str = "",
    path: str = "",
    label: str = "company",
) -> Optional[sqlite3.Row]:
    rows = find_company_rows(
        conn, slug=slug, company_id=company_id, path=path, allow_multi=True
    )
    if not rows:
        print(f"error: {label} not found", file=sys.stderr)
        return None
    if len(rows) > 1:
        # If all share same slug+different roots, require --id
        print(
            f"error: multiple matches for {label} — pass --id",
            file=sys.stderr,
        )
        for r in rows:
            print(
                f"candidate\t{r['id']}\t{r['slug']}\t{r['project_root']}",
                file=sys.stderr,
            )
        return None
    return rows[0]


def refresh_missing(conn: sqlite3.Connection, row: sqlite3.Row) -> str:
    """Return effective status; mark active→missing if SoT gone."""
    status = row["status"]
    path = Path(row["company_path"])
    if status == STATUS_ARCHIVED:
        return status
    if not path.is_dir():
        if status != STATUS_MISSING:
            conn.execute(
                "UPDATE companies SET status = ?, updated_at = ? WHERE id = ?",
                (STATUS_MISSING, utc_now(), row["id"]),
            )
            conn.commit()
        return STATUS_MISSING
    if status == STATUS_MISSING:
        conn.execute(
            "UPDATE companies SET status = ?, updated_at = ?, last_seen_at = ? WHERE id = ?",
            (STATUS_ACTIVE, utc_now(), utc_now(), row["id"]),
        )
        conn.commit()
        return STATUS_ACTIVE
    return status


def duplicate_slugs(conn: sqlite3.Connection, status_filter: Optional[str] = None) -> set[str]:
    q = """
        SELECT slug FROM companies
        WHERE (? IS NULL OR status = ?)
        GROUP BY slug HAVING COUNT(*) > 1
    """
    rows = conn.execute(q, (status_filter, status_filter)).fetchall()
    return {r["slug"] for r in rows}


def upsert_company(
    conn: sqlite3.Connection,
    *,
    slug: str,
    project_root: Path,
    company_path: Path,
    budget: str = "",
    topology: str = "",
    tech: str = "",
    packages: str = "",
    family: str = "",
    note: str = "",
    quiet: bool = False,
) -> tuple[str, str]:
    """Insert/update one row. Returns (action, id) where action is registered|updated."""
    slug = slug.strip()
    if not slug.endswith("-company"):
        slug = f"{slug}-company"
    project_root = abs_path(project_root)
    company_path = abs_path(company_path)
    budget = (budget or "").strip()
    topology = (topology or "").strip()
    tech = (tech or "").strip()
    packages = (packages or "").strip()
    family = normalize_family(family) if (family or "").strip() else ""
    note = (note or "").strip()
    now = utc_now()
    cid = make_id(slug, project_root)

    existing = conn.execute(
        "SELECT id, status FROM companies WHERE slug = ? AND project_root = ?",
        (slug, project_root.as_posix()),
    ).fetchone()

    if "-archived-" in company_path.name:
        status = STATUS_ARCHIVED
    elif company_path.is_dir():
        status = STATUS_ACTIVE
    else:
        status = STATUS_MISSING

    if existing and existing["status"] == STATUS_ARCHIVED and status == STATUS_MISSING:
        status = STATUS_ARCHIVED

    if existing:
        conn.execute(
            """
            UPDATE companies SET
                company_path = ?, budget = COALESCE(NULLIF(?, ''), budget),
                topology = COALESCE(NULLIF(?, ''), topology),
                tech = COALESCE(NULLIF(?, ''), tech),
                packages = COALESCE(NULLIF(?, ''), packages),
                family = COALESCE(NULLIF(?, ''), family),
                status = ?, updated_at = ?, last_seen_at = ?,
                note = COALESCE(NULLIF(?, ''), note)
            WHERE id = ?
            """,
            (
                company_path.as_posix(),
                budget,
                topology,
                tech,
                packages,
                family,
                status,
                now,
                now,
                note,
                existing["id"],
            ),
        )
        conn.commit()
        action, rid = "updated", existing["id"]
    else:
        # New row: if family omitted, store heuristic so list/resolve still group
        if not family:
            family = family_key(slug)
        conn.execute(
            """
            INSERT INTO companies(
                id, slug, project_root, company_path, budget, topology, tech,
                packages, family, status, created_at, updated_at, last_seen_at, note
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                cid,
                slug,
                project_root.as_posix(),
                company_path.as_posix(),
                budget,
                topology,
                tech,
                packages,
                family,
                status,
                now,
                now,
                now,
                note,
            ),
        )
        conn.commit()
        action, rid = "registered", cid

    if not quiet:
        print(f"{action}\t{rid}\t{slug}\t{project_root}\t{company_path}")
    return action, rid


def cmd_register(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    slug = (args.slug or "").strip()
    if not slug:
        print("error: --slug required", file=sys.stderr)
        return 2
    project_root = abs_path(args.project_root)
    if args.company_path:
        company_path = abs_path(args.company_path)
    else:
        s = slug if slug.endswith("-company") else f"{slug}-company"
        company_path = project_root / ".agents" / s

    action, _rid = upsert_company(
        conn,
        slug=slug,
        project_root=project_root,
        company_path=company_path,
        budget=args.budget or "",
        topology=args.topology or "",
        tech=args.tech or "",
        packages=getattr(args, "packages", "") or "",
        family=getattr(args, "family", "") or "",
        note=args.note or "",
    )
    s = slug if slug.endswith("-company") else f"{slug}-company"
    dups = duplicate_slugs(conn)
    if s in dups:
        print(f"warn\tdup_slug\t{s}\thint\tsame_slug_other_root")
        print("suggest\tarchive_one_or_rename_slug\tkeep intentional forks if both active")
        print(f"next\tcheck --slug {s}")
    return 0 if action else 0


SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "DerivedData",
    "Pods",
    ".build",
    "build",
    "dist",
    "venv",
    ".venv",
    "__pycache__",
    "Library",
    "Applications",
    ".Trash",
}


@dataclass
class FoundCompany:
    slug: str
    project_root: Path
    company_path: Path
    budget: str = ""
    topology: str = ""
    tech: str = ""
    packages: str = ""
    family: str = ""
    in_registry: bool = False
    registry_status: str = ""


def looks_like_company_os(company_dir: Path) -> bool:
    if not company_dir.is_dir():
        return False
    name = company_dir.name
    if not name.endswith("-company"):
        return False
    if "-archived-" in name:
        return False
    # Must live under .agents/
    if company_dir.parent.name != ".agents":
        return False
    # Holding conglomerate is not a subsidiary
    if name == "holding-company" or company_dir.name == "holding":
        return False
    if (company_dir / "system" / "staffs").is_dir():
        return True
    if (company_dir / "system" / "harness").is_dir():
        return True
    if (company_dir / "COMPANY.md").is_file():
        return True
    return False


def parse_company_meta(company_dir: Path) -> tuple[str, str, str, str, str]:
    """Best-effort budget / topology / tech / packages / family from md files."""
    budget = topology = tech = packages = family = ""
    for rel in ("COMPANY.md", "cache/WORKSPACE.md"):
        p = company_dir / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not budget:
            m = re.search(
                r"\*\*Budget at create:\*\*\s*`?(low|medium|high)`?",
                text,
                re.I,
            )
            if not m:
                m = re.search(r"\bBudget\b.*?\b(low|medium|high)\b", text, re.I)
            if m:
                budget = m.group(1).lower()
        if not tech:
            m = re.search(r"\*\*Tech seed notes:\*\*\s*`([^`]+)`", text)
            if m:
                tech = m.group(1).strip()
        if not topology:
            m = re.search(r"\|\s*Topology\s*\|\s*`?(teams|companies)`?\s*\|", text, re.I)
            if m:
                topology = m.group(1).lower()
            elif re.search(r"\btopology\b.*\bteams\b", text, re.I):
                topology = "teams"
            elif re.search(r"\btopology\b.*\bcompanies\b", text, re.I):
                topology = "companies"
        if not packages:
            m = re.search(r"\|\s*Packages\s*\|\s*([^|]+)\|", text, re.I)
            if m:
                raw = m.group(1).strip().strip("`")
                if raw and "none" not in raw.lower():
                    packages = raw
            if not packages:
                m = re.search(r"\*\*Packages:\*\*\s*(.+)", text, re.I)
                if m:
                    raw = m.group(1).strip()
                    if raw and "none" not in raw.lower() and "infer" not in raw.lower():
                        packages = raw
        if not family:
            m = re.search(r"\|\s*Family\s*\|\s*`?([^`|]+)`?\s*\|", text, re.I)
            if not m:
                m = re.search(r"\*\*Family:\*\*\s*`?([^`\n]+)`?", text, re.I)
            if m:
                family = normalize_family(m.group(1))
    # Heuristic from slug when empty: frontend-company → frontend
    if not packages:
        stem = company_dir.name
        if stem.endswith("-company"):
            stem = stem[: -len("-company")]
        for tip in (
            "frontend",
            "backend",
            "mobile",
            "ios",
            "android",
            "web",
            "api",
            "admin",
        ):
            if tip in stem.lower():
                packages = tip
                break
    if not family:
        family = family_key(company_dir.name)
    return budget, topology, tech, packages, family


def default_scan_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home / "Documents",
        home / "Desktop",
        home / "Projects",
        home / "Developer",
        home / "dev",
        home / "code",
        home / "src",
        home / "work",
        home / "repos",
        home,  # shallow fallback
    ]
    # Also scan agents-home siblings only via explicit roots; holding templates skipped in walk
    out: list[Path] = []
    seen: set[str] = set()
    for c in candidates:
        if not c.is_dir():
            continue
        key = str(c.resolve())
        if key in seen:
            continue
        # Prefer deeper roots; if home is listed, use smaller max-depth later
        seen.add(key)
        out.append(c.resolve())
    return out


def iter_company_dirs(root: Path, max_depth: int) -> Iterator[Path]:
    root = root.resolve()
    if not root.is_dir():
        return
    # depth = number of path parts below root
    base_len = len(root.parts)
    stack: list[Path] = [root]
    while stack:
        cur = stack.pop()
        try:
            depth = len(cur.parts) - base_len
        except Exception:
            continue
        if depth > max_depth:
            continue
        try:
            entries = list(cur.iterdir())
        except (PermissionError, OSError):
            continue
        # Fast path: …/.agents/*-company
        if cur.name == ".agents":
            for child in entries:
                if looks_like_company_os(child):
                    yield child.resolve()
            continue
        for child in entries:
            if not child.is_dir():
                continue
            name = child.name
            if name in SKIP_DIR_NAMES or name.startswith("."):
                # still enter .agents
                if name != ".agents":
                    continue
            try:
                child_depth = len(child.parts) - base_len
            except Exception:
                continue
            if child_depth <= max_depth:
                stack.append(child)


def discover_companies(
    roots: Sequence[Path],
    max_depth: int,
    conn: Optional[sqlite3.Connection] = None,
) -> list[FoundCompany]:
    found: dict[str, FoundCompany] = {}
    for root in roots:
        # Shallower when scanning entire home
        depth = max_depth
        if root.resolve() == Path.home().resolve():
            depth = min(max_depth, 4)
        for company_path in iter_company_dirs(root, depth):
            # Skip template factory input
            try:
                parts = company_path.parts
                if "templates" in parts and "company" in parts:
                    continue
                if str(company_path).startswith(str(holding_root())):
                    # never treat holding tree as a subsidiary product company
                    continue
            except Exception:
                pass
            slug = company_path.name
            project_root = company_path.parent.parent  # …/project/.agents/slug
            budget, topology, tech, packages, family = parse_company_meta(company_path)
            key = f"{slug}\0{project_root.as_posix()}"
            fc = FoundCompany(
                slug=slug,
                project_root=project_root,
                company_path=company_path,
                budget=budget,
                topology=topology,
                tech=tech,
                packages=packages,
                family=family,
            )
            if conn is not None:
                row = conn.execute(
                    "SELECT id, status FROM companies WHERE slug = ? AND project_root = ?",
                    (slug, project_root.as_posix()),
                ).fetchone()
                if row:
                    fc.in_registry = True
                    fc.registry_status = row["status"]
            found[key] = fc
    return sorted(found.values(), key=lambda x: (x.slug, str(x.project_root)))


def cmd_scan(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    roots = [abs_path(r) for r in (args.root or [])] or default_scan_roots()
    max_depth = int(args.max_depth)
    found = discover_companies(roots, max_depth, conn)

    registered = updated = 0
    if args.register:
        for fc in found:
            if args.dry_run:
                if fc.in_registry:
                    updated += 1
                else:
                    registered += 1
                continue
            action, _ = upsert_company(
                conn,
                slug=fc.slug,
                project_root=fc.project_root,
                company_path=fc.company_path,
                budget=fc.budget,
                topology=fc.topology or "teams",
                tech=fc.tech,
                packages=fc.packages,
                family=fc.family,
                note="scan",
                quiet=True,
            )
            if action == "registered":
                registered += 1
            else:
                updated += 1
        if not args.dry_run:
            found = discover_companies(roots, max_depth, conn)

    dups = {fc.slug for fc in found if sum(1 for g in found if g.slug == fc.slug) > 1}

    if use_tsv(args):
        print(
            "cols\tslug\tproject_root\tcompany_path\tbudget\ttopology\t"
            "in_registry\tregistry_status\tdup\taction"
        )
        for fc in found:
            action = ""
            if args.register:
                action = "dry_run" if args.dry_run else "upsert"
            elif not fc.in_registry:
                action = "new"
            print(
                f"scan\t{fc.slug}\t{fc.project_root}\t{fc.company_path}\t"
                f"{fc.budget}\t{fc.topology}\t"
                f"{1 if fc.in_registry else 0}\t{fc.registry_status}\t"
                f"{1 if fc.slug in dups else 0}\t{action}"
            )
        print(f"count\t{len(found)}")
        if args.register and not args.dry_run:
            print(f"registered\t{registered}")
            print(f"updated\t{updated}")
        print("rule\tstaffs read TSV stdout only — never open sqlite")
    else:
        table_rows = []
        for fc in found:
            state = fc.registry_status or ("new" if not fc.in_registry else "")
            if not fc.in_registry:
                state = "new"
            table_rows.append(
                [
                    fc.slug,
                    state,
                    fc.budget or "—",
                    fc.topology or "—",
                    "yes" if fc.slug in dups else "",
                    str(fc.project_root),
                ]
            )
        print_table(
            ["slug", "registry", "budget", "topology", "dup", "project_root"],
            table_rows,
            path_cols={"project_root"},
        )
        n_new = sum(1 for f in found if not f.in_registry)
        print(f"scanned roots: {', '.join(str(r) for r in roots)}")
        print(
            f"found {len(found)} compan{'y' if len(found) == 1 else 'ies'} "
            f"({n_new} not in registry)"
        )
        if args.register and args.dry_run:
            print("dry-run: pass --register without --dry-run to upsert into companies.sqlite")
        elif args.register:
            print(f"registered: {registered}  updated: {updated}")
        elif n_new:
            print("tip: scan --register   # upsert discoveries into local registry")
        if dups:
            print("hint: duplicate slugs found — run check after register")

    # Gone on disk but still in holding registry
    stale = collect_stale(conn)
    if args.prune:
        class _PruneArgs:
            tsv = getattr(args, "tsv", False)
            table = getattr(args, "table", False)
            forget = False
            dry_run = False
            i_am_human = False
            yes = False

        rc = cmd_prune(conn, _PruneArgs())  # type: ignore[arg-type]
        return 1 if rc else 0
    if stale:
        if use_tsv(args):
            print(f"stale\t{len(stale)}")
            print("next\tprune")
        else:
            print(
                f"stale in registry: {len(stale)} "
                "(SoT deleted on disk) — run: prune   or   prune --forget --i-am-human"
            )
    return 0


def use_tsv(args: argparse.Namespace) -> bool:
    """Human default = pretty table; agents pass --tsv (or non-TTY + COMPANY_REGISTRY_TSV=1)."""
    if getattr(args, "tsv", False):
        return True
    if getattr(args, "table", False):
        return False
    if os.environ.get("COMPANY_REGISTRY_TSV", "").strip() in ("1", "true", "yes"):
        return True
    return not sys.stdout.isatty()


def shorten(text: str, width: int, *, keep_end: bool = False) -> str:
    text = text or ""
    if width <= 0 or len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    if keep_end:
        return "..." + text[-(width - 3) :]
    keep = width - 3
    left = max(1, keep // 3)
    right = keep - left
    return text[:left] + "..." + text[-right:]


def print_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    path_cols: Optional[set[str]] = None,
) -> None:
    cols = list(headers)
    path_cols = path_cols or {"project_root", "company_path", "value"}
    data = [[("" if c is None else str(c)) for c in row] for row in rows]
    widths = [len(h) for h in cols]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    term = shutil.get_terminal_size((120, 24)).columns
    # Leave room for borders/separators; give leftover width to path columns
    fixed = sum(
        widths[i] for i, h in enumerate(cols) if h not in path_cols
    ) + (3 * len(cols)) + 1
    path_idxs = [i for i, h in enumerate(cols) if h in path_cols]
    if path_idxs:
        budget = max(28, term - fixed)
        each = max(28, budget // len(path_idxs))
        for i in path_idxs:
            widths[i] = min(widths[i], each)

    def fmt_row(cells: Sequence[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            parts.append(
                shorten(
                    cell,
                    widths[i],
                    keep_end=(cols[i] in path_cols),
                ).ljust(widths[i])
            )
        return "| " + " | ".join(parts) + " |"

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print(sep)
    print(fmt_row(cols))
    print(sep)
    for row in data:
        print(fmt_row(row))
    print(sep)


def _print_row_tsv(row: sqlite3.Row, status: str, dup: int) -> None:
    hint = "same_slug_other_root" if dup else ""
    print(
        f"row\t{row['id']}\t{row['slug']}\t{row['project_root']}\t"
        f"{row['company_path']}\t{status}\t{row['budget']}\t{row['topology']}\t"
        f"{dup}\t{hint}"
    )


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    status_filter = (args.status or "").strip() or None
    slug_filter = (args.slug or "").strip() or None
    if slug_filter and not slug_filter.endswith("-company"):
        slug_filter = f"{slug_filter}-company"

    rows = conn.execute(
        """
        SELECT * FROM companies
        WHERE (? IS NULL OR status = ?)
          AND (? IS NULL OR slug = ?)
        ORDER BY slug, project_root
        """,
        (status_filter, status_filter, slug_filter, slug_filter),
    ).fetchall()

    # Dup among active (or among filtered set if status set)
    dup_scope = status_filter or STATUS_ACTIVE
    dups = duplicate_slugs(conn, dup_scope if not slug_filter else None)
    # If filtering by slug, still mark dup if multiple rows for that slug overall
    if slug_filter:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM companies WHERE slug = ?", (slug_filter,)
        ).fetchone()["n"]
        if count > 1:
            dups.add(slug_filter)

    rendered: list[tuple[sqlite3.Row, str, int]] = []
    for r in rows:
        st = refresh_missing(conn, r)
        r2 = conn.execute("SELECT * FROM companies WHERE id = ?", (r["id"],)).fetchone()
        dup = 1 if r2["slug"] in dups else 0
        rendered.append((r2, st, dup))

    tsv = use_tsv(args)
    if tsv:
        print(
            "cols\tid\tslug\tproject_root\tcompany_path\tstatus\tbudget\ttopology\tdup\thint"
        )
        for r2, st, dup in rendered:
            _print_row_tsv(r2, st, dup)
        print(f"count\t{len(rendered)}")
        if dups and (not slug_filter or slug_filter in dups):
            print(
                "suggest\tarchive_one_or_rename_slug\tkeep intentional forks if both active"
            )
        print("rule\tstaffs read TSV stdout only — never open sqlite")
    else:
        # Compact human list: drop company_path (derivable) + empty hint col
        table_rows = [
            [
                r2["id"][:8],
                r2["slug"],
                st,
                r2["budget"] or "—",
                r2["topology"] or "—",
                "yes" if dup else "",
                r2["project_root"],
            ]
            for r2, st, dup in rendered
        ]
        print_table(
            ["id", "slug", "status", "budget", "topology", "dup", "project_root"],
            table_rows,
            path_cols={"project_root"},
        )
        print(f"{len(rendered)} compan{'y' if len(rendered) == 1 else 'ies'}")
        n_missing = sum(1 for _r, st, _d in rendered if st == STATUS_MISSING)
        if n_missing:
            print(
                f"missing: {n_missing} — SoT deleted on disk; "
                "run: prune   or   prune --forget --i-am-human"
            )
        if dups and (not slug_filter or slug_filter in dups):
            print(
                "hint: duplicate slug — archive one (`archive --id … --i-am-human`) "
                "or rename slug; keep both if intentional forks"
            )
        print("tip: show --slug <slug> for full paths; list --tsv for agents")
    return 0


def cmd_show(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = None
    if args.id:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (args.id,)
        ).fetchone()
    elif args.path:
        p = abs_path(args.path).as_posix()
        row = conn.execute(
            "SELECT * FROM companies WHERE company_path = ? OR project_root = ?",
            (p, p),
        ).fetchone()
    elif args.slug:
        slug = args.slug.strip()
        if not slug.endswith("-company"):
            slug = f"{slug}-company"
        rows = conn.execute(
            "SELECT * FROM companies WHERE slug = ? ORDER BY updated_at DESC",
            (slug,),
        ).fetchall()
        if len(rows) > 1:
            print(f"warn: multiple matches for {slug} — use --id or --path", file=sys.stderr)
            if use_tsv(args):
                for r in rows:
                    st = refresh_missing(conn, r)
                    print(
                        f"candidate\t{r['id']}\t{r['project_root']}\t"
                        f"{r['company_path']}\t{st}"
                    )
                print(
                    "suggest\tarchive_one_or_rename_slug\tkeep intentional forks if both active"
                )
            else:
                cands = []
                for r in rows:
                    st = refresh_missing(conn, r)
                    cands.append(
                        [r["id"], r["project_root"], r["company_path"], st]
                    )
                print_table(
                    ["id", "project_root", "company_path", "status"], cands
                )
            return 1
        row = rows[0] if rows else None
    else:
        print("error: need --id, --slug, or --path", file=sys.stderr)
        return 2

    if row is None:
        print("error: not found", file=sys.stderr)
        return 1

    st = refresh_missing(conn, row)
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (row["id"],)).fetchone()
    dups = duplicate_slugs(conn)
    dup = 1 if row["slug"] in dups else 0

    if use_tsv(args):
        print(
            "cols\tid\tslug\tproject_root\tcompany_path\tstatus\tbudget\ttopology\tdup\thint"
        )
        _print_row_tsv(row, st, dup)
        print(f"tech\t{row['tech']}")
        print(f"packages\t{row['packages']}")
        print(f"family\t{company_family(row)}")
        print(f"created_at\t{row['created_at']}")
        print(f"updated_at\t{row['updated_at']}")
        print(f"last_seen_at\t{row['last_seen_at']}")
        if row["note"]:
            print(f"note\t{row['note']}")
        for d, o, kind in list_links_for(conn, row["id"]):
            print(
                f"related\t{d}\t{kind}\t{o['id']}\t{o['slug']}\t{o['project_root']}"
            )
        if dup:
            print(
                "suggest\tarchive_one_or_rename_slug\tkeep intentional forks if both active"
            )
    else:
        fields = [
            ("id", row["id"]),
            ("slug", row["slug"]),
            ("project_root", row["project_root"]),
            ("company_path", row["company_path"]),
            ("status", st),
            ("budget", row["budget"] or "—"),
            ("topology", row["topology"] or "—"),
            ("tech", row["tech"] or "—"),
            ("packages", row["packages"] or "—"),
            ("family", company_family(row) or "—"),
            ("dup", "yes" if dup else "no"),
            ("created_at", row["created_at"]),
            ("updated_at", row["updated_at"]),
            ("last_seen_at", row["last_seen_at"]),
        ]
        if row["note"]:
            fields.append(("note", row["note"]))
        print_table(["field", "value"], fields)
        links = list_links_for(conn, row["id"])
        if links:
            print("related:")
            print_table(
                ["dir", "kind", "slug", "project_root"],
                [
                    [
                        "→" if d == "out" else "←",
                        kind,
                        o["slug"],
                        o["project_root"],
                    ]
                    for d, o, kind in links
                ],
                path_cols={"project_root"},
            )
        else:
            print("related: (none) — relate --from … --to … --bidirectional")
        if dup:
            print(
                "hint: duplicate slug — archive one or rename; keep both if intentional"
            )
    return 0


def cmd_check(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    slug_filter = (args.slug or "").strip() or None
    if slug_filter and not slug_filter.endswith("-company"):
        slug_filter = f"{slug_filter}-company"

    rows = conn.execute(
        """
        SELECT * FROM companies
        WHERE (? IS NULL OR slug = ?)
        ORDER BY slug, project_root
        """,
        (slug_filter, slug_filter),
    ).fetchall()

    dups = duplicate_slugs(conn)
    issues = 0
    rendered: list[list[str]] = []
    tsv_lines: list[str] = []
    for r in rows:
        st = refresh_missing(conn, r)
        r = conn.execute("SELECT * FROM companies WHERE id = ?", (r["id"],)).fetchone()
        issue = ""
        hint = ""
        if r["slug"] in dups:
            issue = "dup_slug"
            hint = "same_slug_other_root"
            issues += 1
        if st == STATUS_MISSING:
            issue = (issue + "+missing") if issue else "missing"
            hint = hint or "company_path_gone"
            issues += 1
        tsv_lines.append(
            f"check\t{r['id']}\t{r['slug']}\t{r['project_root']}\t"
            f"{r['company_path']}\t{st}\t{issue or 'ok'}\t{hint}"
        )
        rendered.append(
            [
                r["id"],
                r["slug"],
                r["project_root"],
                r["company_path"],
                st,
                issue or "ok",
                hint,
            ]
        )

    if use_tsv(args):
        print("cols\tid\tslug\tproject_root\tcompany_path\tstatus\tissue\thint")
        for line in tsv_lines:
            print(line)
        print(f"issues\t{issues}")
        if any(r["slug"] in dups for r in rows):
            print(
                "suggest\tarchive_one_or_rename_slug\tkeep intentional forks if both active"
            )
            print(
                "suggest\tarchive --id <id> --i-am-human\trenames SoT only; app code untouched"
            )
        print("rule\tstaffs read TSV stdout only — never open sqlite")
    else:
        print_table(
            ["id", "slug", "project_root", "company_path", "status", "issue", "hint"],
            rendered,
        )
        print(f"issues: {issues}")
        if any(r["slug"] in dups for r in rows):
            print(
                "hint: archive one (`archive --id … --i-am-human`) or rename slug; "
                "SoT rename only — app code untouched"
            )
    return 1 if issues else 0


def _resolve_target(conn: sqlite3.Connection, args: argparse.Namespace) -> Optional[sqlite3.Row]:
    if args.id:
        return conn.execute(
            "SELECT * FROM companies WHERE id = ?", (args.id,)
        ).fetchone()
    if args.company_path:
        p = abs_path(args.company_path).as_posix()
        return conn.execute(
            "SELECT * FROM companies WHERE company_path = ?", (p,)
        ).fetchone()
    if args.slug and args.project_root:
        slug = args.slug.strip()
        if not slug.endswith("-company"):
            slug = f"{slug}-company"
        root = abs_path(args.project_root).as_posix()
        return conn.execute(
            "SELECT * FROM companies WHERE slug = ? AND project_root = ?",
            (slug, root),
        ).fetchone()
    return None


def cmd_archive(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    if not args.i_am_human and not args.yes:
        print(
            "error: archive needs --i-am-human (or --yes) — renames company SoT on disk",
            file=sys.stderr,
        )
        return 2

    row = _resolve_target(conn, args)
    if row is None:
        print(
            "error: not found — pass --id, --company-path, or --slug + --project-root",
            file=sys.stderr,
        )
        return 1

    if row["status"] == STATUS_ARCHIVED:
        print(f"already\tarchived\t{row['id']}\t{row['company_path']}")
        return 0

    src = Path(row["company_path"])
    if not src.is_dir():
        conn.execute(
            "UPDATE companies SET status = ?, updated_at = ? WHERE id = ?",
            (STATUS_MISSING, utc_now(), row["id"]),
        )
        conn.commit()
        print(f"error: company_path missing\t{src}", file=sys.stderr)
        print(f"updated\t{row['id']}\tstatus\t{STATUS_MISSING}")
        return 1

    stamp = utc_stamp()
    dest = src.parent / f"{src.name}-archived-{stamp}"
    if dest.exists():
        print(f"error: archive target exists\t{dest}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"dry_run\tarchive\t{src}\t→\t{dest}")
        print(f"suggest\trm -rf {row['project_root']}\tonly if you also want the app tree gone")
        return 0

    shutil.move(str(src), str(dest))
    now = utc_now()
    conn.execute(
        """
        UPDATE companies SET company_path = ?, status = ?, updated_at = ?, note = ?
        WHERE id = ?
        """,
        (
            dest.as_posix(),
            STATUS_ARCHIVED,
            now,
            (row["note"] + " | " if row["note"] else "") + f"archived:{stamp}",
            row["id"],
        ),
    )
    conn.commit()
    print(f"archived\t{row['id']}\t{src}\t→\t{dest}")
    print(f"suggest\trm -rf {row['project_root']}\tonly if you also want the app tree gone")
    print("rule\tSoT renamed only — project source not deleted")
    return 0


def cmd_forget(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    if not args.i_am_human and not args.yes:
        print("error: forget needs --i-am-human (or --yes)", file=sys.stderr)
        return 2
    row = _resolve_target(conn, args)
    if row is None:
        print("error: not found", file=sys.stderr)
        return 1
    conn.execute("DELETE FROM company_links WHERE from_id = ? OR to_id = ?", (row["id"], row["id"]))
    conn.execute("DELETE FROM companies WHERE id = ?", (row["id"],))
    conn.commit()
    print(f"forgot\t{row['id']}\t{row['slug']}\t{row['project_root']}")
    print("rule\tregistry row removed — SoT on disk untouched")
    return 0


def list_links_for(conn: sqlite3.Connection, company_id: str) -> list[tuple[str, sqlite3.Row, str]]:
    """Return list of (direction, other_row, kind). direction is out|in."""
    out: list[tuple[str, sqlite3.Row, str]] = []
    for r in conn.execute(
        """
        SELECT l.kind AS kind, c.*
        FROM company_links l
        JOIN companies c ON c.id = l.to_id
        WHERE l.from_id = ?
        ORDER BY c.slug
        """,
        (company_id,),
    ).fetchall():
        out.append(("out", r, r["kind"]))
    for r in conn.execute(
        """
        SELECT l.kind AS kind, c.*
        FROM company_links l
        JOIN companies c ON c.id = l.from_id
        WHERE l.to_id = ?
        ORDER BY c.slug
        """,
        (company_id,),
    ).fetchall():
        out.append(("in", r, r["kind"]))
    return out


def cmd_relate(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """Link company A ↔ company B (directed; --bidirectional adds reverse)."""
    src = require_one_company(
        conn,
        slug=args.from_slug or "",
        company_id=args.from_id or "",
        path=args.from_path or "",
        label="from",
    )
    if src is None:
        return 1
    dst = require_one_company(
        conn,
        slug=args.to_slug or "",
        company_id=args.to_id or "",
        path=args.to_path or "",
        label="to",
    )
    if dst is None:
        return 1
    if src["id"] == dst["id"]:
        print("error: cannot relate a company to itself", file=sys.stderr)
        return 2
    kind = (args.kind or "related").strip().lower() or "related"
    note = (args.note or "").strip()
    now = utc_now()

    def upsert_link(a: str, b: str) -> None:
        conn.execute(
            """
            INSERT INTO company_links(from_id, to_id, kind, note, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(from_id, to_id, kind) DO UPDATE SET
                note = COALESCE(NULLIF(excluded.note, ''), company_links.note),
                updated_at = excluded.updated_at
            """,
            (a, b, kind, note, now),
        )

    upsert_link(src["id"], dst["id"])
    if args.bidirectional:
        upsert_link(dst["id"], src["id"])
    conn.commit()
    if getattr(args, "tsv", False) or (
        not getattr(args, "table", False) and not sys.stdout.isatty()
    ):
        print(f"related\t{src['slug']}\t→\t{dst['slug']}\tkind\t{kind}")
        if args.bidirectional:
            print(f"related\t{dst['slug']}\t→\t{src['slug']}\tkind\t{kind}")
    else:
        arrow = "↔" if args.bidirectional else "→"
        print(f"related: {src['slug']} {arrow} {dst['slug']}  (kind={kind})")
        print("tip: related --slug <slug>   # list neighbors")
        print("tip: resolve --from <slug> --need api   # prefer linked peers")
    return 0


def cmd_unrelate(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    src = require_one_company(
        conn,
        slug=args.from_slug or "",
        company_id=args.from_id or "",
        path="",
        label="from",
    )
    if src is None:
        return 1
    dst = require_one_company(
        conn,
        slug=args.to_slug or "",
        company_id=args.to_id or "",
        path="",
        label="to",
    )
    if dst is None:
        return 1
    kind = (args.kind or "").strip().lower()
    if kind:
        conn.execute(
            "DELETE FROM company_links WHERE from_id = ? AND to_id = ? AND kind = ?",
            (src["id"], dst["id"], kind),
        )
        if args.bidirectional:
            conn.execute(
                "DELETE FROM company_links WHERE from_id = ? AND to_id = ? AND kind = ?",
                (dst["id"], src["id"], kind),
            )
    else:
        conn.execute(
            "DELETE FROM company_links WHERE from_id = ? AND to_id = ?",
            (src["id"], dst["id"]),
        )
        if args.bidirectional:
            conn.execute(
                "DELETE FROM company_links WHERE from_id = ? AND to_id = ?",
                (dst["id"], src["id"]),
            )
    conn.commit()
    print(f"unrelated\t{src['slug']}\t{dst['slug']}")
    return 0


def family_peers(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    exclude_id: str = "",
) -> list[sqlite3.Row]:
    """Other registry rows sharing the same family (explicit column, else heuristic)."""
    fam = company_family(row)
    if not fam:
        return []
    out: list[sqlite3.Row] = []
    for r in conn.execute(
        "SELECT * FROM companies WHERE status != ? ORDER BY slug",
        (STATUS_ARCHIVED,),
    ).fetchall():
        if exclude_id and r["id"] == exclude_id:
            continue
        if company_family(r) == fam:
            out.append(r)
    return out


def cmd_related(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = require_one_company(
        conn,
        slug=args.slug or "",
        company_id=args.id or "",
        path=args.path or "",
        label="company",
    )
    if row is None:
        return 1
    links = list_links_for(conn, row["id"])
    _heur_fam, role = family_and_role(row["slug"])
    fam = company_family(row)
    peers = family_peers(conn, row, exclude_id=row["id"])
    # Dedupe: family peers not already in explicit links
    linked_ids = {o["id"] for _d, o, _k in links}
    family_only = [p for p in peers if p["id"] not in linked_ids]

    if use_tsv(args):
        print(f"family\t{fam or '—'}")
        print(f"role\t{role or '—'}")
        print(
            "cols\tsource\tdir\tkind\tid\tslug\tproject_root\tcompany_path\t"
            "status\tpackages\ttech"
        )
        for direction, other, kind in links:
            print(
                f"related\tlink\t{direction}\t{kind}\t{other['id']}\t{other['slug']}\t"
                f"{other['project_root']}\t{other['company_path']}\t{other['status']}\t"
                f"{other['packages']}\t{other['tech']}"
            )
        for p in family_only:
            print(
                f"related\tfamily\t~\tfamily\t{p['id']}\t{p['slug']}\t"
                f"{p['project_root']}\t{p['company_path']}\t{p['status']}\t"
                f"{p['packages']}\t{p['tech']}"
            )
        print(f"count\t{len(links) + len(family_only)}")
        print(f"from\t{row['slug']}")
        print("channel\tceo")
    else:
        print(f"company: {row['slug']}  ({row['project_root']})")
        print(f"family: {fam or '—'}   role: {role or '—'}")
        print(
            "family is explicit (--family / set-family); "
            "slug shape is optional. e.g. chat-backend and web-chat-api "
            "both use --family chat."
        )
        rows_out: list[list[str]] = []
        for d, o, kind in links:
            rows_out.append(
                [
                    "link",
                    "→" if d == "out" else "←",
                    kind,
                    o["slug"],
                    o["status"],
                    o["packages"] or "—",
                    o["project_root"],
                ]
            )
        for p in family_only:
            _f, prole = family_and_role(p["slug"])
            rows_out.append(
                [
                    "family",
                    "~",
                    prole or "family",
                    p["slug"],
                    p["status"],
                    p["packages"] or "—",
                    p["project_root"],
                ]
            )
        if not rows_out:
            print(
                "(no link edges and no family peers — "
                "set-family … or relate …)"
            )
            return 0
        print_table(
            ["source", "dir", "kind", "slug", "status", "packages", "project_root"],
            rows_out,
            path_cols={"project_root"},
        )
        print(
            f"{len(rows_out)} neighbor(s)  |  handoff channel: subsidiary ceo"
        )
    return 0


def _score_company(
    row: sqlite3.Row,
    needles: Sequence[str],
    linked_ids: set[str],
    *,
    from_family: str = "",
) -> int:
    blob = " ".join(
        [
            row["slug"],
            row["project_root"],
            row["company_path"],
            row["tech"] or "",
            row["packages"] or "",
            row["note"] or "",
        ]
    ).lower()
    score = 0
    for n in needles:
        n = n.lower().strip()
        if not n:
            continue
        if n in (row["slug"] or "").lower():
            score += 50
        if n in (row["packages"] or "").lower():
            score += 40
        if n in (row["tech"] or "").lower():
            score += 30
        if n in (row["project_root"] or "").lower():
            score += 20
        if n in blob:
            score += 10
        # Role needle: --need backend matches …-backend slug role
        _fam, role = family_and_role(row["slug"])
        if role and (n == role or n in role):
            score += 45
    if row["id"] in linked_ids:
        score += 100  # strongest: explicit relate edge
    if from_family and company_family(row) == from_family:
        score += 80  # same explicit (or heuristic) family
    if row["status"] == STATUS_MISSING:
        score -= 80
    if row["status"] == STATUS_ARCHIVED:
        score -= 100
    return score


def cmd_resolve(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """Token-cheap hop brief: find target company for cross-company handoff."""
    needles: list[str] = []
    if args.need:
        needles.append(args.need)
    if args.slug:
        needles.append(args.slug)
    if args.tech:
        needles.extend(x.strip() for x in args.tech.split(",") if x.strip())
    if args.package:
        needles.append(args.package)
    if args.path:
        needles.append(args.path)
    if not needles and not args.from_slug and not args.from_id:
        print(
            "error: pass --need/--slug/--tech/--package/--path and/or --from",
            file=sys.stderr,
        )
        return 2

    linked_ids: set[str] = set()
    from_row = None
    from_family = ""
    if args.from_slug or args.from_id or args.from_path:
        from_row = require_one_company(
            conn,
            slug=args.from_slug or "",
            company_id=args.from_id or "",
            path=args.from_path or "",
            label="from",
        )
        if from_row is None:
            return 1
        from_family = company_family(from_row)
        for _d, other, _k in list_links_for(conn, from_row["id"]):
            linked_ids.add(other["id"])
        # Same-family peers count as soft-links for "no needles" mode
        for peer in family_peers(conn, from_row, exclude_id=from_row["id"]):
            linked_ids.add(peer["id"])

    rows = list(
        conn.execute(
            "SELECT * FROM companies WHERE status != ? ORDER BY slug",
            (STATUS_ARCHIVED,),
        ).fetchall()
    )
    # If --from and no needles, list link + same-family peers
    if from_row and not needles:
        peers = [r for r in rows if r["id"] in linked_ids]
        scored = []
        for r in peers:
            sc = 100 if r["id"] in {
                o["id"] for _d, o, _k in list_links_for(conn, from_row["id"])
            } else 80
            scored.append((sc, r))
        scored.sort(key=lambda x: (-x[0], x[1]["slug"]))
    else:
        scored = []
        for r in rows:
            if from_row and r["id"] == from_row["id"]:
                continue
            sc = _score_company(
                r, needles, linked_ids, from_family=from_family
            )
            if sc > 0:
                scored.append((sc, r))
        scored.sort(key=lambda x: (-x[0], x[1]["slug"]))

    if not scored:
        if use_tsv(args):
            print("matches\t0")
            print("error\tno_match")
        else:
            print("no matches — try list / relate / scan --register")
        return 1

    top_n = max(1, int(args.limit))
    top = scored[:top_n]
    best_score, best = top[0]

    # Ambiguous if second is close
    ambiguous = len(top) > 1 and (top[1][0] >= best_score - 15)

    tsv = use_tsv(args)
    if tsv:
        if from_row:
            print(f"from\t{from_row['slug']}\t{from_row['id']}\t{from_row['project_root']}")
            print(f"family\t{from_family or '—'}")
        print(
            "cols\trank\tscore\tid\tslug\tfamily\tproject_root\tcompany_path\tstatus\t"
            "packages\ttech\tlinked\tchannel"
        )
        for i, (sc, r) in enumerate(top, 1):
            print(
                f"match\t{i}\t{sc}\t{r['id']}\t{r['slug']}\t{company_family(r) or '—'}\t"
                f"{r['project_root']}\t{r['company_path']}\t{r['status']}\t"
                f"{r['packages']}\t{r['tech']}\t"
                f"{1 if r['id'] in linked_ids else 0}\tceo"
            )
        print(f"pick\t{best['slug']}")
        print(f"channel\tceo")
        print(f"project_root\t{best['project_root']}")
        print(f"company_path\t{best['company_path']}")
        print(f"handoff\tAssign subsidiary ceo only — short English brief")
        if ambiguous:
            print("warn\tambiguous\tconfirm with user or pass stronger --need/--slug")
        print("rule\tdo not open every subsidiary ORG; use this brief")
    else:
        if from_row:
            print(f"from: {from_row['slug']}   family: {from_family or '—'}")
        print_table(
            ["#", "score", "slug", "family", "linked", "packages", "status", "project_root"],
            [
                [
                    str(i),
                    str(sc),
                    r["slug"],
                    company_family(r) or "—",
                    "yes" if r["id"] in linked_ids else "",
                    r["packages"] or "—",
                    r["status"],
                    r["project_root"],
                ]
                for i, (sc, r) in enumerate(top, 1)
            ],
            path_cols={"project_root"},
        )
        print(f"pick: {best['slug']}")
        print(f"channel: ceo")
        print(f"project_root: {best['project_root']}")
        print(f"company_path: {best['company_path']}")
        print("handoff: Assign subsidiary ceo only — short English brief (goal/paths/done-when)")
        if ambiguous:
            print("warn: ambiguous — confirm with user or narrow --need/--slug")
        print("rule: do not open every subsidiary ORG; use this brief")
    return 0


def cmd_set_family(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """Set/clear explicit family on one or more companies (slug order independent)."""
    if args.clear:
        fam = ""
    else:
        raw = (args.family or "").strip()
        if not raw:
            print("error: pass --family <id> or --clear", file=sys.stderr)
            return 2
        fam = normalize_family(raw)
        if not fam:
            print("error: empty family after normalize", file=sys.stderr)
            return 2
    targets: list[sqlite3.Row] = []
    if args.id:
        row = require_one_company(conn, company_id=args.id, label="company")
        if row is None:
            return 1
        targets = [row]
    elif args.slug:
        targets = find_company_rows(
            conn, slug=args.slug, allow_multi=bool(args.all)
        )
        if not targets:
            print("error: company not found", file=sys.stderr)
            return 1
        if len(targets) > 1 and not args.all:
            print(
                "error: multiple matches — pass --id or --all",
                file=sys.stderr,
            )
            for r in targets:
                print(
                    f"candidate\t{r['id']}\t{r['slug']}\t{r['project_root']}",
                    file=sys.stderr,
                )
            return 1
    else:
        print("error: need --slug or --id", file=sys.stderr)
        return 2

    now = utc_now()
    for r in targets:
        conn.execute(
            "UPDATE companies SET family = ?, updated_at = ? WHERE id = ?",
            (fam, now, r["id"]),
        )
    conn.commit()
    for r in targets:
        print(f"family\t{r['id']}\t{r['slug']}\t{fam or '—'}")
    if not use_tsv(args):
        print("tip: related --slug …  /  resolve --from … --need api")
    return 0


def collect_stale(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Mark gone SoT paths as missing; return missing (+ already-missing) rows.

    Archived rows are left alone even if the archived folder was deleted —
    use forget explicitly for those.
    """
    rows = conn.execute(
        "SELECT * FROM companies WHERE status != ? ORDER BY slug, project_root",
        (STATUS_ARCHIVED,),
    ).fetchall()
    stale: list[sqlite3.Row] = []
    for r in rows:
        st = refresh_missing(conn, r)
        r2 = conn.execute("SELECT * FROM companies WHERE id = ?", (r["id"],)).fetchone()
        if st == STATUS_MISSING:
            stale.append(r2)
    return stale


def cmd_prune(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """Detect registry rows whose company SoT was deleted on disk; optionally forget."""
    stale = collect_stale(conn)

    if use_tsv(args):
        print(
            "cols\tid\tslug\tproject_root\tcompany_path\tstatus\taction"
        )
        for r in stale:
            action = "missing"
            if args.forget and not args.dry_run:
                action = "forget"
            elif args.forget and args.dry_run:
                action = "dry_run_forget"
            print(
                f"prune\t{r['id']}\t{r['slug']}\t{r['project_root']}\t"
                f"{r['company_path']}\t{r['status']}\t{action}"
            )
        print(f"stale\t{len(stale)}")
        print("rule\tstaffs read TSV stdout only — never open sqlite")
    else:
        if not stale:
            print_table(
                ["id", "slug", "status", "project_root"],
                [],
                path_cols={"project_root"},
            )
            print("stale: 0 — registry matches disk (no missing SoT paths)")
        else:
            print_table(
                ["id", "slug", "status", "project_root", "company_path"],
                [
                    [
                        r["id"][:8],
                        r["slug"],
                        r["status"],
                        r["project_root"],
                        r["company_path"],
                    ]
                    for r in stale
                ],
                path_cols={"project_root", "company_path"},
            )
            print(
                f"stale: {len(stale)} — SoT deleted on disk but still in holding registry"
            )

    if not stale:
        return 0

    if args.forget:
        if not args.i_am_human and not args.yes:
            print(
                "error: prune --forget needs --i-am-human (or --yes)",
                file=sys.stderr,
            )
            return 2
        if args.dry_run:
            if not use_tsv(args):
                print(
                    f"dry-run: would forget {len(stale)} registry row(s) "
                    "(SoT already gone — only DB cleanup)"
                )
            return 0
        for r in stale:
            conn.execute("DELETE FROM companies WHERE id = ?", (r["id"],))
        conn.commit()
        if use_tsv(args):
            print(f"forgot\t{len(stale)}")
        else:
            print(f"forgot {len(stale)} registry row(s) — disk unchanged")
        return 0

    if not use_tsv(args):
        print(
            "tip: prune --forget --i-am-human   # drop missing rows from registry only"
        )
        print("tip: check   # also reports dup_slug + missing")
    return 1


def build_parser() -> argparse.ArgumentParser:
    epilog = """
examples:
  %(prog)s list
  %(prog)s show --slug calldemoapp-company
  %(prog)s scan --register
  %(prog)s prune --forget --i-am-human
  %(prog)s relate --from frontend-company --to backend-company --kind api --bidirectional
  %(prog)s related --slug frontend-company
  %(prog)s resolve --from frontend-company --need api
  %(prog)s resolve --tech nestjs --package backend
  %(prog)s register --slug my-app --project-root /path/to/project \\
      --packages frontend --tech react

cross-company (token-cheap):
  frontend ceo → holding-ceo
    → resolve --from chat-frontend --need api
    → prefers same family chat-* (not retail-*)
    → Assign backend ceo only (short English brief)
  do NOT open every subsidiary ORG; do NOT Assign foreign ICs directly

naming:
  set --family explicitly (slug order can vary):
    chat-backend, web-chat-api     →  --family chat
    retail-frontend, api-retail    →  --family retail
  heuristic slug parse is fallback only

notes:
  • Store is local/gitignored: <holding>/cache/companies.sqlite
  • TTY → pretty table; agents/pipes → pass --tsv (or COMPANY_REGISTRY_TSV=1)
  • Score: relate links > same family > packages/tech/path
  • See cache/COMPANIES.md
""".rstrip()

    p = argparse.ArgumentParser(
        prog="company_registry.py",
        description=(
            "Holding conglomerate inventory of subsidiaries "
            "(slug + project_root + company SoT path). "
            "Local sqlite — never commit."
        ),
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--db",
        default="",
        help="Override DB path (default: <holding>/cache/companies.sqlite)",
    )
    sub = p.add_subparsers(dest="cmd", required=False, metavar="command")

    reg = sub.add_parser(
        "register",
        help="Upsert one company (slug + project_root)",
        description="Insert or update one subsidiary in the local registry.",
    )
    reg.add_argument("--slug", required=True, help="Company slug (…-company added if missing)")
    reg.add_argument("--project-root", required=True, help="Absolute project root")
    reg.add_argument(
        "--company-path",
        default="",
        help="SoT path (default: <project-root>/.agents/<slug>-company)",
    )
    reg.add_argument("--budget", default="", help="low|medium|high")
    reg.add_argument("--topology", default="", help="teams|companies")
    reg.add_argument("--tech", default="", help="Comma-separated tech tags")
    reg.add_argument(
        "--packages",
        default="",
        help="Package labels e.g. frontend,backend:nestjs (helps resolve)",
    )
    reg.add_argument(
        "--family",
        default="",
        help="Explicit product family id (slug-order independent), e.g. chat",
    )
    reg.add_argument("--note", default="")

    sc = sub.add_parser(
        "scan",
        help="Discover .agents/*-company trees on disk",
        description=(
            "Walk roots for Company OS folders under .agents/*-company. "
            "Use --register to upsert into the local DB. "
            "Also tips when registry has stale (deleted) rows."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: %(prog)s --root ~/Documents --register",
    )
    sc.add_argument(
        "--root",
        action="append",
        default=[],
        help="Scan root (repeatable). Default: Documents/Desktop/Projects/… + home",
    )
    sc.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="Max directory depth under each root (home capped at 4)",
    )
    sc.add_argument(
        "--register",
        action="store_true",
        help="Upsert all discoveries into local companies.sqlite",
    )
    sc.add_argument(
        "--dry-run",
        action="store_true",
        help="With --register: show what would be written, do not write",
    )
    sc.add_argument(
        "--prune",
        action="store_true",
        help="After scan, also mark/list registry rows whose SoT path is gone",
    )

    def add_format_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--tsv",
            action="store_true",
            help="Machine/agent TSV output (default when stdout is not a TTY)",
        )
        sp.add_argument(
            "--table",
            action="store_true",
            help="Force pretty ASCII table (default on TTY)",
        )

    add_format_flags(sc)

    ls = sub.add_parser(
        "list",
        help="Inventory (pretty table on TTY; --tsv for agents)",
        description="List registered companies. Marks missing when SoT path is gone.",
    )
    ls.add_argument("--status", default="", help="Filter: active|missing|archived")
    ls.add_argument("--slug", default="", help="Filter by slug")
    add_format_flags(ls)

    sh = sub.add_parser(
        "show",
        help="Show one company (full paths)",
        description="Show one registry row by --id, --slug, or --path.",
    )
    sh.add_argument("--id", default="")
    sh.add_argument("--slug", default="")
    sh.add_argument("--path", default="", help="project_root or company_path")
    add_format_flags(sh)

    ch = sub.add_parser(
        "check",
        help="Duplicates + missing paths",
        description="Report dup_slug and missing SoT paths (exit 1 if issues).",
    )
    ch.add_argument("--slug", default="")
    add_format_flags(ch)
    doc = sub.add_parser("doctor", help="Alias of check")
    doc.add_argument("--slug", default="")
    add_format_flags(doc)

    pr = sub.add_parser(
        "prune",
        help="List SoT-deleted rows still in registry; optional --forget",
        description=(
            "Refresh status for every non-archived row. Paths that no longer "
            "exist become status=missing. With --forget, drop those DB rows only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: %(prog)s --forget --i-am-human",
    )
    pr.add_argument(
        "--forget",
        action="store_true",
        help="Drop missing rows from registry (disk already gone)",
    )
    pr.add_argument("--dry-run", action="store_true", help="With --forget: preview only")
    pr.add_argument(
        "--i-am-human",
        action="store_true",
        help="Required for --forget (destructive to registry rows)",
    )
    pr.add_argument("--yes", action="store_true", help="Alias of --i-am-human")
    add_format_flags(pr)

    ar = sub.add_parser(
        "archive",
        help="Rename SoT to *-archived-TIMESTAMP",
        description=(
            "Rename .agents/<slug>-company → *-archived-<UTC>. "
            "Does not delete app source. Requires --i-am-human."
        ),
    )
    ar.add_argument("--id", default="")
    ar.add_argument("--company-path", default="")
    ar.add_argument("--slug", default="", help="With --project-root to select row")
    ar.add_argument("--project-root", default="")
    ar.add_argument("--i-am-human", action="store_true")
    ar.add_argument("--yes", action="store_true")
    ar.add_argument("--dry-run", action="store_true")

    fg = sub.add_parser(
        "forget",
        help="Drop one registry row only (SoT untouched)",
        description="Remove a single registry row. Disk SoT is not modified.",
    )
    fg.add_argument("--id", default="")
    fg.add_argument("--company-path", default="")
    fg.add_argument("--slug", default="")
    fg.add_argument("--project-root", default="")
    fg.add_argument("--i-am-human", action="store_true")
    fg.add_argument("--yes", action="store_true")

    rel = sub.add_parser(
        "relate",
        help="Link company A → B (optional --bidirectional)",
        description=(
            "Record that two subsidiaries are related (api, sibling, depends, …). "
            "holding-ceo resolve prefers linked peers for handoffs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "example: %(prog)s --from fe-company --to be-company "
            "--kind api --bidirectional"
        ),
    )
    rel.add_argument("--from", dest="from_slug", default="", help="Source slug")
    rel.add_argument("--from-id", default="")
    rel.add_argument("--from-path", default="")
    rel.add_argument("--to", dest="to_slug", default="", help="Target slug")
    rel.add_argument("--to-id", default="")
    rel.add_argument("--to-path", default="")
    rel.add_argument(
        "--kind",
        default="related",
        help="Link kind: api|sibling|depends|related (default related)",
    )
    rel.add_argument("--note", default="")
    rel.add_argument(
        "--bidirectional",
        action="store_true",
        help="Also create reverse edge",
    )
    add_format_flags(rel)

    un = sub.add_parser("unrelate", help="Remove a link between two companies")
    un.add_argument("--from", dest="from_slug", default="")
    un.add_argument("--from-id", default="")
    un.add_argument("--to", dest="to_slug", default="")
    un.add_argument("--to-id", default="")
    un.add_argument("--kind", default="", help="If set, only remove this kind")
    un.add_argument("--bidirectional", action="store_true")

    nb = sub.add_parser(
        "related",
        help="List companies linked to a slug",
        description="Show outbound/inbound neighbors for handoff routing.",
    )
    nb.add_argument("--slug", default="")
    nb.add_argument("--id", default="")
    nb.add_argument("--path", default="")
    add_format_flags(nb)

    sf = sub.add_parser(
        "set-family",
        help="Set explicit family id (slug arrangement independent)",
        description=(
            "Group companies that belong together even when slug order differs "
            "(chat-* vs retail-*). resolve/related use this before "
            "slug heuristics."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: %(prog)s --slug web-retail-frontend --family retail",
    )
    sf.add_argument("--slug", default="")
    sf.add_argument("--id", default="")
    sf.add_argument("--family", default="", help="Family id, e.g. chat")
    sf.add_argument("--clear", action="store_true", help="Clear explicit family")
    sf.add_argument(
        "--all",
        action="store_true",
        help="When --slug matches many roots, update all",
    )
    add_format_flags(sf)

    rs = sub.add_parser(
        "resolve",
        help="Pick target company for cross-company handoff (token-cheap)",
        description=(
            "Score registry rows by links + explicit family + packages/tech. "
            "Emit a short brief: pick slug, project_root, channel=ceo. "
            "Prefer --from so linked/same-family peers rank first."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: %(prog)s --from frontend-company --need api",
    )
    rs.add_argument("--from", dest="from_slug", default="", help="Requesting company slug")
    rs.add_argument("--from-id", default="")
    rs.add_argument("--from-path", default="")
    rs.add_argument("--need", default="", help="Keyword e.g. api, auth, payment")
    rs.add_argument("--slug", default="", help="Target slug hint")
    rs.add_argument("--tech", default="", help="Comma tech tags")
    rs.add_argument("--package", default="", help="Package label e.g. backend")
    rs.add_argument("--path", default="", help="Path keyword")
    rs.add_argument("--limit", type=int, default=5, help="Max candidates to show")
    add_format_flags(rs)

    sub.add_parser("path", help="Print DB path")
    sub.add_parser(
        "help",
        help="Show this help (same as -h)",
        description="Print top-level help.",
    )
    return p


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.cmd or args.cmd == "help":
        parser.print_help()
        return 0
    db = Path(args.db).expanduser() if args.db else default_db_path()
    if args.cmd == "path":
        print(db)
        return 0
    conn = connect(db)
    try:
        if args.cmd == "register":
            return cmd_register(conn, args)
        if args.cmd == "scan":
            return cmd_scan(conn, args)
        if args.cmd == "list":
            return cmd_list(conn, args)
        if args.cmd == "show":
            return cmd_show(conn, args)
        if args.cmd in ("check", "doctor"):
            return cmd_check(conn, args)
        if args.cmd == "prune":
            return cmd_prune(conn, args)
        if args.cmd == "relate":
            return cmd_relate(conn, args)
        if args.cmd == "unrelate":
            return cmd_unrelate(conn, args)
        if args.cmd == "related":
            return cmd_related(conn, args)
        if args.cmd == "set-family":
            return cmd_set_family(conn, args)
        if args.cmd == "resolve":
            return cmd_resolve(conn, args)
        if args.cmd == "archive":
            return cmd_archive(conn, args)
        if args.cmd == "forget":
            return cmd_forget(conn, args)
        print(f"error: unknown cmd {args.cmd}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
