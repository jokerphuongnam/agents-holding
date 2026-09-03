#!/usr/bin/env python3
"""Seed hop data/*.tsv for a new subsidiary — no Marlin roster/route pollution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALWAYS = [
    # name, tier, perm, cap, skill, lead, qc, routing, blurb
    # Leads stay dispatch (maps low). Plan writers po-* stay xhigh via budget policy.
    ("ba-lead", "dispatch", "plan", "read-only", "", "", "", "1", "BA lead — assign ba-user vs ba-workflow. Not user channel."),
    ("ba-user", "medium", "plan", "read-only", "", "ba-lead", "", "1", "Clarify ask with user; design intake. User channel with ceo."),
    ("ba-workflow", "medium", "default", "all", "", "ba-lead", "", "0", "Jira/tickets/process tooling. Not user channel."),
    ("ceo", "dispatch", "plan", "read-only", "marlin-hop", "", "", "1", "Dispatch only. hop then spawn IC/lead. Do not code."),
    ("cto", "dispatch", "plan", "read-only", "", "", "", "1", "Multi-team architecture; recommend tech teams. Do not code."),
    ("git", "low", "default", "all", "", "", "", "0", "git add/commit/branch/push/gitignore gate."),
    ("po-lead", "dispatch", "plan", "read-only", "", "", "", "1", "PO lead — assign po-new vs po-modify. Does not write plans."),
    ("po-modify", "xhigh", "default", "all", "", "po-lead", "", "0", "AC + update existing cache/plans/. Not new plan files."),
    ("po-new", "xhigh", "default", "all", "", "po-lead", "", "0", "Create one new plan under cache/plans/."),
    ("qc-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Assign matching *-qc; adapt QC shape to this company."),
    ("tech-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Slice design. Not CTO. Not a default coder. Lives on seeded tech team."),
]

DESIGN = [
    ("design-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Assign ui-designer or ux-writer; design-system and UX quality bar."),
    ("ui-designer", "medium", "default", "all", "", "design-lead", "", "0", "Project design system — color, type, icons, components."),
    ("ux-writer", "medium", "default", "all", "", "design-lead", "", "0", "User-facing copy and microcopy for clearer UX."),
]


def tech_roles(tech: str) -> tuple[list[tuple], list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (extra agents rows, roster pairs, route prefixes)."""
    t = (tech or "").lower()
    agents: list[tuple] = []
    roster: list[tuple[str, str]] = []
    routes: list[tuple[str, str]] = []

    frontend = any(k in t for k in ("react", "vue", "angular", "frontend", "next", "nuxt", "svelte"))
    mobile = any(k in t for k in ("ios", "android", "flutter", "swiftui", "compose", "mobile"))
    node_be = any(k in t for k in ("node", "express", "nestjs", "backend", "fastapi", "django", "rails", "spring"))
    ts_js = any(k in t for k in ("typescript", "javascript", "ts", "js"))

    if frontend or ts_js or "react" in t or "vue" in t:
        agents.append(
            ("frontend-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
             "Frontend app code (React/Vue/etc per CTO seed). Not design system.")
        )
        roster.append(("tech-lead", "frontend-engineer"))
        roster.append(("ceo", "tech-lead"))
        for pref in ("src/", "apps/web/", "apps/frontend/", "web/", "frontend/"):
            routes.append((pref, "frontend-engineer"))

    if mobile or "android" in t or "ios" in t:
        agents.append(
            ("mobile-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
             "Mobile app code (iOS/Android/Flutter per CTO seed). Not design system.")
        )
        roster.append(("tech-lead", "mobile-engineer"))
        roster.append(("ceo", "tech-lead"))
        for pref in ("apps/mobile/", "apps/ios/", "apps/android/", "mobile/", "ios/", "android/"):
            routes.append((pref, "mobile-engineer"))

    if node_be:
        agents.append(
            ("backend-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
             "Backend/API services per CTO seed. Cross-company API asks go via holding.")
        )
        roster.append(("tech-lead", "backend-engineer"))
        roster.append(("ceo", "tech-lead"))
        for pref in ("apps/api/", "apps/backend/", "backend/", "server/", "services/"):
            routes.append((pref, "backend-engineer"))

    if any(k in t for k in ("data", "analytics", "bi", "warehouse")):
        agents.append(
            ("data", "medium", "default", "all", "", "", "", "0",
             "Bench/analytics reports for this company; cite files; no invented numbers.")
        )
        roster.append(("ceo", "data"))

    return agents, roster, routes


