#!/usr/bin/env python3
"""Holding user-habit cache (SQLite, local-only).

Single-user prefs for new-company + restaff. Agents MUST use this CLI —
never open the DB or dump all rows into a prompt. Fetch by key only.

Store (gitignored):
  <holding>/cache/user_habits.sqlite
  override: HABIT_CACHE_DB=/path/to/file.sqlite

Agent-facing output is compact TSV / one-liners (low token).
Staffs/agents read CLI stdout only — never open the SQLite file.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


SCHEMA_VERSION = "1"

# kind values
KIND_STRUCTURE = "structure"
KIND_DEFAULTS = "defaults"
KIND_CHANGE = "change"
KIND_COMPANY = "company"
KIND_META = "meta"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def holding_root() -> Path:
    """…/holding — script lives at holding/system/install/habit_cache.py."""
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
            value TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_habits_family ON habits(family)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habits_kind ON habits(kind)")
    # schema marker
    cur = conn.execute("SELECT value FROM habits WHERE key = ?", ("meta:schema",))
    row = cur.fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO habits(key, family, kind, value, weight, updated_at) VALUES (?,?,?,?,?,?)",
            ("meta:schema", "", KIND_META, SCHEMA_VERSION, 0, utc_now()),
        )
        conn.commit()
    return conn


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
    # structure:mobile | defaults:web | change:mobile:add_ic | company:slug:shape
    parts = key.split(":")
    if len(parts) < 2:
        return ""
    if parts[0] in ("structure", "defaults") and len(parts) >= 2:
        return parts[1]
    if parts[0] == "change" and len(parts) >= 2:
        return parts[1]
    return ""


def print_row(key: str, value: str, weight: float, updated_at: str, *, with_meta: bool) -> None:
    if with_meta:
        print(f"{key}\t{value}\tw={weight:g}\t@{updated_at}")
    else:
        # agent default: key + value only
        print(f"{key}\t{value}")


def cmd_get(conn: sqlite3.Connection, key: str, with_meta: bool) -> int:
    row = conn.execute(
        "SELECT key, value, weight, updated_at FROM habits WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}", file=sys.stderr)
        return 1
    print_row(row["key"], row["value"], row["weight"], row["updated_at"], with_meta=with_meta)
    return 0


def cmd_keys(conn: sqlite3.Connection, prefix: str) -> int:
    if prefix:
        rows = conn.execute(
            "SELECT key, weight, updated_at FROM habits WHERE key LIKE ? ORDER BY key",
            (prefix + "%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT key, weight, updated_at FROM habits WHERE key != 'meta:schema' ORDER BY key"
        ).fetchall()
    print("key\tweight\tupdated_at")
    for r in rows:
        print(f"{r['key']}\t{r['weight']:g}\t{r['updated_at']}")
    return 0


def upsert(
    conn: sqlite3.Connection,
    key: str,
    value: str,
    *,
    family: Optional[str] = None,
    kind: Optional[str] = None,
    weight: Optional[float] = None,
    bump: bool = False,
) -> None:
    fam = family if family is not None else family_of_key(key)
    knd = kind if kind is not None else kind_of_key(key)
    existing = conn.execute(
        "SELECT weight FROM habits WHERE key = ?", (key,)
    ).fetchone()
    if existing is None:
        w = 1.0 if weight is None else float(weight)
        conn.execute(
            "INSERT INTO habits(key, family, kind, value, weight, updated_at) VALUES (?,?,?,?,?,?)",
            (key, fam, knd, value, w, utc_now()),
        )
    else:
        if weight is not None:
            w = float(weight)
        elif bump:
            w = float(existing["weight"]) + 1.0
        else:
            w = float(existing["weight"])
        conn.execute(
            "UPDATE habits SET family=?, kind=?, value=?, weight=?, updated_at=? WHERE key=?",
            (fam, knd, value, w, utc_now(), key),
        )
    conn.commit()


def cmd_record(
    conn: sqlite3.Connection,
    key: str,
    value: str,
    family: Optional[str],
    weight: Optional[float],
    bump: bool,
) -> int:
    if key == "meta:schema":
        print("error: meta:schema is reserved", file=sys.stderr)
        return 2
    upsert(conn, key, value, family=family, weight=weight, bump=bump)
    row = conn.execute(
        "SELECT key, value, weight, updated_at FROM habits WHERE key = ?", (key,)
    ).fetchone()
    print_row(row["key"], row["value"], row["weight"], row["updated_at"], with_meta=True)
    return 0


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


def top_changes(conn: sqlite3.Connection, family: str, limit: int = 3) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT key, value, weight, updated_at FROM habits
        WHERE kind = ? AND family = ?
        ORDER BY weight DESC, updated_at DESC
        LIMIT ?
        """,
        (KIND_CHANGE, family, limit),
    ).fetchall()


