#!/usr/bin/env python3
"""Internal task cache for Marlin Company OS.

SoT for roles/routing stays in agents.tsv + hop. This cache only stores the
**active user task** so CEO/BA can resume without re-analyzing the whole tree.

Cascade still applies (user→ceo/ba-user→…). Cache skips *re-derivation*, not ranks.

Files (gitignored under .agents/marlin-language-company/):
  .agents/marlin-language-company/cache/cache/task.json       machine-readable
  .agents/marlin-language-company/cache/cache/CURRENT_TASK.md short human summary for CEO paste

Usage:
  python3 task_cache.py show
  python3 task_cache.py clear
  python3 task_cache.py set --goal '...' --path 'mpm/...' --role mpm-engineer
  python3 task_cache.py patch --status in_progress --note 'AC locked'
  python3 task_cache.py fingerprint   # print fingerprint of current cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home

SCHEMA_VERSION = 1


def cache_dir() -> Path:
    d = agents_home() / "cache" / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def json_path() -> Path:
    return cache_dir() / "task.json"


def md_path() -> Path:
    return cache_dir() / "CURRENT_TASK.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_task() -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "task_id": "",
        "goal": "",
        "paths": [],
        "user_language": "",
        "phase": "new",  # new | clarifying | assigned | in_progress | blocked | done
        "chosen_option": "",
        "active_role": "",
        "lead": "",
        "qc": "",
        "plan_cite": "",
        "ac_summary": "",
        "hop": {},  # last hop.py fields worth keeping
        "notes": [],
        "updated_at": "",
        "fingerprint": "",
    }


def fingerprint(data: dict) -> str:
    key = "|".join(
        [
            data.get("goal", "").strip().lower(),
            ",".join(data.get("paths") or []),
            data.get("chosen_option", "").strip().lower(),
            data.get("active_role", "").strip(),
        ]
    )
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def load() -> dict:
    p = json_path()
    if not p.is_file():
        return empty_task()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty_task()
    if not isinstance(data, dict):
        return empty_task()
    base = empty_task()
    base.update({k: data.get(k, base[k]) for k in base})
    return base


def render_md(data: dict) -> str:
    paths = data.get("paths") or []
    path_lines = "\n".join(f"- `{p}`" for p in paths) if paths else "- _(none)_"
    notes = data.get("notes") or []
    note_lines = "\n".join(f"- {n}" for n in notes[-8:]) if notes else "- _(none)_"
    hop = data.get("hop") or {}
    hop_lines = "\n".join(f"- **{k}:** `{v}`" for k, v in hop.items()) if hop else "- _(none)_"
    return "\n".join(
        [
            "# Current task (cache)",
            "",
            "Internal Company OS scratch — **not** SoT. Cleared when the user starts a new task.",
            "CEO/BA read this before a full re-route. Cascade still applies.",
            "",
            f"- **task_id / fingerprint:** `{data.get('fingerprint') or '—'}`",
            f"- **phase:** `{data.get('phase') or 'new'}`",
            f"- **updated_at:** `{data.get('updated_at') or '—'}`",
            f"- **user_language:** `{data.get('user_language') or '—'}`",
            "",
            "## Goal",
            "",
            data.get("goal") or "_(empty)_",
            "",
            "## Paths",
            "",
            path_lines,
            "",
            "## Routing (cached)",
            "",
            f"- **chosen_option:** {data.get('chosen_option') or '—'}",
            f"- **active_role:** `{data.get('active_role') or '—'}`",
            f"- **lead:** `{data.get('lead') or '—'}`",
            f"- **qc:** `{data.get('qc') or '—'}`",
            f"- **plan_cite:** `{data.get('plan_cite') or '—'}`",
            "",
            "## AC summary",
            "",
            data.get("ac_summary") or "_(none)_",
            "",
            "## Last hop fields",
            "",
            hop_lines,
            "",
            "## Notes (recent)",
            "",
            note_lines,
            "",
            "## CEO resume rule",
            "",
            "1. If the user’s message continues **this** goal/paths → resume `active_role`",
            "   (short brief; do not re-run BA/full hop analysis).",
            "2. If the user changes goal/paths or says “new task” → `task_cache.py clear`",
            "   then full cascade from the top.",
            "3. Only `ceo` / `ba-user` talk to the user; cache text stays English.",
            "",
        ]
    )


def save(data: dict) -> None:
    data["schema"] = SCHEMA_VERSION
    data["updated_at"] = now_iso()
    data["fingerprint"] = fingerprint(data)
    json_path().write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path().write_text(render_md(data), encoding="utf-8")


def cmd_show(_: argparse.Namespace) -> int:
    data = load()
    if not data.get("goal") and not data.get("active_role"):
        print("task_cache: empty (no active task)")
        print(f"json: {json_path()}")
        return 0
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"---\nmd: {md_path()}")
    return 0


def cmd_clear(_: argparse.Namespace) -> int:
    for p in (json_path(), md_path()):
        if p.is_file():
            p.unlink()
    print("task_cache: cleared")
    return 0


def cmd_fingerprint(_: argparse.Namespace) -> int:
    data = load()
    print(data.get("fingerprint") or fingerprint(data))
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    data = load()
    if args.goal is not None:
        data["goal"] = args.goal
    if args.path:
        # replace paths list
        data["paths"] = list(args.path)
    if args.add_path:
        paths = list(data.get("paths") or [])
        for p in args.add_path:
            if p not in paths:
                paths.append(p)
        data["paths"] = paths
    if args.role is not None:
        data["active_role"] = args.role
    if args.lead is not None:
        data["lead"] = args.lead
    if args.qc is not None:
        data["qc"] = args.qc
    if args.phase is not None:
        data["phase"] = args.phase
    if args.option is not None:
        data["chosen_option"] = args.option
    if args.plan is not None:
        data["plan_cite"] = args.plan
    if args.ac is not None:
        data["ac_summary"] = args.ac
    if args.lang is not None:
        data["user_language"] = args.lang
    if args.note:
        notes = list(data.get("notes") or [])
        notes.append(f"{now_iso()} {args.note}")
        data["notes"] = notes[-20:]
    if args.hop_json:
        try:
            data["hop"] = json.loads(args.hop_json)
        except json.JSONDecodeError as e:
            print(f"invalid --hop-json: {e}", file=sys.stderr)
            return 1
    if not data.get("task_id"):
        data["task_id"] = fingerprint(data)
    save(data)
    print(f"task_cache: saved fingerprint={data['fingerprint']} phase={data['phase']}")
    print(f"md: {md_path()}")
    return 0


def cmd_patch(args: argparse.Namespace) -> int:
    """Patch without requiring a full set — same fields as set."""
    return cmd_set(args)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="print task.json")
    sub.add_parser("clear", help="delete active task cache")
    sub.add_parser("fingerprint", help="print fingerprint")

    def add_fields(p: argparse.ArgumentParser) -> None:
        p.add_argument("--goal", default=None)
        p.add_argument("--path", action="append", default=None, help="replace paths (repeatable)")
        p.add_argument("--add-path", action="append", default=None, help="append path")
        p.add_argument("--role", default=None, help="active_role")
        p.add_argument("--lead", default=None)
        p.add_argument("--qc", default=None)
        p.add_argument("--phase", default=None)
        p.add_argument("--option", default=None, help="chosen_option")
        p.add_argument("--plan", default=None, help="plan_cite")
        p.add_argument("--ac", default=None, help="ac_summary")
        p.add_argument("--lang", default=None, help="user_language")
        p.add_argument("--note", default=None)
        p.add_argument("--hop-json", default=None, help='JSON object of last hop fields')

    ps = sub.add_parser("set", help="create/replace fields and save")
    add_fields(ps)
    pp = sub.add_parser("patch", help="update fields on existing cache")
    add_fields(pp)

    args = ap.parse_args()
    if args.cmd == "show":
        return cmd_show(args)
    if args.cmd == "clear":
        return cmd_clear(args)
    if args.cmd == "fingerprint":
        return cmd_fingerprint(args)
    if args.cmd in {"set", "patch"}:
        return cmd_set(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
