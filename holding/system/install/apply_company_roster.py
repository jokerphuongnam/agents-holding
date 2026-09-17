#!/usr/bin/env python3
"""Apply a reviewed staff/skill roster onto a Company OS tree.

Used by agents-holding-app Add Company wizard after create-company.sh:

  python3 apply_company_roster.py --company-path DIR --spec roster.json

Spec JSON:
  {
    "keep_staffs": ["ceo", "ba-user", ...],   # template staff names to keep
    "custom_staffs": [
      {
        "name": "my-role",
        "team": "custom",
        "description": "...",
        "tier": "medium",
        "lead": "ceo",
        "skill_ids": ["swift-core"],
        "new_skills": [
          {"id": "my-skill", "title": "My skill", "body": "# My skill\\n..."}
        ]
      }
    ],
    "extra_skill_ids": ["react"]   # optional library skills to copy
  }

Always keeps `ceo`. Removes other template staff .md not listed in keep_staffs.
Rewrites agents.tsv from remaining staffs + custom rows.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ALWAYS_META = {
    # name: (tier, perm, cap, skill, lead, qc, routing, blurb)
    "ba-lead": ("dispatch", "plan", "read-only", "", "", "", "1", "BA lead"),
    "ba-user": ("medium", "plan", "read-only", "ba-requirements", "ba-lead", "", "1", "User channel BA"),
    "ba-workflow": ("medium", "default", "all", "", "ba-lead", "", "0", "Tickets/process"),
    "ceo": ("dispatch", "plan", "read-only", "marlin-hop", "", "", "1", "Dispatch / user channel"),
    "cto": ("dispatch", "plan", "read-only", "", "", "", "1", "Architecture"),
    "git": ("low", "default", "all", "", "", "", "0", "git gate"),
    "po-lead": ("dispatch", "plan", "read-only", "", "", "", "1", "PO lead"),
    "po-modify": ("xhigh", "default", "all", "", "po-lead", "", "0", "Update plans"),
    "po-new": ("xhigh", "default", "all", "", "po-lead", "", "0", "New plans"),
    "qc-lead": ("dispatch", "plan", "read-only", "", "", "", "1", "QC dispatch"),
    "tech-lead": ("dispatch", "plan", "read-only", "", "", "", "1", "Tech lead"),
    "design-lead": ("dispatch", "plan", "read-only", "", "", "", "1", "Design lead"),
    "ui-designer": ("medium", "default", "all", "", "design-lead", "", "0", "UI designer"),
    "ux-writer": ("medium", "default", "all", "", "design-lead", "", "0", "UX writer"),
    "game-designer": ("medium", "default", "all", "", "design-lead", "", "0", "Game designer"),
}


def load_manifest(library: Path) -> dict[str, dict]:
    path = library / "MANIFEST.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s["id"]: s for s in data.get("skills") or [] if s.get("id")}


def copy_skill(library: Path, skill_id: str, company: Path, target_rel: str | None) -> Path | None:
    manifest = load_manifest(library)
    entry = manifest.get(skill_id)
    src: Path | None = None
    dest_team = "custom"
    dest_role = "shared"
    if entry:
        src = library / entry["path"]
        target = entry.get("target") or "cross-cut/shared"
        parts = str(target).split("/")
        if len(parts) >= 2:
            dest_team, dest_role = parts[0], parts[1]
        elif parts:
            dest_team = parts[0]
    else:
        # filesystem search
        for p in library.rglob("SKILL.md"):
            if p.parent.name == skill_id:
                src = p.parent
                break
    if src is None or not src.is_dir():
        print(f"warn\tmissing_skill\t{skill_id}", file=sys.stderr)
        return None
    if target_rel:
        parts = target_rel.split("/")
        if len(parts) >= 2:
            dest_team, dest_role = parts[0], parts[1]
    dest = company / "system" / "skills" / "customs" / dest_team / dest_role / skill_id
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"skill\tcopied\t{skill_id}\t{dest}")
    return dest


def write_new_skill(company: Path, skill_id: str, title: str, body: str, team: str, role: str) -> Path:
    dest = company / "system" / "skills" / "customs" / team / role / skill_id
    dest.mkdir(parents=True, exist_ok=True)
    text = body.strip()
    if not text.startswith("---"):
        text = f"---\nname: {skill_id}\ndescription: {title}\n---\n\n# {title}\n\n{text}\n"
    (dest / "SKILL.md").write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    print(f"skill\tcreated\t{skill_id}\t{dest}")
    return dest


def write_staff_md(company: Path, name: str, team: str, description: str, tier: str, lead: str, skills: list[str]) -> Path:
    team_dir = company / "system" / "staffs" / team
    team_dir.mkdir(parents=True, exist_ok=True)
    path = team_dir / f"{name}.md"
    skill_line = ", ".join(skills)
    body = f"""---
name: {name}
description: {description.splitlines()[0][:120] if description else name}
tier: {tier}
permission_mode: plan
capability_mode: read-only
---
{description.strip() or f'Staff `{name}`.'}

