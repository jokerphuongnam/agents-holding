#!/usr/bin/env python3
"""Company durable task memory (SQLite, local-only).

Complements task_cache.py:
  - task_cache  = active pointer (current goal/role) — JSON
  - task_memory = durable keyed memory of past work, fail modes, fixes

Agents / staffs MUST use this CLI stdout only (compact TSV).
Forbidden for agents: opening the DB file, sqlite3 shell, read_file on *.sqlite,
or pasting `dump` into prompts. Fetch by key (or propose for a path/goal) only.

Store (under company cache/cache/, typically gitignored):
  <company>/cache/cache/task_memory.sqlite
  override: TASK_MEMORY_DB=/path/to/file.sqlite
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

SCHEMA_VERSION = "1"

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
            value TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory(kind)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_path ON memory(path_prefix)"
    )
    if conn.execute("SELECT 1 FROM memory WHERE key = ?", ("meta:schema",)).fetchone() is None:
        conn.execute(
            "INSERT INTO memory(key, kind, path_prefix, value, weight, updated_at) VALUES (?,?,?,?,?,?)",
            ("meta:schema", KIND_META, "", SCHEMA_VERSION, 0, utc_now()),
        )
        conn.commit()
    return conn


def kind_of_key(key: str) -> str:
    head = key.split(":", 1)[0]
    return {
        "task": KIND_TASK,
        "path": KIND_PATH,
        "fail": KIND_FAIL,
        "fix": KIND_FIX,
        "meta": KIND_META,
    }.get(head, "other")


def print_kv(key: str, value: str, weight: float, updated_at: str, *, meta: bool) -> None:
    if meta:
        print(f"{key}\t{value}\tw={weight:g}\t@{updated_at}")
    else:
        print(f"{key}\t{value}")


def cmd_get(conn: sqlite3.Connection, key: str, meta: bool) -> int:
    row = conn.execute(
        "SELECT key, value, weight, updated_at FROM memory WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}", file=sys.stderr)
        return 1
    print_kv(row["key"], row["value"], row["weight"], row["updated_at"], meta=meta)
    return 0


def cmd_keys(conn: sqlite3.Connection, prefix: str) -> int:
    if prefix:
        rows = conn.execute(
            "SELECT key, weight, updated_at FROM memory WHERE key LIKE ? ORDER BY key",
            (prefix + "%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT key, weight, updated_at FROM memory WHERE key != 'meta:schema' ORDER BY key"
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
    kind: Optional[str] = None,
    path_prefix: Optional[str] = None,
    weight: Optional[float] = None,
    bump: bool = False,
) -> None:
    knd = kind or kind_of_key(key)
    existing = conn.execute(
        "SELECT weight, path_prefix FROM memory WHERE key = ?", (key,)
    ).fetchone()
    if existing is None:
        w = 1.0 if weight is None else float(weight)
        pp = path_prefix or ""
        conn.execute(
            "INSERT INTO memory(key, kind, path_prefix, value, weight, updated_at) VALUES (?,?,?,?,?,?)",
            (key, knd, pp, value, w, utc_now()),
        )
    else:
        if weight is not None:
            w = float(weight)
        elif bump:
            w = float(existing["weight"]) + 1.0
        else:
            w = float(existing["weight"])
        pp = path_prefix if path_prefix is not None else (existing["path_prefix"] or "")
        conn.execute(
            "UPDATE memory SET kind=?, path_prefix=?, value=?, weight=?, updated_at=? WHERE key=?",
            (knd, pp, value, w, utc_now(), key),
        )
    conn.commit()


def cmd_record(
    conn: sqlite3.Connection,
    key: str,
    value: str,
    path_prefix: Optional[str],
    weight: Optional[float],
    bump: bool,
) -> int:
    if key == "meta:schema":
        print("error: meta:schema is reserved", file=sys.stderr)
        return 2
    upsert(conn, key, value, path_prefix=path_prefix, weight=weight, bump=bump)
    row = conn.execute(
        "SELECT key, value, weight, updated_at FROM memory WHERE key = ?", (key,)
    ).fetchone()
    print_kv(row["key"], row["value"], row["weight"], row["updated_at"], meta=True)
    return 0


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
        conn.execute("DELETE FROM memory WHERE key LIKE ?", (prefix + "%",))
        conn.commit()
        print(f"cleared\tprefix:{prefix}")
        return 0
    print("error: need --key, --prefix, or --all", file=sys.stderr)
    return 2


def cmd_propose(
    conn: sqlite3.Connection,
    path: str,
    goal: str,
    limit: int,
) -> int:
    """Compact prior for a path/goal — avoid full hop re-derivation when HIT."""
    path = (path or "").strip()
    goal = (goal or "").strip()
    print(f"path\t{path or '—'}")
    if goal:
        print(f"goal\t{goal}")

    hits = 0

    # Exact path key
    if path:
        row = conn.execute(
            "SELECT key, value, weight, updated_at FROM memory WHERE key = ?",
            (f"path:{path}",),
        ).fetchone()
        if row:
            hits += 1
            print(f"path_hit\t{row['key']}\t{row['value']}")
        else:
            # Longest prefix match among path:* keys
            candidates = conn.execute(
                """
                SELECT key, value, weight, path_prefix, updated_at FROM memory
                WHERE kind = ? AND path_prefix != ''
                ORDER BY length(path_prefix) DESC, weight DESC
                """,
                (KIND_PATH,),
            ).fetchall()
            matched = None
            for c in candidates:
                pp = c["path_prefix"] or ""
                if path == pp or path.startswith(pp):
                    matched = c
                    break
            if matched:
                hits += 1
                print(f"path_prefix\t{matched['key']}\t{matched['value']}")
            else:
                print("path_hit\tMISS")

        # Fails / fixes tied to this path prefix
        fails = conn.execute(
            """
            SELECT key, value, weight FROM memory
            WHERE kind = ? AND (path_prefix = ? OR ? LIKE path_prefix || '%')
            ORDER BY weight DESC, updated_at DESC LIMIT ?
            """,
            (KIND_FAIL, path, path, limit),
        ).fetchall()
        fixes = conn.execute(
            """
            SELECT key, value, weight FROM memory
            WHERE kind = ? AND (path_prefix = ? OR ? LIKE path_prefix || '%')
            ORDER BY weight DESC, updated_at DESC LIMIT ?
            """,
            (KIND_FIX, path, path, limit),
        ).fetchall()
        if fails:
            for r in fails:
                hits += 1
                print(f"fail\t{r['key']}\t{r['value']}")
        else:
            print("fail\tMISS")
        if fixes:
            for r in fixes:
                hits += 1
                print(f"fix\t{r['key']}\t{r['value']}")
        else:
            print("fix\tMISS")

    # Goal → task key fingerprint
    if goal:
        tid = slugify(goal)
        row = conn.execute(
            "SELECT key, value FROM memory WHERE key = ?", (f"task:{tid}",)
        ).fetchone()
        if row:
            hits += 1
            print(f"task_hit\t{row['key']}\t{row['value']}")
        else:
            # fuzzy: goal tokens in value
            token = slugify(goal)[:20]
            rows = conn.execute(
                """
                SELECT key, value, weight FROM memory
                WHERE kind = ? AND (key LIKE ? OR value LIKE ?)
                ORDER BY weight DESC LIMIT ?
                """,
                (KIND_TASK, f"%{token}%", f"%{token}%", limit),
            ).fetchall()
            if rows:
                for r in rows:
                    hits += 1
                    print(f"task_near\t{r['key']}\t{r['value']}")
            else:
                print("task_hit\tMISS")

    print(f"hits\t{hits}")
    print(
        "note\tHIT → resume/edit from memory; skip full re-hop when role/path still valid. "
        "MISS → hop once. Always refresh task_cache active pointer."
    )
    print("rule\tstaffs read this TSV only — never open sqlite")
    return 0


def cmd_record_done(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    """After a hop finishes: store task + path + optional fail/fix compact lines."""
    goal = (args.goal or "").strip()
    path = (args.path or "").strip()
    if not goal and not path:
        print("error: need --goal and/or --path", file=sys.stderr)
        return 2

    n = 0
    role = (args.role or "").strip()
    summary = (args.summary or "").strip()
    fails = (args.fails or "").strip()
    fixes = (args.fixes or "").strip()
    plan = (args.plan or "").strip()

    parts = []
    if summary:
        parts.append(f"summary={summary}")
    if role:
        parts.append(f"role={role}")
    if path:
        parts.append(f"path={path}")
    if plan:
        parts.append(f"plan={plan}")
    if fails:
        parts.append(f"fails={fails}")
    if fixes:
        parts.append(f"fixes={fixes}")
    value = "|".join(parts) if parts else "done"

    if goal:
        tid = args.task_id.strip() if args.task_id else slugify(goal)
        upsert(
            conn,
            f"task:{tid}",
            value,
            kind=KIND_TASK,
            path_prefix=path,
            bump=True,
        )
        n += 1
        print(f"recorded\ttask:{tid}")

    if path:
        upsert(
            conn,
            f"path:{path}",
            value,
            kind=KIND_PATH,
            path_prefix=path,
            bump=True,
        )
        n += 1
        print(f"recorded\tpath:{path}")

        if fails:
            fk = f"fail:{slugify(path)}:{slugify(fails)[:24]}"
            upsert(
                conn,
                fk,
                f"fails={fails}" + (f"|fixes={fixes}" if fixes else ""),
                kind=KIND_FAIL,
                path_prefix=path,
                bump=True,
            )
            n += 1
            print(f"recorded\t{fk}")

        if fixes:
            xk = f"fix:{slugify(path)}:{slugify(fixes)[:24]}"
            upsert(
                conn,
                xk,
                f"fixes={fixes}" + (f"|fails={fails}" if fails else ""),
                kind=KIND_FIX,
                path_prefix=path,
                bump=True,
            )
            n += 1
            print(f"recorded\t{xk}")

    print(f"recorded_n\t{n}")
    return 0 if n else 2


def cmd_dump(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT key, kind, path_prefix, value, weight, updated_at FROM memory ORDER BY key"
    ).fetchall()
    print("key\tkind\tpath_prefix\tweight\tupdated_at\tvalue")
    for r in rows:
        print(
            f"{r['key']}\t{r['kind']}\t{r['path_prefix']}\t{r['weight']:g}\t{r['updated_at']}\t{r['value']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Company task memory (SQLite). Use get/propose by key — not dump."
    )
    p.add_argument("--db", default="", help="SQLite path override / TASK_MEMORY_DB")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="Fetch one key")
    g.add_argument("--key", required=True)
    g.add_argument("--meta", action="store_true")

    k = sub.add_parser("keys", help="List keys (optional prefix)")
    k.add_argument("--prefix", default="")

    r = sub.add_parser("record", help="Upsert one key")
    r.add_argument("--key", required=True)
    r.add_argument("--value", required=True)
    r.add_argument("--path-prefix", default="")
    r.add_argument("--weight", type=float, default=None)
    r.add_argument("--bump", action="store_true")

    rd = sub.add_parser(
        "record-done",
        help="After work: store task/path (+ optional fails/fixes) in compact form",
    )
    rd.add_argument("--goal", default="")
    rd.add_argument("--path", default="")
    rd.add_argument("--role", default="")
    rd.add_argument("--summary", default="")
    rd.add_argument("--fails", default="", help="Known failure mode (short)")
    rd.add_argument("--fixes", default="", help="What fixed it (short)")
    rd.add_argument("--plan", default="")
    rd.add_argument("--task-id", default="", help="Override slug for task: key")

    pr = sub.add_parser("propose", help="Prior for path/goal before hop")
    pr.add_argument("--path", default="")
    pr.add_argument("--goal", default="")
    pr.add_argument("--limit", type=int, default=3)

    c = sub.add_parser("clear")
    c.add_argument("--key", default="")
    c.add_argument("--prefix", default="")
    c.add_argument("--all", action="store_true")

    d = sub.add_parser(
        "dump",
        help="Human/debug ONLY — agents must not run this or paste output",
    )
    d.add_argument(
        "--i-am-human",
        action="store_true",
        help="Required gate so agents do not call dump by mistake",
    )
    sub.add_parser("path", help="Print DB path (path only — still do not open the file)")
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
