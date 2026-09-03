#!/usr/bin/env python3
"""Holding user-habit cache (SQLite, local-only).

Two-step agent I/O (low token):
  1) index  → key + short_descript (pick which habit applies)
  2) get    → load that key's `work` (payload HR actually uses)

Staffs/agents read CLI stdout only — never open *.sqlite / dump.

Store (gitignored):
  <holding>/cache/user_habits.sqlite
  override: HABIT_CACHE_DB=…
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

SCHEMA_VERSION = "2"

KIND_STRUCTURE = "structure"
KIND_DEFAULTS = "defaults"
KIND_CHANGE = "change"
KIND_COMPANY = "company"
KIND_META = "meta"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def holding_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_db_path() -> Path:
    env = os.environ.get("HABIT_CACHE_DB", "").strip()
    if env:
        return Path(env).expanduser()
    return holding_root() / "cache" / "user_habits.sqlite"


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            key TEXT PRIMARY KEY,
            family TEXT,
            kind TEXT NOT NULL,
            short_descript TEXT NOT NULL DEFAULT '',
            work TEXT NOT NULL DEFAULT '',
            weight REAL NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habits_family ON habits(family)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habits_kind ON habits(kind)")
    row = conn.execute("SELECT 1 FROM habits WHERE key = ?", ("meta:schema",)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO habits(key, family, kind, short_descript, work, weight, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("meta:schema", "", KIND_META, "schema version", SCHEMA_VERSION, 0, utc_now()),
        )
    else:
        conn.execute(
            "UPDATE habits SET work = ?, updated_at = ? WHERE key = ?",
            (SCHEMA_VERSION, utc_now(), "meta:schema"),
        )
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(habits)").fetchall()}
    if "value" in cols and "work" not in cols:
        conn.execute("ALTER TABLE habits ADD COLUMN work TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE habits SET work = value")
    if "short_descript" not in cols:
        conn.execute(
            "ALTER TABLE habits ADD COLUMN short_descript TEXT NOT NULL DEFAULT ''"
        )
    cols2 = {r[1] for r in conn.execute("PRAGMA table_info(habits)").fetchall()}
    if "work" not in cols2:
        conn.execute("ALTER TABLE habits ADD COLUMN work TEXT NOT NULL DEFAULT ''")
    conn.execute(
        """
        UPDATE habits SET short_descript = 'legacy:' || key
        WHERE key != 'meta:schema'
          AND (short_descript IS NULL OR short_descript = '')
        """
    )
    conn.commit()


def kind_of_key(key: str) -> str:
    if key.startswith("structure:"):
        return KIND_STRUCTURE
    if key.startswith("defaults:"):
        return KIND_DEFAULTS
    if key.startswith("change:"):
        return KIND_CHANGE
    if key.startswith("company:"):
        return KIND_COMPANY
    if key.startswith("meta:"):
        return KIND_META
    return "other"


def family_of_key(key: str) -> str:
    parts = key.split(":")
    if len(parts) < 2:
        return ""
    if parts[0] in ("structure", "defaults", "change") and len(parts) >= 2:
        return parts[1]
    return ""


def cmd_index(conn: sqlite3.Connection, prefix: str, family: str, intent: str) -> int:
    print("col\tkey\tshort_descript")
    q = "SELECT key, short_descript FROM habits WHERE key != 'meta:schema'"
    args: list[str] = []
    if prefix:
        q += " AND key LIKE ?"
        args.append(prefix + "%")
    if family:
        q += " AND family = ?"
        args.append(family)
    if intent in ("new-company", "new", "create"):
        q += " AND (kind IN ('structure','defaults','change') OR key LIKE 'structure:%' OR key LIKE 'defaults:%' OR key LIKE 'change:%')"
    elif intent in ("restaff", "shortage", "reorg", "hire"):
        q += " AND (kind IN ('company','change','structure') OR key LIKE 'company:%' OR key LIKE 'change:%' OR key LIKE 'structure:%')"
    q += " ORDER BY key"
    rows = conn.execute(q, args).fetchall()
    for r in rows:
        sd = (r["short_descript"] or "").replace("\t", " ").strip() or "—"
        print(f"index\t{r['key']}\t{sd}")
    print(f"count\t{len(rows)}")
    print("next\tget --key <key>  # load work for chosen key")
    print("rule\tstaffs read TSV stdout only — never open sqlite")
    return 0


def cmd_get(conn: sqlite3.Connection, key: str, with_meta: bool) -> int:
    row = conn.execute(
        "SELECT key, short_descript, work, weight, updated_at, family, kind FROM habits WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}", file=sys.stderr)
        return 1
    print(f"key\t{row['key']}")
    print(f"short_descript\t{(row['short_descript'] or '').strip() or '—'}")
    print(f"work\t{(row['work'] or '').strip()}")
    if with_meta:
        print(f"kind\t{row['kind']}")
        print(f"family\t{row['family'] or ''}")
        print(f"weight\t{row['weight']:g}")
        print(f"updated_at\t{row['updated_at']}")
    print("rule\tuse `work` to act; do not re-open sqlite")
    return 0


def upsert(
    conn: sqlite3.Connection,
    key: str,
    short_descript: str,
    work: str,
    *,
    family: Optional[str] = None,
    kind: Optional[str] = None,
    weight: Optional[float] = None,
    bump: bool = False,
) -> None:
    fam = family if family is not None else family_of_key(key)
    knd = kind if kind is not None else kind_of_key(key)
    existing = conn.execute(
        "SELECT weight, short_descript, work FROM habits WHERE key = ?", (key,)
    ).fetchone()
    if existing is None:
        w = 1.0 if weight is None else float(weight)
        conn.execute(
            "INSERT INTO habits(key, family, kind, short_descript, work, weight, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (key, fam, knd, short_descript, work, w, utc_now()),
        )
    else:
        if weight is not None:
            w = float(weight)
        elif bump:
            w = float(existing["weight"]) + 1.0
        else:
            w = float(existing["weight"])
        sd = short_descript if short_descript else (existing["short_descript"] or "")
        wk = work if work else (existing["work"] or "")
        conn.execute(
            "UPDATE habits SET family=?, kind=?, short_descript=?, work=?, weight=?, updated_at=? WHERE key=?",
            (fam, knd, sd, wk, w, utc_now(), key),
        )
    conn.commit()


def cmd_record(
    conn: sqlite3.Connection,
    key: str,
    short_descript: str,
    work: str,
    family: Optional[str],
    weight: Optional[float],
    bump: bool,
) -> int:
    if key == "meta:schema":
        print("error: meta:schema is reserved", file=sys.stderr)
        return 2
    if not short_descript.strip() or not work.strip():
        print("error: --short-descript and --work required", file=sys.stderr)
        return 2
    upsert(
        conn,
        key,
        short_descript.strip(),
        work.strip(),
        family=family,
        weight=weight,
        bump=bump,
    )
    return cmd_get(conn, key, with_meta=True)


def cmd_clear(conn: sqlite3.Connection, key: Optional[str], family: Optional[str], all_: bool) -> int:
    if all_:
        conn.execute("DELETE FROM habits WHERE key != 'meta:schema'")
        conn.commit()
        print("cleared\tall")
        return 0
    if key:
        conn.execute("DELETE FROM habits WHERE key = ?", (key,))
        conn.commit()
        print(f"cleared\t{key}")
        return 0
    if family:
        conn.execute(
            "DELETE FROM habits WHERE family = ? AND key != 'meta:schema'", (family,)
        )
        conn.commit()
        print(f"cleared\tfamily:{family}")
        return 0
    print("error: need --key, --family, or --all", file=sys.stderr)
    return 2


def cmd_propose(conn: sqlite3.Connection, intent: str, family: str, slug: Optional[str]) -> int:
    """Filtered index for intent — key + short_descript only."""
    family = (family or "").strip().lower() or "general"
    intent = intent.strip().lower()
    print(f"intent\t{intent}")
    print(f"family\t{family}")
    if slug:
        print(f"slug\t{slug}")
    if intent in ("restaff", "shortage", "reorg", "hire") and not slug:
        print("error: --slug required for restaff", file=sys.stderr)
        return 2
    # index by family + intent kinds
    cmd_index(conn, "", family, intent)
    if slug:
        # also list company-specific keys
        rows = conn.execute(
            "SELECT key, short_descript FROM habits WHERE key LIKE ? ORDER BY key",
            (f"company:{slug}:%",),
        ).fetchall()
        for r in rows:
            print(f"index\t{r['key']}\t{(r['short_descript'] or '—').strip()}")
    print("note\tprior only — pick one key → get --key; lock with user before writes")
    return 0


def cmd_record_bundle(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    n = 0
    family = (args.family or "").strip().lower() or "general"
    if args.structure:
        sd = args.structure_sd or f"when creating/structuring a {family} company"
        upsert(conn, f"structure:{family}", sd, args.structure, family=family, kind=KIND_STRUCTURE, bump=True)
        n += 1
    if args.defaults:
        sd = args.defaults_sd or f"when choosing budget/tech defaults for {family}"
        upsert(conn, f"defaults:{family}", sd, args.defaults, family=family, kind=KIND_DEFAULTS, bump=True)
        n += 1
    if args.change_pattern:
        val = args.change_value or args.change_pattern
        sd = args.change_sd or f"when restaff pattern={args.change_pattern} on {family}"
        upsert(
            conn,
            f"change:{family}:{args.change_pattern}",
            sd,
            val,
            family=family,
            kind=KIND_CHANGE,
            bump=True,
        )
        n += 1
    if args.slug and args.company_shape:
        sd = args.shape_sd or f"when restaffing company {args.slug}"
        upsert(
            conn,
            f"company:{args.slug}:shape",
            sd,
            args.company_shape,
            family=family,
            kind=KIND_COMPANY,
            bump=False,
        )
        n += 1
    if args.slug and args.last_restaff:
        sd = f"when recalling last restaff of {args.slug}"
        upsert(
            conn,
            f"company:{args.slug}:last_restaff",
            sd,
            args.last_restaff,
            family=family,
            kind=KIND_COMPANY,
            bump=False,
        )
        n += 1
    if n == 0:
        print(
            "error: record-bundle needs --structure/--defaults/--change-pattern "
            "and/or --slug with --company-shape/--last-restaff",
            file=sys.stderr,
        )
        return 2
    print(f"recorded\t{n}\tfamily\t{family}")
    if args.slug:
        print(f"slug\t{args.slug}")
    print("next\tindex / propose → get --key")
    return 0


def cmd_dump(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT key, family, kind, short_descript, work, weight, updated_at FROM habits ORDER BY key"
    ).fetchall()
    print("key\tfamily\tkind\tweight\tupdated_at\tshort_descript\twork")
    for r in rows:
        print(
            f"{r['key']}\t{r['family']}\t{r['kind']}\t{r['weight']:g}\t{r['updated_at']}\t"
            f"{r['short_descript']}\t{r['work']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Holding habit cache. index (key+short_descript) → get (work)."
    )
    p.add_argument("--db", default="")
    sub = p.add_subparsers(dest="cmd", required=True)

    ix = sub.add_parser("index", help="Step1: key + short_descript")
    ix.add_argument("--prefix", default="")
    ix.add_argument("--family", default="")
    ix.add_argument("--intent", default="", help="new-company|restaff filter")

    k = sub.add_parser("keys", help="Alias of index --prefix")
    k.add_argument("--prefix", default="")

    g = sub.add_parser("get", help="Step2: short_descript + work for one key")
    g.add_argument("--key", required=True)
    g.add_argument("--meta", action="store_true")

    r = sub.add_parser("record", help="Upsert key with short_descript + work")
    r.add_argument("--key", required=True)
    r.add_argument("--short-descript", required=True)
    r.add_argument("--work", required=True)
    r.add_argument("--family", default="")
    r.add_argument("--weight", type=float, default=None)
    r.add_argument("--bump", action="store_true")

    rb = sub.add_parser("record-bundle", help="After lock: write structure/defaults/change/company")
    rb.add_argument("--family", required=True)
    rb.add_argument("--structure", default="")
    rb.add_argument("--structure-sd", default="")
    rb.add_argument("--defaults", default="")
    rb.add_argument("--defaults-sd", default="")
    rb.add_argument("--change-pattern", default="")
    rb.add_argument("--change-value", default="")
    rb.add_argument("--change-sd", default="")
    rb.add_argument("--slug", default="")
    rb.add_argument("--company-shape", default="")
    rb.add_argument("--shape-sd", default="")
    rb.add_argument("--last-restaff", default="")

    pr = sub.add_parser("propose", help="Filtered index for new-company|restaff")
    pr.add_argument("--intent", required=True)
    pr.add_argument("--family", required=True)
    pr.add_argument("--slug", default="")

    c = sub.add_parser("clear")
    c.add_argument("--key", default="")
    c.add_argument("--family", default="")
    c.add_argument("--all", action="store_true")

    d = sub.add_parser("dump", help="Human/debug ONLY")
    d.add_argument("--i-am-human", action="store_true")
    sub.add_parser("path", help="Print DB path")
    return p


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    db = Path(args.db).expanduser() if args.db else default_db_path()
    if args.cmd == "path":
        print(db)
        return 0
    conn = connect(db)
    try:
        if args.cmd == "index":
            return cmd_index(conn, args.prefix, args.family, args.intent)
        if args.cmd == "keys":
            return cmd_index(conn, args.prefix, "", "")
        if args.cmd == "get":
            return cmd_get(conn, args.key, args.meta)
        if args.cmd == "record":
            return cmd_record(
                conn,
                args.key,
                args.short_descript,
                args.work,
                args.family or None,
                args.weight,
                args.bump,
            )
        if args.cmd == "record-bundle":
            return cmd_record_bundle(conn, args)
        if args.cmd == "propose":
            return cmd_propose(conn, args.intent, args.family, args.slug or None)
        if args.cmd == "clear":
            return cmd_clear(conn, args.key or None, args.family or None, args.all)
        if args.cmd == "dump":
            if not args.i_am_human:
                print(
                    "error: dump is human-only; agents use index→get. "
                    "Re-run with --i-am-human if debugging locally.",
                    file=sys.stderr,
                )
                return 2
            return cmd_dump(conn)
        print(f"unknown cmd: {args.cmd}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