"""
    if skill_line:
        body += f"**Skills:** `{skill_line}`\n"
    if lead:
        body += f"\n**Lead:** `{lead}`\n"
    path.write_text(body, encoding="utf-8")
    print(f"staff\twritten\t{name}\t{path}")
    return path


def list_staff_files(company: Path) -> list[Path]:
    root = company / "system" / "staffs"
    if not root.is_dir():
        return []
    return [p for p in root.rglob("*.md") if p.name != "ORG.md"]


def rebuild_agents_tsv(company: Path, custom_rows: list[dict]) -> None:
    hop = company / "system" / "skills" / "defaults" / "marlin-hop" / "data"
    hop.mkdir(parents=True, exist_ok=True)
    rows: list[tuple] = []
    for path in list_staff_files(company):
        name = path.stem
        team = path.parent.name
        text = path.read_text(encoding="utf-8")
        meta = ALWAYS_META.get(name)
        if meta:
            tier, perm, cap, skill, lead, qc, routing, blurb = meta
        else:
            # custom / unknown
            tier = "medium"
            perm = "plan"
            cap = "read-only"
            skill = ""
            lead = "ceo"
            qc = ""
            routing = "0"
            blurb = ""
            for line in text.splitlines():
                if line.startswith("tier:"):
                    tier = line.split(":", 1)[1].strip()
                if line.startswith("description:"):
                    blurb = line.split(":", 1)[1].strip()
            for c in custom_rows:
                if c.get("name") == name:
                    tier = c.get("tier") or tier
                    lead = c.get("lead") or lead
                    skill = ",".join(c.get("skill_ids") or [])
                    blurb = (c.get("description") or blurb).splitlines()[0][:80]
                    routing = "1" if name in ("ba-user", "ceo", "backend-ba") else routing
        rows.append((name, tier, perm, cap, skill, lead, qc, routing, blurb or name))

    rows.sort(key=lambda r: r[0])
    header = "name\ttier\tpermission_mode\tcapability_mode\tskill\tlead\tqc\trouting\tblurb\n"
    lines = [header] + ["\t".join(r) + "\n" for r in rows]
    out = hop / "agents.tsv"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"agents\twrote\t{out}\tcount={len(rows)}")


def apply(company: Path, spec: dict, library: Path) -> int:
    keep = set(spec.get("keep_staffs") or [])
    keep.add("ceo")  # hard requirement
    custom = list(spec.get("custom_staffs") or [])
    extra_skills = list(spec.get("extra_skill_ids") or [])

    # Remove template staffs not kept
    for path in list_staff_files(company):
        name = path.stem
        if name in keep:
            continue
        if any(c.get("name") == name for c in custom):
            continue
        path.unlink()
        print(f"staff\tremoved\t{name}")
        # prune empty team dirs later

    # Custom staffs + their skills
    for c in custom:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        team = (c.get("team") or "custom").strip() or "custom"
        desc = c.get("description") or f"Custom staff `{name}`."
        tier = c.get("tier") or "medium"
        lead = c.get("lead") or "ceo"
        skill_ids = list(c.get("skill_ids") or [])
        for ns in c.get("new_skills") or []:
            sid = (ns.get("id") or "").strip()
            if not sid:
                continue
            write_new_skill(
                company,
                sid,
                ns.get("title") or sid,
                ns.get("body") or f"# {sid}\n",
                team,
                name,
            )
            if sid not in skill_ids:
                skill_ids.append(sid)
        for sid in skill_ids:
            copy_skill(library, sid, company, f"{team}/{name}")
        write_staff_md(company, name, team, desc, tier, lead, skill_ids)
        keep.add(name)

    for sid in extra_skills:
        copy_skill(library, sid, company, None)

    # Drop empty team directories (except keep structure lightly)
    staffs_root = company / "system" / "staffs"
    if staffs_root.is_dir():
        for team_dir in list(staffs_root.iterdir()):
            if team_dir.is_dir() and not any(team_dir.glob("*.md")):
                shutil.rmtree(team_dir)
                print(f"team\tremoved_empty\t{team_dir.name}")

    rebuild_agents_tsv(company, custom)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--company-path", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path, help="JSON roster spec")
    ap.add_argument(
        "--library",
        type=Path,
        default=None,
        help="skills-library root (default: <agents-home>/templates/skills-library)",
    )
    args = ap.parse_args()
    company = args.company_path.resolve()
    if not company.is_dir():
        print(f"error\tmissing_company\t{company}", file=sys.stderr)
        return 1
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if args.library:
        library = args.library.resolve()
    else:
        # company/../../templates when holding layout; else sibling of holding package
        holding_install = Path(__file__).resolve().parent
        agents_home = holding_install.parents[2]  # .../agents-holding
        library = agents_home / "templates" / "skills-library"
    if not library.is_dir():
        print(f"error\tmissing_library\t{library}", file=sys.stderr)
        return 1
    return apply(company, spec, library)


if __name__ == "__main__":
    raise SystemExit(main())
