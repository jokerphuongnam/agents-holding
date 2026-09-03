#!/usr/bin/env python3
"""Seed hop data/*.tsv for a new subsidiary — no Marlin roster/route pollution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALWAYS = [
    # name, tier, perm, cap, skill, lead, qc, routing, blurb
    # Leads stay dispatch (maps low). Plan writers po-* stay xhigh via budget policy.
    ("ba-lead", "dispatch", "plan", "read-only", "", "product-lead", "", "1", "BA lead — assign ba-user vs ba-workflow. Not user channel."),
    ("ba-user", "medium", "plan", "read-only", "", "product-lead", "", "1", "Clarify ask with user; design intake. User channel with ceo."),
    ("ba-workflow", "medium", "default", "all", "", "ba-lead", "", "0", "Jira/tickets/process tooling. Not user channel."),
    ("ceo", "dispatch", "plan", "read-only", "marlin-hop", "", "", "1", "Dispatch only. Product→product-lead; cross-team up-then-down; slim plan_dir+read."),
    ("cto", "dispatch", "plan", "read-only", "", "", "", "1", "Multi-team architecture; recommend tech teams. Do not code."),
    ("git", "low", "default", "all", "", "", "", "0", "git add/commit/branch/push/gitignore gate."),
    ("po-lead", "dispatch", "plan", "read-only", "", "product-lead", "", "1", "Optional PO lead; default product-lead Assigns po-* directly."),
    ("po-modify", "xhigh", "default", "all", "", "product-lead", "", "0", "AC + update existing cache/plans/. Not new plan files."),
    ("po-new", "xhigh", "default", "all", "", "product-lead", "", "0", "Create one new plan under cache/plans/."),
    ("product-lead", "dispatch", "plan", "read-only", "marlin-hop", "", "", "1", "Product lead — CEO first; ba-user/po only; Result to CEO with plan_dir+read."),
    ("qc-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Assign matching *-qc; adapt QC shape to this company."),
    ("tech-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Slice design. Not CTO. Not a default coder. Lives on seeded tech team."),
]

DESIGN = [
    ("design-lead", "dispatch", "plan", "read-only", "", "", "", "1", "Assign ui-designer or ux-writer; design-system and UX quality bar."),
    ("ui-designer", "medium", "default", "all", "", "design-lead", "", "0", "Project design system — color, type, icons, components."),
    ("ux-writer", "medium", "default", "all", "", "design-lead", "", "0", "User-facing copy and microcopy for clearer UX."),
]


def parse_packages(raw: str) -> list[tuple[str, str]]:
    """Parse ``frontend:react,backend:nestjs`` or ``frontend,backend`` → [(path, tech)]."""
    out: list[tuple[str, str]] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            path, tech = part.split(":", 1)
            out.append((path.strip().strip("/"), tech.strip()))
        else:
            out.append((part.strip().strip("/"), ""))
    return out


def _norm_prefix(path: str) -> str:
    p = path.strip().strip("/")
    return f"{p}/" if p else ""


def _kind_for_package(path: str, tech: str) -> str:
    """Classify package as frontend | backend | mobile | data | unknown."""
    blob = f"{path} {tech}".lower().replace("\\", "/")
    if any(k in blob for k in ("ios", "android", "flutter", "swiftui", "compose", "mobile")):
        return "mobile"
    if any(k in blob for k in ("data", "analytics", "bi", "warehouse")):
        return "data"
    if any(
        k in blob
        for k in (
            "backend", "server", "services", "api", "nestjs", "express", "fastapi",
            "django", "rails", "spring", "node",
        )
    ):
        return "backend"
    if any(
        k in blob
        for k in (
            "frontend", "web", "react", "vue", "angular", "next", "nuxt", "svelte",
            "typescript", "javascript",
        )
    ):
        return "frontend"
    # path heuristics
    base = path.lower().replace("\\", "/").split("/")[-1]
    if base in ("frontend", "web", "client", "ui", "app"):
        return "frontend"
    if base in ("backend", "server", "api", "services"):
        return "backend"
    if base in ("mobile", "ios", "android"):
        return "mobile"
    return "unknown"


def tech_roles(
    tech: str,
    packages: list[tuple[str, str]] | None = None,
) -> tuple[list[tuple], list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (extra agents rows, roster pairs, route prefixes).

    When ``packages`` is set, force engineer roles + routes for those paths
    even if ``--tech`` is thin (monorepo teams topology).
    """
    t = (tech or "").lower()
    agents: list[tuple] = []
    roster: list[tuple[str, str]] = []
    routes: list[tuple[str, str]] = []
    have: set[str] = set()

    def add_frontend(extra_prefixes: list[str] | None = None) -> None:
        if "frontend-engineer" not in have:
            agents.append(
                ("frontend-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
                 "Frontend app code (React/Vue/etc per CTO seed). Not design system.")
            )
            roster.append(("tech-lead", "frontend-engineer"))
            roster.append(("ceo", "tech-lead"))
            have.add("frontend-engineer")
        prefs = list(extra_prefixes or [])
        prefs.extend(["src/", "apps/web/", "apps/frontend/", "web/", "frontend/"])
        for pref in prefs:
            if pref:
                routes.append((pref, "frontend-engineer"))

    def add_mobile(extra_prefixes: list[str] | None = None) -> None:
        if "mobile-engineer" not in have:
            agents.append(
                ("mobile-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
                 "Mobile app code (iOS/Android/Flutter per CTO seed). Not design system.")
            )
            roster.append(("tech-lead", "mobile-engineer"))
            roster.append(("ceo", "tech-lead"))
            have.add("mobile-engineer")
        prefs = list(extra_prefixes or [])
        prefs.extend(["apps/mobile/", "apps/ios/", "apps/android/", "mobile/", "ios/", "android/"])
        for pref in prefs:
            if pref:
                routes.append((pref, "mobile-engineer"))

    def add_backend(extra_prefixes: list[str] | None = None) -> None:
        if "backend-engineer" not in have:
            agents.append(
                ("backend-engineer", "medium", "default", "all", "", "tech-lead", "qc-lead", "0",
                 "Backend/API services per CTO seed. Cross-company API asks go via holding.")
            )
            roster.append(("tech-lead", "backend-engineer"))
            roster.append(("ceo", "tech-lead"))
            have.add("backend-engineer")
        prefs = list(extra_prefixes or [])
        prefs.extend(["apps/api/", "apps/backend/", "backend/", "server/", "services/"])
        for pref in prefs:
            if pref:
                routes.append((pref, "backend-engineer"))

    def add_data() -> None:
        if "data" not in have:
            agents.append(
                ("data", "medium", "default", "all", "", "", "", "0",
                 "Bench/analytics reports for this company; cite files; no invented numbers.")
            )
            roster.append(("ceo", "data"))
            have.add("data")

    # Package-forced teams (monorepo)
    for path, pkg_tech in packages or []:
        kind = _kind_for_package(path, pkg_tech)
        pref = _norm_prefix(path)
        if kind == "frontend":
            add_frontend([pref] if pref else None)
        elif kind == "backend":
            add_backend([pref] if pref else None)
        elif kind == "mobile":
            add_mobile([pref] if pref else None)
        elif kind == "data":
            add_data()
        else:
            # Unknown path: still route to frontend-engineer as a safe default IC
            add_frontend([pref] if pref else None)

    frontend = any(k in t for k in ("react", "vue", "angular", "frontend", "next", "nuxt", "svelte"))
    mobile = any(k in t for k in ("ios", "android", "flutter", "swiftui", "compose", "mobile"))
    node_be = any(k in t for k in ("node", "express", "nestjs", "backend", "fastapi", "django", "rails", "spring"))
    ts_js = any(k in t for k in ("typescript", "javascript", "ts", "js"))

    if frontend or ts_js or "react" in t or "vue" in t:
        add_frontend()
    if mobile or "android" in t or "ios" in t:
        add_mobile()
    if node_be:
        add_backend()
    if any(k in t for k in ("data", "analytics", "bi", "warehouse")):
        add_data()

    # de-dupe routes preserving order
    seen_r: set[tuple[str, str]] = set()
    routes_u: list[tuple[str, str]] = []
    for p, a in routes:
        if (p, a) not in seen_r:
            seen_r.add((p, a))
            routes_u.append((p, a))

    return agents, roster, routes_u


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
    ap.add_argument(
        "--packages",
        default="",
        help="Comma list path[:tech] e.g. frontend:react,backend:nestjs — forces teams/routes",
    )
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

    packages = parse_packages(args.packages)
    # Merge package tech tags into effective tech for design/heuristic detection
    pkg_tech_bits = [tech for _, tech in packages if tech]
    effective_tech = ",".join(x for x in [args.tech, *pkg_tech_bits] if x)
    pkg_kinds = {_kind_for_package(p, t) for p, t in packages}

    agents = list(ALWAYS)
    roster: list[tuple[str, str]] = [
        ("ceo", "product-lead"),
        ("product-lead", "ba-lead"),
        ("product-lead", "ba-user"),
        ("product-lead", "po-new"),
        ("product-lead", "po-modify"),
        ("ba-lead", "ba-user"),
        ("ba-lead", "ba-workflow"),
        ("ceo", "cto"),
        ("ceo", "git"),
        ("ceo", "qc-lead"),
        ("ceo", "tech-lead"),
        ("cto", "tech-lead"),
    ]
    # plans/ → product-lead (decides po-new vs po-modify; never paste full plan down)
    routes: list[tuple[str, str]] = [("cache/plans/", "product-lead")]

    want_design = is_frontend(effective_tech) or bool(pkg_kinds & {"frontend", "mobile"})
    if want_design:
        agents.extend(DESIGN)
        roster.extend(
            [
                ("ceo", "design-lead"),
                ("design-lead", "ui-designer"),
                ("design-lead", "ux-writer"),
            ]
        )

    extra_a, extra_r, extra_routes = tech_roles(effective_tech, packages)
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
    # Generic company: agents.tsv loads; roster has ceo→product-lead→ba-user/po-*.
    bad = 0
    if "ceo" not in AGENTS:
        print("FAIL missing ceo in agents.tsv", file=sys.stderr)
        bad += 1
    if "product-lead" not in AGENTS:
        print("FAIL missing product-lead in agents.tsv", file=sys.stderr)
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
