#!/usr/bin/env python3
"""Plan create/edit/delete history for one company. Filesystem is the source.

Any writer (terminal, agent, app) only touches ``cache/plans``. This script
diffs those files into ``cache/plan_history.sqlite``. Run ``sync`` after a
change, or ``watch`` so a backend process records edits while they happen.

Actor:
  --actor / $AGENTS_STAFF when the caller knows the PO.
  Otherwise a new file uses the owner line, else ``po-new``.
  An edit or delete with no actor is stored as the OS user.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_files (
  path TEXT PRIMARY KEY,
  sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plan_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_path TEXT NOT NULL,
  kind TEXT NOT NULL,
  actor TEXT NOT NULL,
  at TEXT NOT NULL,
  source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS plan_events_path ON plan_events (plan_path, id);
"""

OWNER_RE = re.compile(r"^\s*>?\s*\**\s*(?:plan\s+)?owner\s*:\**\s*(.+)$", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_birth(path: Path) -> str:
    st = path.stat()
    stamp = getattr(st, "st_birthtime", None) or st.st_mtime
    return datetime.fromtimestamp(stamp, timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def is_plan(rel: str) -> bool:
    low = rel.lower().replace("\\", "/")
    if "/references/" in f"/{low}/":
        return False
    name = Path(low).name
    if name in {"readme.md", "changelog.md", "skill.md"}:
        return False
    return name.endswith(".md") and ("plan" in name or "roadmap" in name)


def plans_under(company: Path) -> dict[str, Path]:
    root = company / "cache" / "plans"
    found: dict[str, Path] = {}
    if not root.is_dir():
        return found
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if is_plan(rel):
            found[rel] = path
    return found


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def owner_actor(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:60]
    except OSError:
        return None
    for line in lines:
        match = OWNER_RE.match(line.strip())
        if not match:
            continue
        tokens = re.findall(r"[A-Za-z0-9_-]+", match.group(1).replace("`", ""))
        for token in tokens:
            if token.lower().startswith("po-"):
                return token
    return None


def actor_for(kind: str, path: Path | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("AGENTS_STAFF", "").strip()
    if env:
        return env
    if kind == "created" and path is not None:
        return owner_actor(path) or "po-new"
    return os.environ.get("USER") or "unknown"


def insert_event(conn: sqlite3.Connection, path: str, kind: str, actor: str, at: str, source: str) -> None:
    conn.execute(
        "INSERT INTO plan_events (plan_path, kind, actor, at, source) VALUES (?, ?, ?, ?, ?)",
        (path, kind, actor, at, source),
    )


def sync(company: Path, explicit_actor: str | None, source: str) -> list[tuple[str, str, str]]:
    conn = connect(company / "cache" / "plan_history.sqlite")
    current = plans_under(company)
    known = {row[0]: row[1] for row in conn.execute("SELECT path, sha256 FROM plan_files")}
    changes: list[tuple[str, str, str]] = []

    backfill = source == "backfill"
    for rel, path in sorted(current.items()):
        digest = sha256(path)
        if rel not in known:
            actor = actor_for("created", path, None if backfill else explicit_actor)
            when = file_birth(path) if backfill else utc_now()
            insert_event(conn, rel, "created", actor, when, "backfill" if backfill else source)
            conn.execute(
                "INSERT INTO plan_files (path, sha256) VALUES (?, ?)",
                (rel, digest),
            )
            changes.append(("created", rel, actor))
        elif known[rel] != digest:
            actor = actor_for("edited", path, explicit_actor)
            insert_event(conn, rel, "edited", actor, utc_now(), source)
            conn.execute("UPDATE plan_files SET sha256 = ? WHERE path = ?", (digest, rel))
            changes.append(("edited", rel, actor))

    for rel in sorted(set(known) - set(current)):
        actor = actor_for("deleted", None, explicit_actor)
        insert_event(conn, rel, "deleted", actor, utc_now(), source)
        conn.execute("DELETE FROM plan_files WHERE path = ?", (rel,))
        changes.append(("deleted", rel, actor))

    conn.commit()
    conn.close()
    return changes


def first_sync_is_backfill(company: Path) -> bool:
    return not (company / "cache" / "plan_history.sqlite").exists()


def list_events(company: Path, plan: str | None) -> None:
    db_path = company / "cache" / "plan_history.sqlite"
    if not db_path.exists():
        return
    conn = connect(db_path)
    if plan:
        rows = conn.execute(
            "SELECT at, kind, actor, plan_path, source FROM plan_events WHERE plan_path = ? ORDER BY id",
            (plan,),
        )
    else:
        rows = conn.execute(
            "SELECT at, kind, actor, plan_path, source FROM plan_events ORDER BY id"
        )
    for at, kind, actor, path, source in rows:
        print(f"{at}\t{kind}\t{actor}\t{path}\t{source}")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Record plan create/edit/delete history")
    parser.add_argument("command", choices=("sync", "watch", "list"))
    parser.add_argument("--company", required=True, help="Company root (the *-company directory)")
    parser.add_argument("--actor", default="", help="PO staff name. Defaults to $AGENTS_STAFF")
    parser.add_argument("--plan", default="", help="Relative path under cache/plans for list")
    parser.add_argument("--interval", type=float, default=2.0, help="watch poll seconds")
    args = parser.parse_args()
    company = Path(args.company).expanduser().resolve()
    actor = args.actor.strip() or None

    if args.command == "list":
        list_events(company, args.plan.strip() or None)
        return
    if args.command == "sync":
        source = "backfill" if first_sync_is_backfill(company) else "sync"
        for kind, rel, who in sync(company, actor, source):
            print(f"{kind}\t{who}\t{rel}")
        return
    while True:
        source = "backfill" if first_sync_is_backfill(company) else "watch"
        sync(company, actor, source)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
