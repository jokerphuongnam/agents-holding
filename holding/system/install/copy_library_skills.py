#!/usr/bin/env python3
"""Copy matching skills-library entries into a new company's customs/ tree."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--tech", default="")
    ap.add_argument("--library", required=True)
    args = ap.parse_args()

    dest = Path(args.dest)
    lib = Path(args.library)
    manifest = json.loads((lib / "MANIFEST.json").read_text(encoding="utf-8"))
    tech = (args.tech or "").lower()
    tokens = {t.strip() for t in tech.replace(";", ",").split(",") if t.strip()}
    tokens |= set(tech.split())

    # Always include product/design/qc baseline skills for every company
    always_tags = {"ba", "po", "qc", "requirements", "ac", "test-strategy"}
    # Design skills if UI-ish
    ui = any(
        k in tech
        for k in (
            "react", "vue", "angular", "ios", "android", "flutter", "swiftui",
            "compose", "frontend", "mobile", "ui", "ux", "next", "design",
        )
    )
    if ui:
        always_tags |= {"design", "design-system", "ux-writing", "design-intake", "figma"}

    copied = []
    for entry in manifest.get("skills") or []:
        tags = {str(t).lower() for t in entry.get("tags") or []}
        if not (tags & tokens) and not (tags & always_tags):
            continue
        # For always_tags product/qc, require tag intersection with always set meaningfully
        if not (tags & tokens):
            # only copy ba/po/qc/design baseline
            if not (tags & {"ba", "po", "qc", "requirements", "ac", "test-strategy", "automation", "regression", "design", "design-system", "ux-writing", "design-intake", "critique", "design-review", "copy", "content", "figma", "ux"}):
                continue

        rel = entry["path"]
        src = lib / rel
        if not (src / "SKILL.md").is_file():
            continue
        target = entry["target"]  # team/role
        skill_id = entry["id"]
        out = dest / "system" / "skills" / "customs" / target / skill_id
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(src, out)
        copied.append((target, skill_id, sorted(tags & (tokens | always_tags))))

        # Upsert TASK_SKILLS.json
        task_path = dest / "system" / "skills" / "customs" / target / "TASK_SKILLS.json"
        role = target.split("/")[-1]
        data = {
            "role": role,
            "default_skill": "",
            "customs_root": f"system/skills/customs/{target}",
            "note": "Auto-seeded from templates/skills-library; append tasks freely.",
            "tasks": [],
        }
        if task_path.is_file():
            try:
                data = json.loads(task_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        tasks = data.setdefault("tasks", [])
        if not any(t.get("skill") == skill_id for t in tasks):
            tasks.append(
                {
                    "id": skill_id,
                    "when": entry.get("tags") or [skill_id],
                    "skill": skill_id,
                }
            )
        task_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"[copy_library_skills] copied {len(copied)} skills")
    for target, sid, hit in copied[:30]:
        print(f"  - {target}/{sid} tags={hit}")
    if len(copied) > 30:
        print(f"  … {len(copied) - 30} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