def get_optional(conn: sqlite3.Connection, key: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT key, value, weight, updated_at FROM habits WHERE key = ?", (key,)
    ).fetchone()


def cmd_propose(
    conn: sqlite3.Connection,
    intent: str,
    family: str,
    slug: Optional[str],
) -> int:
    """Print only the prior lines needed for this intent (low token)."""
    family = (family or "").strip().lower() or "general"
    intent = intent.strip().lower()
    print(f"intent\t{intent}")
    print(f"family\t{family}")
    if slug:
        print(f"slug\t{slug}")

    hits = 0

    def emit(row: Optional[sqlite3.Row], label: str) -> None:
        nonlocal hits
        if row is None:
            print(f"{label}\tMISS")
            return
        hits += 1
        print(f"{label}\t{row['key']}\t{row['value']}")

    if intent in ("new-company", "new", "create"):
        emit(get_optional(conn, f"structure:{family}"), "structure")
        emit(get_optional(conn, f"defaults:{family}"), "defaults")
        changes = top_changes(conn, family, 3)
        if not changes:
            print("change_top\tMISS")
        else:
            # one compact line: pattern:weight|…
            parts = []
            for r in changes:
                # change:mobile:add_ic → add_ic
                pat = r["key"].split(":")[-1] if ":" in r["key"] else r["key"]
                parts.append(f"{pat}:{r['weight']:g}")
            print("change_top\t" + "|".join(parts))
            for r in changes:
                print(f"change\t{r['key']}\t{r['value']}")
                hits += 1

    elif intent in ("restaff", "shortage", "reorg", "hire"):
        if not slug:
            print("error: --slug required for restaff", file=sys.stderr)
            return 2
        emit(get_optional(conn, f"company:{slug}:shape"), "shape")
        emit(get_optional(conn, f"company:{slug}:last_restaff"), "last_restaff")
        # fallback structure prior for the family
        emit(get_optional(conn, f"structure:{family}"), "structure_fallback")
        changes = top_changes(conn, family, 3)
        if not changes:
            print("change_top\tMISS")
        else:
            parts = []
            for r in changes:
                pat = r["key"].split(":")[-1] if ":" in r["key"] else r["key"]
                parts.append(f"{pat}:{r['weight']:g}")
            print("change_top\t" + "|".join(parts))
            for r in changes:
                print(f"change\t{r['key']}\t{r['value']}")
                hits += 1
    else:
        print(
            "error: --intent must be new-company|restaff",
            file=sys.stderr,
        )
        return 2

    print(f"hits\t{hits}")
    print("note\tprior only — lock with user before create-company / writing staffs")
    return 0 if hits else 0  # MISS-only is still OK (empty prior)