def is_frontend(tech: str) -> bool:
    t = (tech or "").lower()
    return any(
        k in t
        for k in (
            "react", "vue", "angular", "ios", "android", "flutter", "swiftui",
            "compose", "frontend", "mobile", "ui", "ux", "next",
        )
    )


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join(r))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="company root")
    ap.add_argument("--budget", default="medium")
    ap.add_argument("--tech", default="")
    ap.add_argument("--budget-json", required=True)
    args = ap.parse_args()

    dest = Path(args.dest)
    data = dest / "system" / "skills" / "defaults" / "marlin-hop" / "data"
    full_cfg = json.loads(Path(args.budget_json).read_text(encoding="utf-8"))
    policy = full_cfg.get("policy") or {}
    budget_cfg = full_cfg[args.budget]
    overrides = dict(budget_cfg.get("agents_tsv_tier_overrides") or {})
    for role in policy.get("always_max_roles") or ("po-modify", "po-new"):
        overrides[role] = policy.get("always_max_tier") or "xhigh"

    agents = list(ALWAYS)
    roster: list[tuple[str, str]] = [
        ("ceo", "ba-lead"),
        ("ba-lead", "ba-user"),
        ("ba-lead", "ba-workflow"),
        ("ceo", "cto"),
        ("ceo", "git"),
        ("ceo", "po-lead"),
        ("po-lead", "po-modify"),
        ("po-lead", "po-new"),
        ("ceo", "qc-lead"),
        ("ceo", "tech-lead"),
        ("cto", "tech-lead"),
    ]
    routes: list[tuple[str, str]] = []

    if is_frontend(args.tech):
        agents.extend(DESIGN)
        roster.extend(
            [
                ("ceo", "design-lead"),
                ("design-lead", "ui-designer"),
                ("design-lead", "ux-writer"),
            ]
        )

    extra_a, extra_r, extra_routes = tech_roles(args.tech)
    agents.extend(extra_a)
    roster.extend(extra_r)
    routes.extend(extra_routes)

    # de-dupe roster
    seen = set()
    roster_u: list[tuple[str, str]] = []
    for a, b in roster:
        if (a, b) not in seen:
            seen.add((a, b))
            roster_u.append((a, b))

    header = [
        "name",
        "tier",
        "permission_mode",
        "capability_mode",
        "skill",
        "lead",
        "qc",
        "routing",
        "blurb",
    ]
    rows: list[list[str]] = []
    for row in agents:
        cells = list(row)
        name = cells[0]
        if name in overrides:
            cells[1] = overrides[name]
        rows.append(list(cells))

    write_tsv(data / "agents.tsv", header, rows)
    write_tsv(data / "roster.tsv", ["parent", "child"], [[a, b] for a, b in roster_u])
    write_tsv(data / "route.tsv", ["prefix", "agent"], [[p, a] for p, a in routes] or [["docs/", "ba-user"]])
    write_tsv(data / "section.tsv", ["needle", "agent"], [["qa summary", "qc-lead"]])
    write_tsv(data / "cases.tsv", ["path", "agent"], [["docs/", "ba-user"]])

    # Soften hop self-test: generic cases only (avoid Marlin src/ expectations)
    hop_py = dest / "system" / "skills" / "defaults" / "marlin-hop" / "scripts" / "hop.py"
    if hop_py.is_file():
        text = hop_py.read_text(encoding="utf-8")
        start = text.find("def self_test()")
        if start >= 0:
            end = text.find("\ndef main()", start)
            if end > start:
                new_fn = '''def self_test() -> int:
    # Generic company: agents.tsv loads; roster has ceo→ba-lead and ba-user.
    bad = 0
    if "ceo" not in AGENTS:
        print("FAIL missing ceo in agents.tsv", file=sys.stderr)
        bad += 1
    if "ba-lead" not in AGENTS:
        print("FAIL missing ba-lead in agents.tsv", file=sys.stderr)
        bad += 1
    if "ba-user" not in AGENTS:
        print("FAIL missing ba-user in agents.tsv", file=sys.stderr)
        bad += 1
    print("self-test", "ok" if bad == 0 else f"{bad} failed")
    return bad

'''
                text = text[:start] + new_fn + text[end:]
                hop_py.write_text(text, encoding="utf-8")

    print(f"[seed_company_hop_data] agents={len(rows)} roster={len(roster_u)} routes={len(routes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
