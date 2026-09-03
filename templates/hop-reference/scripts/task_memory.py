#!/usr/bin/env python3
"""Company durable task memory (SQLite, local-only).

Per-staff tables: each IC only reads/writes their own cache
(e.g. ux-writer never sees rest-api-dev rows).

Two-step agent I/O (low token):
  1) index --staff <name>  → key + short_descript (pick one)
  2) get   --staff <name> --key <key> → work payload

Staffs/agents read CLI stdout only — never open *.sqlite / dump.
First-pass cost: normal work + cheap record-done (keep short_descript/work compact).
Savings show up on mode=candidates — not by making the first pass 2–3× heavier.
Match equivalent patterns (e.g. List+nav Screens), not identical tasks — exact 1-1 is rare.

work payload is DISTILLED only — never paste full files:
  summary=…|fails=…|fixes=…|refs=path:start-end;path:start-end
Use `snippets` to print only those line ranges.

Cache value (real projects):
  1) reusable pattern refs (not whole sibling files with unrelated chrome)
  2) known bugs already fixed — no-cache often re-hits / only partially re-fixes them
  3) similar/related bugs via short_descript equivalence — transfer fails/fixes
If a run "with cache" costs more than re-hitting the same bugs, usage is wrong.

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

SCHEMA_VERSION = "3"

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


def staff_slug(staff: str) -> str:
    s = staff.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s or not s[0].isalpha():
        s = "s_" + (s or "unknown")
    return s[:48]


def table_for(staff: str) -> str:
    """SQL table name for one staff — isolated from others."""
    return f"staff_{staff_slug(staff)}"


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
        CREATE TABLE IF NOT EXISTS _meta (
            key TEXT PRIMARY KEY,
            work TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _staff_registry (
            staff TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate_legacy_flat(conn)
    conn.execute(
        "INSERT INTO _meta(key, work, updated_at) VALUES(?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET work=excluded.work, updated_at=excluded.updated_at",
        ("schema", SCHEMA_VERSION, utc_now()),
    )
    conn.commit()
    return conn


def ensure_staff_table(conn: sqlite3.Connection, staff: str) -> str:
    t = table_for(staff)
    # table name is sanitized — safe to interpolate
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {t} (
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
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{t}_kind ON {t}(kind)"
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{t}_path ON {t}(path_prefix)"
    )
    conn.execute(
        "INSERT INTO _staff_registry(staff, table_name, updated_at) VALUES(?,?,?) "
        "ON CONFLICT(staff) DO UPDATE SET table_name=excluded.table_name, updated_at=excluded.updated_at",
        (staff.strip(), t, utc_now()),
    )
    conn.commit()
    return t


def _migrate_legacy_flat(conn: sqlite3.Connection) -> None:
    """Move old single `memory` table rows into per-staff tables."""
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "memory" not in tables:
        return
    cols = {r[1] for r in conn.execute("PRAGMA table_info(memory)").fetchall()}
    # ensure short_descript/work exist conceptually
    has_work = "work" in cols
    has_value = "value" in cols
    has_sd = "short_descript" in cols
    rows = conn.execute("SELECT * FROM memory WHERE key != 'meta:schema'").fetchall()
    for r in rows:
        d = dict(r)
        work = (d.get("work") if has_work else None) or (d.get("value") if has_value else "") or ""
        sd = (d.get("short_descript") if has_sd else None) or f"legacy:{d.get('key')}"
        # infer staff from work role=… or fall back unknown
        staff = "unknown"
        m = re.search(r"(?:^|\|)role=([^|]+)", work)
        if m:
            staff = m.group(1).strip()
        t = ensure_staff_table(conn, staff)
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {t}
            (key, kind, path_prefix, short_descript, work, weight, updated_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                d["key"],
                d.get("kind") or kind_of_key(d["key"]),
                d.get("path_prefix") or "",
                sd,
                work,
                float(d.get("weight") or 1),
                d.get("updated_at") or utc_now(),
            ),
        )
    conn.execute("ALTER TABLE memory RENAME TO memory_legacy_v2")
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


def require_staff(staff: Optional[str]) -> str:
    s = (staff or "").strip()
    if not s:
        print(
            "error: --staff <role-name> required (each employee only reads own table)",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return s


def _path_related(path: str, stored: str) -> bool:
    """True if paths are the same area (not required to be byte-identical)."""
    if not path or not stored:
        return False
    a, b = path.rstrip("/"), stored.rstrip("/")
    if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
        return True
    # share a meaningful parent segment (e.g. …/Screens/Foo vs …/Screens/)
    as_, bs = a.split("/"), b.split("/")
    if len(as_) >= 2 and len(bs) >= 2 and as_[:2] == bs[:2]:
        return True
    return False


def _goal_tokens(goal: str) -> list[str]:
    parts = re.findall(r"[a-z0-9]{3,}", goal.lower())
    # drop ultra-common noise
    stop = {"the", "and", "for", "with", "from", "that", "this", "when", "into"}
    return [p for p in parts if p not in stop][:12]


def cmd_index(
    conn: sqlite3.Connection,
    staff: str,
    prefix: str,
    path: str,
    goal: str,
) -> int:
    """List candidate keys. Reuse = equivalent/fitting short_descript, not 1-1 identical task."""
    t = ensure_staff_table(conn, staff)
    print(f"staff\t{staff}")
    print(f"table\t{t}")
    print("col\tkey\tshort_descript")

    rows: list[sqlite3.Row] = []
    seen: set[str] = set()

    def add(r: sqlite3.Row) -> None:
        if r["key"] not in seen:
            seen.add(r["key"])
            rows.append(r)

    all_rows = conn.execute(
        f"""
        SELECT key, short_descript, weight, path_prefix, kind, work FROM {t}
        ORDER BY weight DESC, updated_at DESC
        """
    ).fetchall()

    if path or goal:
        tokens = _goal_tokens(goal) if goal else []
        for r in all_rows:
            pp = r["path_prefix"] or ""
            k = r["key"]
            sd = (r["short_descript"] or "").lower()
            wk = (r["work"] or "").lower()
            hit = False
            if path and (
                k == f"path:{path}"
                or _path_related(path, pp)
                or (k.startswith("path:") and _path_related(path, k[5:]))
            ):
                hit = True
            if tokens:
                blob = f"{k} {sd} {wk}"
                if any(tok in blob for tok in tokens):
                    hit = True
            if hit:
                add(r)
        if not rows and prefix:
            for r in conn.execute(
                f"SELECT key, short_descript FROM {t} WHERE key LIKE ? ORDER BY key",
                (prefix + "%",),
            ).fetchall():
                add(r)
    elif prefix:
        for r in conn.execute(
            f"SELECT key, short_descript FROM {t} WHERE key LIKE ? ORDER BY key",
            (prefix + "%",),
        ).fetchall():
            add(r)
    else:
        for r in all_rows:
            add(r)

    for r in rows:
        sd = (r["short_descript"] or "").replace("\t", " ").strip() or "—"
        print(f"index\t{r['key']}\t{sd}")
    print(f"count\t{len(rows)}")
    # Mandatory gate: index first. Candidates = possible equivalents, not exact clones.
    if len(rows) == 0:
        print("mode\tnew")
        print(
            f"next\tdo the work (no get). When finished MUST "
            f"record-done --staff {staff} (creates cache)."
        )
    else:
        print("mode\tcandidates")
        print(
            f"next\tpick ONE key whose short_descript fits THIS ask "
            f"(equivalent OK — not identical goal/path required). "
            f"If none fit → treat as new. If one fits → "
            f"get --staff {staff} --key <key> → use `work`. "
            f"When finished, if anything changed MUST record-done (upsert overwrites)."
        )
    print(
        "rule\tALWAYS index first. Match by suitability (short_descript), not 1-1 identical tasks. "
        "Staffs read own table via TSV only — never open sqlite / other staff tables"
    )
    return 0


def cmd_get(conn: sqlite3.Connection, staff: str, key: str, meta: bool) -> int:
    t = ensure_staff_table(conn, staff)
    row = conn.execute(
        f"""
        SELECT key, short_descript, work, weight, updated_at, path_prefix, kind
        FROM {t} WHERE key = ?
        """,
        (key,),
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}\tstaff={staff}", file=sys.stderr)
        return 1
    print(f"staff\t{staff}")
    print(f"key\t{row['key']}")
    print(f"short_descript\t{(row['short_descript'] or '').strip() or '—'}")
    print(f"work\t{(row['work'] or '').strip()}")
    if meta:
        print(f"kind\t{row['kind']}")
        print(f"path_prefix\t{row['path_prefix'] or ''}")
        print(f"weight\t{row['weight']:g}")
        print(f"updated_at\t{row['updated_at']}")
        print(f"table\t{t}")
    print("rule\tuse `work` only; do not read other staff caches")
    return 0


def upsert(
    conn: sqlite3.Connection,
    staff: str,
    key: str,
    short_descript: str,
    work: str,
    *,
    kind: Optional[str] = None,
    path_prefix: Optional[str] = None,
    weight: Optional[float] = None,
    bump: bool = False,
) -> None:
    t = ensure_staff_table(conn, staff)
    knd = kind or kind_of_key(key)
    existing = conn.execute(
        f"SELECT weight, path_prefix, short_descript, work FROM {t} WHERE key = ?",
        (key,),
    ).fetchone()
    if existing is None:
        w = 1.0 if weight is None else float(weight)
        conn.execute(
            f"""
            INSERT INTO {t}
            (key, kind, path_prefix, short_descript, work, weight, updated_at)
            VALUES (?,?,?,?,?,?,?)
            """,
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
            f"""
            UPDATE {t}
            SET kind=?, path_prefix=?, short_descript=?, work=?, weight=?, updated_at=?
            WHERE key=?
            """,
            (knd, pp, sd, wk, w, utc_now(), key),
        )
    conn.commit()


def cmd_record(
    conn: sqlite3.Connection,
    staff: str,
    key: str,
    short_descript: str,
    work: str,
    path_prefix: Optional[str],
    weight: Optional[float],
    bump: bool,
) -> int:
    if not short_descript.strip() or not work.strip():
        print("error: --short-descript and --work required", file=sys.stderr)
        return 2
    upsert(
        conn,
        staff,
        key,
        short_descript.strip(),
        work.strip(),
        path_prefix=path_prefix,
        weight=weight,
        bump=bump,
    )
    return cmd_get(conn, staff, key, meta=True)


def cmd_clear(
    conn: sqlite3.Connection,
    staff: str,
    key: Optional[str],
    prefix: Optional[str],
    all_: bool,
) -> int:
    t = ensure_staff_table(conn, staff)
    if all_:
        conn.execute(f"DELETE FROM {t}")
        conn.commit()
        print(f"cleared\tstaff={staff}\tall")
        return 0
    if key:
        conn.execute(f"DELETE FROM {t} WHERE key = ?", (key,))
        conn.commit()
        print(f"cleared\tstaff={staff}\t{key}")
        return 0
    if prefix:
        conn.execute(f"DELETE FROM {t} WHERE key LIKE ?", (prefix + "%",))
        conn.commit()
        print(f"cleared\tstaff={staff}\tprefix:{prefix}")
        return 0
    print("error: need --key, --prefix, or --all", file=sys.stderr)
    return 2


def cmd_propose(conn: sqlite3.Connection, staff: str, path: str, goal: str) -> int:
    print(f"path\t{path or '—'}")
    if goal:
        print(f"goal\t{goal}")
    return cmd_index(conn, staff, "", path, goal)


def _collect_candidates(
    conn: sqlite3.Connection, staff: str, path: str, goal: str
) -> list[sqlite3.Row]:
    """Same matching as index, but return row objects (includes work)."""
    t = ensure_staff_table(conn, staff)
    rows: list[sqlite3.Row] = []
    seen: set[str] = set()

    def add(r: sqlite3.Row) -> None:
        if r["key"] not in seen:
            seen.add(r["key"])
            rows.append(r)

    all_rows = conn.execute(
        f"""
        SELECT key, short_descript, weight, path_prefix, kind, work FROM {t}
        ORDER BY weight DESC, updated_at DESC
        """
    ).fetchall()
    tokens = _goal_tokens(goal) if goal else []
    if path or goal:
        for r in all_rows:
            pp = r["path_prefix"] or ""
            k = r["key"]
            sd = (r["short_descript"] or "").lower()
            wk = (r["work"] or "").lower()
            hit = False
            if path and (
                k == f"path:{path}"
                or _path_related(path, pp)
                or (k.startswith("path:") and _path_related(path, k[5:]))
            ):
                hit = True
            if tokens:
                blob = f"{k} {sd} {wk}"
                if any(tok in blob for tok in tokens):
                    hit = True
            if hit:
                add(r)
    else:
        for r in all_rows:
            add(r)
    return rows


def parse_refs(work: str) -> list[tuple[str, int, int]]:
    """Parse refs=path:start-end;path:start-end from work payload."""
    out: list[tuple[str, int, int]] = []
    m = re.search(r"(?:^|\|)refs=([^|]*)", work or "")
    if not m:
        return out
    blob = m.group(1).strip()
    if not blob:
        return out
    for part in blob.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        # path may contain ':' on Windows — split from right for start-end
        try:
            path_part, rng = part.rsplit(":", 1)
            if "-" not in rng:
                continue
            a, b = rng.split("-", 1)
            start, end = int(a), int(b)
            if start < 1 or end < start:
                continue
            out.append((path_part, start, end))
        except ValueError:
            continue
    return out


def print_snippets(refs: list[tuple[str, int, int]], *, root: Optional[Path] = None) -> int:
    """Print only cited line ranges (distilled context — not full files)."""
    root = root or Path.cwd()
    n = 0
    for rel, start, end in refs:
        path = (root / rel).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            print(f"skip\t{rel}\toutside cwd", file=sys.stderr)
            continue
        if not path.is_file():
            print(f"MISS_REF\t{rel}:{start}-{end}", file=sys.stderr)
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        end = min(end, len(lines))
        print(f"snippet\t{rel}:{start}-{end}")
        for i in range(start - 1, end):
            print(f"{i+1}|{lines[i]}")
        n += 1
    print(f"snippets_n\t{n}")
    return 0 if n else 1


def cmd_resolve(
    conn: sqlite3.Connection,
    staff: str,
    path: str,
    goal: str,
    *,
    with_snippets: bool,
) -> int:
    """One-shot cheap gate: NEW or chosen key+work (no separate index+get)."""
    print(f"staff\t{staff}")
    if path:
        print(f"path\t{path}")
    if goal:
        print(f"goal\t{goal}")
    cands = _collect_candidates(conn, staff, path, goal)
    # Prefer task/path rows over fail/fix splinters for the chosen work payload
    ranked = sorted(
        cands,
        key=lambda r: (
            0 if r["kind"] == KIND_TASK else 1 if r["kind"] == KIND_PATH else 2,
            -float(r["weight"] or 0),
        ),
    )
    if not ranked:
        print("mode\tnew")
        print(
            "next\tdo work; record-done with fails/fixes + refs=file:start-end "
            "(distill only — never cache full files)"
        )
        print("rule\tone CLI call — do not also index/get")
        return 0
    pick = ranked[0]
    work = (pick["work"] or "").strip()
    print("mode\treuse")
    print(f"key\t{pick['key']}")
    print(f"short_descript\t{(pick['short_descript'] or '').strip() or '—'}")
    print(f"work\t{work}")
    # Surface known bugs explicitly (main win vs no-cache re-fixing from scratch)
    for field in ("fails", "fixes", "summary"):
        m = re.search(rf"(?:^|\|){field}=([^|]*)", work)
        if m and m.group(1).strip():
            print(f"{field}\t{m.group(1).strip()}")
    print(f"candidates\t{len(cands)}")
    refs = parse_refs(work)
    if refs:
        print("refs\t" + ";".join(f"{p}:{a}-{b}" for p, a, b in refs))
    print(
        "next\tAVOID re-hitting `fails`; apply `fixes`; read ONLY refs/snippets; "
        "do NOT copy whole siblings; record-done if you learn a related bug/fix"
    )
    print(
        "rule\tcache = pattern refs + known/related bugs — never full-file; "
        "no-cache often re-breaks or only partially re-fixes the same issues"
    )
    if with_snippets and refs:
        print_snippets(refs)
    elif with_snippets and not refs:
        print("note\tno refs= in work — add refs on next record-done", file=sys.stderr)
    return 0


def cmd_snippets(conn: sqlite3.Connection, staff: str, key: str) -> int:
    """Load one key and print only refs= line ranges (anti full-file read)."""
    t = ensure_staff_table(conn, staff)
    row = conn.execute(
        f"SELECT key, work FROM {t} WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        print(f"MISS\t{key}\tstaff={staff}", file=sys.stderr)
        return 1
    work = row["work"] or ""
    print(f"staff\t{staff}")
    print(f"key\t{row['key']}")
    print(f"work\t{work.strip()}")
    refs = parse_refs(work)
    if not refs:
        print("error: work has no refs=file:start-end — cannot snippets", file=sys.stderr)
        return 2
    return print_snippets(refs)


def cmd_record_done(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    staff = require_staff(args.staff or args.role)
    goal = (args.goal or "").strip()
    path = (args.path or "").strip()
    if not goal and not path:
        print("error: need --goal and/or --path", file=sys.stderr)
        return 2

    role = (args.role or staff).strip()
    summary = (args.summary or "").strip()
    fails = (args.fails or "").strip()
    fixes = (args.fixes or "").strip()
    plan = (args.plan or "").strip()
    refs = (getattr(args, "refs", None) or "").strip()
    slim = not getattr(args, "full", False)

    work_parts = []
    if summary:
        work_parts.append(f"summary={summary}")
    work_parts.append(f"role={role}")
    if path:
        work_parts.append(f"path={path}")
    if plan:
        work_parts.append(f"plan={plan}")
    if fails:
        work_parts.append(f"fails={fails}")
    if fixes:
        work_parts.append(f"fixes={fixes}")
    if refs:
        # refs=app/Foo.jsx:40-55;app/Foo.jsx:70-78 — essence pointers, not full files
        work_parts.append(f"refs={refs}")
    work = "|".join(work_parts)
    if not refs:
        print(
            "warn\tno --refs file:start-end — prefer citing only the lines that matter",
            file=sys.stderr,
        )

    n = 0
    sd = (
        args.short_descript.strip()
        if args.short_descript
        else (f"when List+nav empty/204 pattern under {path or 'app'}")
    )

    # Default slim: one path row (+ optional one task row). fails/fixes live inside work.
    if path:
        upsert(conn, staff, f"path:{path}", sd, work, kind=KIND_PATH, path_prefix=path, bump=True)
        n += 1
        print(f"recorded\tstaff={staff}\tpath:{path}\t{sd}")

    if goal:
        tid = args.task_id.strip() if args.task_id else slugify(goal)
        upsert(conn, staff, f"task:{tid}", sd, work, kind=KIND_TASK, path_prefix=path, bump=True)
        n += 1
        print(f"recorded\tstaff={staff}\ttask:{tid}\t{sd}")

    if not slim and path:
        if fails:
            fk = f"fail:{slugify(path)}:{slugify(fails)[:24]}"
            upsert(
                conn,
                staff,
                fk,
                f"when hit: {fails}",
                f"fails={fails}" + (f"|fixes={fixes}" if fixes else "") + f"|role={role}",
                kind=KIND_FAIL,
                path_prefix=path,
                bump=True,
            )
            n += 1
            print(f"recorded\tstaff={staff}\t{fk}")
        if fixes:
            xk = f"fix:{slugify(path)}:{slugify(fixes)[:24]}"
            upsert(
                conn,
                staff,
                xk,
                f"when applying fix for path {path}",
                f"fixes={fixes}" + (f"|fails={fails}" if fails else "") + f"|role={role}",
                kind=KIND_FIX,
                path_prefix=path,
                bump=True,
            )
            n += 1
            print(f"recorded\tstaff={staff}\t{xk}")

    print(f"recorded_n\t{n}")
    print("upsert\toverwrite")
    print(f"next\tnext task: resolve --staff {staff} --path … [--goal …] (one shot)")
    return 0 if n else 2


def cmd_staffs(conn: sqlite3.Connection) -> int:
    """List staff tables that exist (names only — no work). Human/CEO overview."""
    rows = conn.execute(
        "SELECT staff, table_name, updated_at FROM _staff_registry ORDER BY staff"
    ).fetchall()
    print("staff\ttable\tupdated_at")
    for r in rows:
        print(f"{r['staff']}\t{r['table_name']}\t{r['updated_at']}")
    print(f"count\t{len(rows)}")
    print("rule\tICs must not browse other staff tables; use own --staff only")
    return 0


def cmd_dump(conn: sqlite3.Connection, staff: Optional[str]) -> int:
    if staff:
        staffs = [staff]
    else:
        staffs = [
            r["staff"]
            for r in conn.execute("SELECT staff FROM _staff_registry ORDER BY staff")
        ]
    print("staff\tkey\tkind\tpath_prefix\tweight\tupdated_at\tshort_descript\twork")
    for st in staffs:
        t = ensure_staff_table(conn, st)
        for r in conn.execute(
            f"SELECT key, kind, path_prefix, short_descript, work, weight, updated_at FROM {t} ORDER BY key"
        ).fetchall():
            print(
                f"{st}\t{r['key']}\t{r['kind']}\t{r['path_prefix']}\t{r['weight']:g}\t"
                f"{r['updated_at']}\t{r['short_descript']}\t{r['work']}"
            )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Per-staff task memory. index→get; --staff required for ICs."
    )
    p.add_argument("--db", default="")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_staff(sp: argparse.ArgumentParser, required: bool = True) -> None:
        sp.add_argument(
            "--staff",
            required=required,
            default="" if not required else None,
            help="Owner role name (own table only), e.g. swiftui-dev",
        )

    ix = sub.add_parser("index", help="Step1: key+short_descript for ONE staff")
    add_staff(ix)
    ix.add_argument("--prefix", default="")
    ix.add_argument("--path", default="")
    ix.add_argument("--goal", default="")

    k = sub.add_parser("keys", help="Alias of index")
    add_staff(k)
    k.add_argument("--prefix", default="")

    g = sub.add_parser("get", help="Step2: work for one key in staff table")
    add_staff(g)
    g.add_argument("--key", required=True)
    g.add_argument("--meta", action="store_true")

    r = sub.add_parser("record", help="Upsert into staff table")
    add_staff(r)
    r.add_argument("--key", required=True)
    r.add_argument("--short-descript", required=True)
    r.add_argument("--work", required=True)
    r.add_argument("--path-prefix", default="")
    r.add_argument("--weight", type=float, default=None)
    r.add_argument("--bump", action="store_true")

    rd = sub.add_parser("record-done", help="After work: write into --staff table")
    rd.add_argument("--staff", default="", help="Owner (defaults to --role)")
    rd.add_argument("--role", default="", help="Alias/default for --staff")
    rd.add_argument("--goal", default="")
    rd.add_argument("--path", default="")
    rd.add_argument("--summary", default="")
    rd.add_argument("--fails", default="")
    rd.add_argument("--fixes", default="")
    rd.add_argument("--plan", default="")
    rd.add_argument("--task-id", default="")
    rd.add_argument("--short-descript", default="")
    rd.add_argument(
        "--refs",
        default="",
        help="Distilled pointers only: path:start-end;path:start-end (never full file)",
    )
    rd.add_argument(
        "--full",
        action="store_true",
        help="Also write separate fail:/fix: rows (default slim: path+task only)",
    )

    pr = sub.add_parser("propose", help="Filtered index for one staff")
    add_staff(pr)
    pr.add_argument("--path", default="")
    pr.add_argument("--goal", default="")

    rs = sub.add_parser(
        "resolve",
        help="One-shot: NEW or best-fitting key+work (prefer over index+get)",
    )
    add_staff(rs)
    rs.add_argument("--path", default="")
    rs.add_argument("--goal", default="")
    rs.add_argument(
        "--with-snippets",
        action="store_true",
        help="Also print only refs= line ranges (no full-file dump)",
    )

    sn = sub.add_parser(
        "snippets",
        help="Print only refs= line ranges for a key (distilled read)",
    )
    add_staff(sn)
    sn.add_argument("--key", required=True)

    c = sub.add_parser("clear")
    add_staff(c)
    c.add_argument("--key", default="")
    c.add_argument("--prefix", default="")
    c.add_argument("--all", action="store_true")

    sub.add_parser("staffs", help="List staff table names only (no work)")

    d = sub.add_parser("dump", help="Human/debug ONLY")
    d.add_argument("--i-am-human", action="store_true")
    d.add_argument("--staff", default="", help="Limit dump to one staff")
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
        if args.cmd == "staffs":
            return cmd_staffs(conn)
        if args.cmd == "dump":
            if not args.i_am_human:
                print(
                    "error: dump is human-only; agents use resolve --staff. "
                    "Re-run with --i-am-human if debugging locally.",
                    file=sys.stderr,
                )
                return 2
            return cmd_dump(conn, args.staff or None)

        staff = require_staff(getattr(args, "staff", None) or getattr(args, "role", None))

        if args.cmd == "index":
            return cmd_index(conn, staff, args.prefix, args.path, args.goal)
        if args.cmd == "keys":
            return cmd_index(conn, staff, args.prefix, "", "")
        if args.cmd == "get":
            return cmd_get(conn, staff, args.key, args.meta)
        if args.cmd == "record":
            return cmd_record(
                conn,
                staff,
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
            return cmd_propose(conn, staff, args.path, args.goal)
        if args.cmd == "resolve":
            return cmd_resolve(
                conn,
                staff,
                args.path,
                args.goal,
                with_snippets=bool(getattr(args, "with_snippets", False)),
            )
        if args.cmd == "snippets":
            return cmd_snippets(conn, staff, args.key)
        if args.cmd == "clear":
            return cmd_clear(conn, staff, args.key or None, args.prefix or None, args.all)
        print(f"unknown cmd: {args.cmd}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
