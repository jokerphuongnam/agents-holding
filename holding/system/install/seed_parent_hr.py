#!/usr/bin/env python3
"""Enable a company to own children: seed `hr` staff + manage-children skill.

Rule: only companies with hr may run child-org flows (create/read/approve/
staff children). Idempotent: safe to re-run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def upsert_agents_tsv(path: Path) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return
    header = lines[0].split("\t")
    if "name" not in header:
        return
    i_name = header.index("name")
    names = set()
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = ln.split("\t")
        if len(cells) > i_name:
            names.add(cells[i_name])
    if "hr" in names:
        return
    # name tier perm cap skill lead qc routing blurb
    row = {
        "name": "hr",
        "tier": "medium",
        "permission_mode": "plan",
        "capability_mode": "read-only",
        "skill": "",
        "lead": "ceo",
        "qc": "",
        "routing": "1",
        "blurb": "Parent HR — own child portfolio (approve/create/grants/staff). Not holding-hr.",
    }
    cells = [row.get(h, "") for h in header]
    # map known headers
    for h in header:
        if h in row:
            cells[header.index(h)] = row[h]
    lines.append("\t".join(cells))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def upsert_roster_tsv(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "\thr\n" in text or text.endswith("\thr") or "\nceo\thr\n" in text:
        if any(ln.split("\t")[:2] == ["ceo", "hr"] for ln in text.splitlines() if "\t" in ln):
            return
    lines = text.splitlines()
    if not lines:
        lines = ["parent\tchild"]
    if not any(ln.startswith("ceo\thr") for ln in lines):
        lines.append("ceo\thr")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", required=True, help="Parent …/<slug>-company/")
    ap.add_argument(
        "--agents-home",
        default="",
        help="Agents home with templates/ (default: infer from this script)",
    )
    args = ap.parse_args()
    parent = Path(args.parent).expanduser().resolve()
    if not (parent / "system").is_dir():
        print(f"error: not a Company OS: {parent}", file=sys.stderr)
        return 1

    agents_home = (
        Path(args.agents_home).expanduser().resolve()
        if args.agents_home
        else Path(__file__).resolve().parents[3]
    )
    # Not under system/staffs/ — that tree is rsynced into every new company.
    staff_src = agents_home / "templates" / "company" / "children" / "hr.md"
    skill_src = (
        agents_home / "templates" / "skills-library" / "product" / "hr" / "manage-children"
    )
    if not staff_src.is_file():
        print(f"error: missing staff template {staff_src}", file=sys.stderr)
        return 1
    if not (skill_src / "SKILL.md").is_file():
        print(f"error: missing skill {skill_src}", file=sys.stderr)
        return 1

    staff_dst = parent / "system" / "staffs" / "cross-cut" / "hr.md"
    staff_dst.parent.mkdir(parents=True, exist_ok=True)
    created_staff = False
    if not staff_dst.is_file():
        shutil.copy2(staff_src, staff_dst)
        created_staff = True
    else:
        # Refresh card so owns-children language stays current
        shutil.copy2(staff_src, staff_dst)

    skill_dst = parent / "system" / "skills" / "customs" / "cross-cut" / "hr" / "manage-children"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    if skill_dst.exists():
        shutil.rmtree(skill_dst)
    shutil.copytree(skill_src, skill_dst)

    task_path = parent / "system" / "skills" / "customs" / "cross-cut" / "hr" / "TASK_SKILLS.json"
    data = {
        "role": "hr",
        "default_skill": "manage-children",
        "customs_root": "system/skills/customs/cross-cut/hr",
        "note": "Parent HR owns child-company portfolio (approve/create/grants/staff).",
        "tasks": [
            {
                "skill": "manage-children",
                "when": "create/approve child, inventory, grants, hire into child",
            }
        ],
    }
    if task_path.is_file():
        try:
            data = json.loads(task_path.read_text(encoding="utf-8"))
            tasks = data.setdefault("tasks", [])
            if not any(t.get("skill") == "manage-children" for t in tasks):
                tasks.append(
                    {
                        "skill": "manage-children",
                        "when": "create/approve child, inventory, grants, hire into child",
                    }
                )
            data["default_skill"] = "manage-children"
        except json.JSONDecodeError:
            pass
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    hop = parent / "system" / "skills" / "defaults" / "marlin-hop" / "data"
    upsert_agents_tsv(hop / "agents.tsv")
    upsert_roster_tsv(hop / "roster.tsv")

    print(
        f"[seed_parent_hr] parent={parent.name} "
        f"staff={'created' if created_staff else 'refreshed'} "
        f"skill=manage-children"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
