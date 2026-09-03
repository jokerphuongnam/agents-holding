#!/usr/bin/env python3
"""Company durable task memory (SQLite, local-only).

Two-step agent I/O (low token):
  1) index  → load key + short_descript only (pick which memory applies)
  2) get    → fetch that key's `work` payload (what the IC actually uses)

Complements task_cache.py (active pointer JSON).

Staffs/agents read CLI stdout only — never open *.sqlite / sqlite3 / dump.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home  # noqa: E402

SCHEMA_VERSION = "2"

KIND_TASK = "task"
KIND_PATH = "path"
KIND_FAIL = "fail"
KIND_FIX = "fix"
KIND_META = "meta"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str, max_len: int = 48) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-") or "x"
    return s[:max_len]


def default_db_path() -> Path:
    env = os.environ.get("TASK_MEMORY_DB", "").strip()
    if env:
        return Path(env).expanduser()
    return agents_home() / "cache" / "cache" / "task_memory.sqlite"


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory (
            key TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            path_prefix TEXT,
            short_descript TEXT NOT NULL DEFAULT '',
            work TEXT NOT NULL DEFAULT '',
            weight REAL NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory(kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_path ON memory(path_prefix)")
    if conn.execute("SELECT 1 FROM memory WHERE key = ?", ("meta:schema",)).fetchone() is None:
        conn.execute(
            "INSERT INTO memory(key, kind, path_prefix, short_descript, work, weight, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("meta:schema", KIND_META, "", "schema version", SCHEMA_VERSION, 0, utc_now()),
        )
        conn.commit()
    else:
        conn.execute(
            "UPDATE memory SET work = ?, updated_at = ? WHERE key = ?",
            (SCHEMA_VERSION, utc_now(), "meta:schema"),
        )
        conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(memory)").fetchall()}
    # v1 used `value` — rename into work + empty short_descript
    if "value" in cols and "work" not in cols:
        conn.execute("ALTER TABLE memory ADD COLUMN work TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE memory SET work = value")
    if "work" not in cols and "value" not in cols:
        pass  # fresh create already has work
    if "short_descript" not in cols:
        conn.execute(
            "ALTER TABLE memory ADD COLUMN short_descript TEXT NOT NULL DEFAULT ''"
        )
    # ensure work exists on odd states
    cols2 = {r[1] for r in conn.execute("PRAGMA table_info(memory)").fetchall()}
    if "work" not in cols2:
        conn.execute("ALTER TABLE memory ADD COLUMN work TEXT NOT NULL DEFAULT ''")
    # backfill empty short_descript from key so index is usable after v1→v2
    conn.execute(
        """
        UPDATE memory SET short_descript = 'legacy:' || key
        WHERE key != 'meta:schema'
          AND (short_descript IS NULL OR short_descript = '')
        """
    )
    conn.commit()


def kind_of_key(key: str) -> str:
    head = key.split(":", 1)[0]
    return {
        "task": KIND_TASK,
        "path": KIND_PATH,
        "fail": KIND_FAIL,
        "fix": KIND_FIX,
        "meta": KIND_META,
    }.get(head, "other")


def cmd_index(
    conn: sqlite3.Connection,
    prefix: str,
    path: str,
    goal: str,
) -> int:
    """Step 1: key + short_descript only (pick a key). No work payloads."""
    print("col\tkey\tshort_descript")
    rows: list[sqlite3.Row] = []

    if path or goal:
        # filtered candidates
        seen = set()
        if path:
            # exact + prefix match on path_prefix / key
            for r in conn.execute(
                """
                SELECT key, short_descript, weight, path_prefix FROM memory
                WHERE key != 'meta:schema' AND kind != ?
                ORDER BY weight DESC, updated_at DESC
                """,
                (KIND_META,),
            ).fetchall():
                pp = r["path_prefix"] or ""
                k = r["key"]
                if k == f"path:{path}" or (pp and (path == pp or path.startswith(pp))):
                    if k not in seen:
                        seen.add(k)
                        rows.append(r)
                elif k.startswith("fail:") or k.startswith("fix:"):
                    if pp and (path == pp or path.startswith(pp)):
                        if k not in seen:
                            seen.add(k)
                            rows.append(r)
        if goal:
            token = slugify(goal)
            for r in conn.execute(
                """
                SELECT key, short_descript, weight, path_prefix FROM memory
                WHERE key != 'meta:schema' AND kind = ?
                  AND (key LIKE ? OR short_descript LIKE ? OR work LIKE ?)
                ORDER BY weight DESC LIMIT 20
                """,
                (KIND_TASK, f"%{token}%", f"%{token}%", f"%{token}%"),
            ).fetchall():
                if r["key"] not in seen:
                    seen.add(r["key"])
                    rows.append(r)
        if not rows and prefix:
            rows = conn.execute(
                "SELECT key, short_descript FROM memory WHERE key LIKE ? AND key != 'meta:schema' ORDER BY key",
                (prefix + "%",),
            ).fetchall()
    elif prefix:
        rows = conn.execute(
            "SELECT key, short_descript FROM memory WHERE key LIKE ? AND key != 'meta:schema' ORDER BY key",
            (prefix + "%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT key, short_descript FROM memory WHERE key != 'meta:schema' ORDER BY key"
        ).fetchall()

    for r in rows:
        sd = (r["short_descript"] or "").replace("\t", " ").strip() or "—"
        print(f"index\t{r['key']}\t{sd}")
    print(f"count\t{len(rows)}")
    print("next\tget --key <key>  # load work payload for the chosen key")
    print("rule\tstaffs read TSV stdout only — never open sqlite")
    return 0


def cmd_get(conn: sqlite3.Connection, key: str, meta: bool) -> int:
    """Step 2: full row for one key — includes `work` (actual working context)."""
    row = conn.execute(
        "SELECT key, short_descript, work, weight, updated_at, path_prefix, kind "
        "FROM memory WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}", file=sys.stderr)
        return 1
    print(f"key\t{row['key']}")
    print(f"short_descript\t{(row['short_descript'] or '').strip() or '—'}")
    print(f"work\t{(row['work'] or '').strip()}")
    if meta:
        print(f"kind\t{row['kind']}")
        print(f"path_prefix\t{row['path_prefix'] or ''}")
        print(f"weight\t{row['weight']:g}")
        print(f"updated_at\t{row['updated_at']}")
    print("rule\tuse `work` to execute; do not re-open sqlite")
    return 0


def cmd_keys(conn: sqlite3.Connection, prefix: str) -> int:
    """Alias of index (key + short_descript)."""
    return cmd_index(conn, prefix, "", "")


def upsert(
    conn: sqlite3.Connection,
    key: str,
    short_descript: str,
    work: str,
    *,
    kind: Optional[str] = None,
    path_prefix: Optional[str] = None,
    weight: Optional[float] = None,
    bump: bool = False,
) -> None:
    knd = kind or kind_of_key(key)
    existing = conn.execute(
        "SELECT weight, path_prefix, short_descript, work FROM memory WHERE key = ?",
        (key,),
    ).fetchone()
    if existing is None:
        w = 1.0 if weight is None else float(weight)
        conn.execute(
            "INSERT INTO memory(key, kind, path_prefix, short_descript, work, weight, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (key, knd, path_prefix or "", short_descript, work, w, utc_now()),
        )
    else:
        if weight is not None:
            w = float(weight)
        elif bump:
            w = float(existing["weight"]) + 1.0
        else:
            w = float(existing["weight"])
        pp = path_prefix if path_prefix is not None else (existing["path_prefix"] or "")
        sd = short_descript if short_descript else (existing["short_descript"] or "")
        wk = work if work else (existing["work"] or "")
        conn.execute(
            "UPDATE memory SET kind=?, path_prefix=?, short_descript=?, work=?, weight=?, updated_at=? "
            "WHERE key=?",
            (knd, pp, sd, wk, w, utc_now(), key),
        )
    conn.commit()


def cmd_record(
    conn: sqlite3.Connection,
    key: str,
    short_descript: str,
    work: str,
    path_prefix: Optional[str],
    weight: Optional[float],
    bump: bool,
) -> int:
    if key == "meta:schema":
        print("error: meta:schema is reserved", file=sys.stderr)
        return 2
    if not short_descript.strip():
        print("error: --short-descript required (when to use this key)", file=sys.stderr)
        return 2
    if not work.strip():
        print("error: --work required (payload the IC reads to act)", file=sys.stderr)
        return 2
    upsert(
        conn,
        key,
        short_descript.strip(),
        work.strip(),
        path_prefix=path_prefix,
        weight=weight,
        bump=bump,
    )
    return cmd_get(conn, key, meta=True)


def cmd_clear(
    conn: sqlite3.Connection,
    key: Optional[str],
    prefix: Optional[str],
    all_: bool,
) -> int:
    if all_:
        conn.execute("DELETE FROM memory WHERE key != 'meta:schema'")
        conn.commit()
        print("cleared\tall")
        return 0
    if key:
        conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        conn.commit()
        print(f"cleared\t{key}")
        return 0
    if prefix:
        conn.execute(
            "DELETE FROM memory WHERE key LIKE ? AND key != 'meta:schema'",
            (prefix + "%",),
        )
        conn.commit()
        print(f"cleared\tprefix:{prefix}")
        return 0
    print("error: need --key, --prefix, or --all", file=sys.stderr)
    return 2


def cmd_propose(conn: sqlite3.Connection, path: str, goal: str, limit: int) -> int:
    """Filtered index for a path/goal — still key+short_descript only."""
    print(f"path\t{path or '—'}")
    if goal:
        print(f"goal\t{goal}")
    # reuse index filter; trim to limit
    # collect via temporary logic
    rc = cmd_index(conn, "", path, goal)
    return rc


def cmd_record_done(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    goal = (args.goal or "").strip()
    path = (args.path or "").strip()
    if not goal and not path:
        print("error: need --goal and/or --path", file=sys.stderr)
        return 2

    role = (args.role or "").strip()
    summary = (args.summary or "").strip()
    fails = (args.fails or "").strip()
    fixes = (args.fixes or "").strip()
    plan = (args.plan or "").strip()

    work_parts = []
    if summary:
        work_parts.append(f"summary={summary}")
    if role:
        work_parts.append(f"role={role}")
    if path:
        work_parts.append(f"path={path}")
    if plan:
        work_parts.append(f"plan={plan}")
    if fails:
        work_parts.append(f"fails={fails}")
    if fixes:
        work_parts.append(f"fixes={fixes}")
    work = "|".join(work_parts) if work_parts else "done"

    n = 0
    if goal:
        tid = args.task_id.strip() if args.task_id else slugify(goal)
        sd = args.short_descript.strip() if args.short_descript else f"when goal≈{goal}"
        upsert(
            conn,
            f"task:{tid}",
            sd,
            work,
            kind=KIND_TASK,
            path_prefix=path,
            bump=True,
        )
        n += 1
        print(f"recorded\ttask:{tid}\t{sd}")

    if path:
        sd = (
            args.short_descript.strip()
            if args.short_descript
            else f"when working under {path}"
        )
        upsert(
            conn,
            f"path:{path}",
            sd,
            work,
            kind=KIND_PATH,
            path_prefix=path,
            bump=True,
        )
        n += 1
        print(f"recorded\tpath:{path}\t{sd}")

        if fails:
            fk = f"fail:{slugify(path)}:{slugify(fails)[:24]}"
            fsd = f"when hit: {fails}"
            fwork = f"fails={fails}" + (f"|fixes={fixes}" if fixes else "")
            upsert(conn, fk, fsd, fwork, kind=KIND_FAIL, path_prefix=path, bump=True)
            n += 1
            print(f"recorded\t{fk}\t{fsd}")

        if fixes:
            xk = f"fix:{slugify(path)}:{slugify(fixes)[:24]}"
            xsd = f"when applying fix for path {path}"
            xwork = f"fixes={fixes}" + (f"|fails={fails}" if fails else "")
            upsert(conn, xk, xsd, xwork, kind=KIND_FIX, path_prefix=path, bump=True)
            n += 1
            print(f"recorded\t{xk}\t{xsd}")

    print(f"recorded_n\t{n}")
    print("next\tindex / propose → pick key → get --key")
    return 0 if n else 2


def cmd_dump(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT key, kind, path_prefix, short_descript, work, weight, updated_at "
        "FROM memory ORDER BY key"
    ).fetchall()
    print("key\tkind\tpath_prefix\tweight\tupdated_at\tshort_descript\twork")
    for r in rows:
        print(
            f"{r['key']}\t{r['kind']}\t{r['path_prefix']}\t{r['weight']:g}\t"
            f"{r['updated_at']}\t{r['short_descript']}\t{r['work']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Company task memory. index (key+short_descript) → get (work)."
    )
    p.add_argument("--db", default="", help="SQLite path override / TASK_MEMORY_DB")
    sub = p.add_subparsers(dest="cmd", required=True)

    ix = sub.add_parser("index", help="Step1: list key + short_descript (no work)")
    ix.add_argument("--prefix", default="")
    ix.add_argument("--path", default="", help="Filter candidates for this path")
    ix.add_argument("--goal", default="", help="Filter task keys near this goal")

    # backwards-compatible alias
    k = sub.add_parser("keys", help="Alias of index")
    k.add_argument("--prefix", default="")

    g = sub.add_parser("get", help="Step2: load short_descript + work for one key")
    g.add_argument("--key", required=True)
    g.add_argument("--meta", action="store_true")

    r = sub.add_parser("record", help="Upsert one key with short_descript + work")
    r.add_argument("--key", required=True)
    r.add_argument("--short-descript", required=True, help="When to pick this key")
    r.add_argument("--work", required=True, help="Payload the IC reads to act")
    r.add_argument("--path-prefix", default="")
    r.add_argument("--weight", type=float, default=None)
    r.add_argument("--bump", action="store_true")

    rd = sub.add_parser("record-done", help="After work: store task/path/fail/fix rows")
    rd.add_argument("--goal", default="")
    rd.add_argument("--path", default="")
    rd.add_argument("--role", default="")
    rd.add_argument("--summary", default="")
    rd.add_argument("--fails", default="")
    rd.add_argument("--fixes", default="")
    rd.add_argument("--plan", default="")
    rd.add_argument("--task-id", default="")
    rd.add_argument(
        "--short-descript",
        default="",
        help="Override short_descript for task/path rows",
    )

    pr = sub.add_parser(
        "propose",
        help="Filtered index for path/goal (still key+short_descript only)",
    )
    pr.add_argument("--path", default="")
    pr.add_argument("--goal", default="")
    pr.add_argument("--limit", type=int, default=3)

    c = sub.add_parser("clear")
    c.add_argument("--key", default="")
    c.add_argument("--prefix", default="")
    c.add_argument("--all", action="store_true")

    d = sub.add_parser("dump", help="Human/debug ONLY")
    d.add_argument("--i-am-human", action="store_true")
    sub.add_parser("path", help="Print DB path (do not open the file)")
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
            return cmd_index(conn, args.prefix, args.path, args.goal)
        if args.cmd == "keys":
            return cmd_keys(conn, args.prefix)
        if args.cmd == "get":
            return cmd_get(conn, args.key, args.meta)
        if args.cmd == "record":
            return cmd_record(
                conn,
                args.key,
                args.short_descript,
                args.work,
                args.path_prefix or None,
                args.weight,
                args.bump,
            )
        if args.cmd == "record-done":
            return cmd_record_done(conn, args)
        if args.cmd == "propose":
            return cmd_propose(conn, args.path, args.goal, args.limit)
        if args.cmd == "clear":
            return cmd_clear(conn, args.key or None, args.prefix or None, args.all)
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