def cmd_dump(conn: sqlite3.Connection) -> int:
    """Human debug — do not use in agent prompts."""
    rows = conn.execute(
        "SELECT key, family, kind, value, weight, updated_at FROM habits ORDER BY key"
    ).fetchall()
    print("key\tfamily\tkind\tweight\tupdated_at\tvalue")
    for r in rows:
        print(
            f"{r['key']}\t{r['family']}\t{r['kind']}\t{r['weight']:g}\t{r['updated_at']}\t{r['value']}"
        )
    return 0


def cmd_record_bundle(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """After user lock: write structure/defaults/change and/or company shape."""
    n = 0
    family = (args.family or "").strip().lower() or "general"
    if args.structure:
        upsert(
            conn,
            f"structure:{family}",
            args.structure,
            family=family,
            kind=KIND_STRUCTURE,
            bump=True,
        )
        n += 1
    if args.defaults:
        upsert(
            conn,
            f"defaults:{family}",
            args.defaults,
            family=family,
            kind=KIND_DEFAULTS,
            bump=True,
        )
        n += 1
    if args.change_pattern:
        # value may be empty → store pattern name as reminder
        val = args.change_value or args.change_pattern
        upsert(
            conn,
            f"change:{family}:{args.change_pattern}",
            val,
            family=family,
            kind=KIND_CHANGE,
            bump=True,
        )
        n += 1
    if args.slug and args.company_shape:
        upsert(
            conn,
            f"company:{args.slug}:shape",
            args.company_shape,
            family=family,
            kind=KIND_COMPANY,
            bump=False,
        )
        n += 1
    if args.slug and args.last_restaff:
        upsert(
            conn,
            f"company:{args.slug}:last_restaff",
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
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Holding habit cache (SQLite). Agents: get/propose by key only."
    )
    p.add_argument(
        "--db",
        default="",
        help="SQLite path (default: <holding>/cache/user_habits.sqlite or HABIT_CACHE_DB)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="Fetch one key (MISS → exit 1)")
    g.add_argument("--key", required=True)
    g.add_argument("--meta", action="store_true", help="Include weight + updated_at")

    k = sub.add_parser("keys", help="List keys only (optional prefix)")
    k.add_argument("--prefix", default="")

    r = sub.add_parser("record", help="Upsert one key=value")
    r.add_argument("--key", required=True)
    r.add_argument("--value", required=True)
    r.add_argument("--family", default="")
    r.add_argument("--weight", type=float, default=None)
    r.add_argument("--bump", action="store_true", help="Increment weight on update")

    rb = sub.add_parser(
        "record-bundle",
        help="After lock: write structure/defaults/change and/or company shape",
    )
    rb.add_argument("--family", required=True)
    rb.add_argument("--structure", default="")
    rb.add_argument("--defaults", default="")
    rb.add_argument("--change-pattern", default="", help="e.g. add_ic, add_lead, bump_budget")
    rb.add_argument("--change-value", default="")
    rb.add_argument("--slug", default="")
    rb.add_argument("--company-shape", default="")
    rb.add_argument("--last-restaff", default="")

    pr = sub.add_parser("propose", help="Compact prior for new-company|restaff")
    pr.add_argument("--intent", required=True, help="new-company | restaff")
    pr.add_argument("--family", required=True, help="mobile|web|backend|general|…")
    pr.add_argument("--slug", default="", help="Required for restaff")

    c = sub.add_parser("clear", help="Delete keys")
    c.add_argument("--key", default="")
    c.add_argument("--family", default="")
    c.add_argument("--all", action="store_true")

    d = sub.add_parser("dump", help="Human/debug ONLY — agents must not run this")
    d.add_argument("--i-am-human", action="store_true", help="Required gate for dump")
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
        if args.cmd == "get":
            return cmd_get(conn, args.key, args.meta)
        if args.cmd == "keys":
            return cmd_keys(conn, args.prefix)
        if args.cmd == "record":
            return cmd_record(
                conn,
                args.key,
                args.value,
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
            if not getattr(args, "i_am_human", False):
                print(
                    "error: dump is human-only; agents use propose/get. "
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
