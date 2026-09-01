#!/usr/bin/env python3
"""Path / QA section → spawn fields. Replaces reading ORG.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_tsv, resolve_vendor, company_relposix

# Tables in ../data/*.tsv (tab). Agents read hop.py stdout, not these files.
# Vendor model/effort come from `.agents/marlin-language-company/system/harness/<id>.toml` (Company OS drivers).


def _pairs(name: str, a: str, b: str) -> list[tuple[str, str]]:
    return [(r[a], r[b]) for r in load_tsv(name) if r.get(a)]


PREFIXES: list[tuple[str, str]] = _pairs("route.tsv", "prefix", "agent")
SECTIONS: list[tuple[str, str]] = _pairs("section.tsv", "needle", "agent")

# One row per agent. Do not open .md for listing/spawn fields.
AGENTS = {r["name"]: r for r in load_tsv("agents.tsv") if r.get("name")}
BLURB = {n: r.get("blurb", "") for n, r in AGENTS.items()}
SKILL = {n: r["skill"] for n, r in AGENTS.items() if r.get("skill")}
LEAD = {n: r["lead"] for n, r in AGENTS.items() if r.get("lead")}
QC = {n: r["qc"] for n, r in AGENTS.items() if r.get("qc")}
ROUTING = {n for n, r in AGENTS.items() if r.get("routing") == "1"}
_ROSTER = load_tsv("roster.tsv")
CEO_BELOW = [r["child"] for r in _ROSTER if r.get("parent") == "ceo"]
LEAD_BELOW: dict[str, list[str]] = {}
for r in _ROSTER:
    p, c = r.get("parent", ""), r.get("child", "")
    if p and c and p != "ceo":
        LEAD_BELOW.setdefault(p, []).append(c)


LIBRARY_LESSONS = re.compile(
    r"(?:^|/)(?:18_foundation|19_secure|21_unittest|22_networking|23_database|errors/21_)"
)
LANG_LESSONS = re.compile(
    r"(?:^|/)(?:0[1-9]_|1[0-7]_|20_stability|errors/)"
)

def graph_team(agent: str) -> str | None:
    if agent.startswith("marlin"):
        return "marlin"
    if agent.startswith("cpp-llvm"):
        return "marlin"  # compiler graph file name may stay cache/graphs/marlin.md
    if agent.startswith("libraries") or agent == "security-engineer":
        return "libraries"
    if agent.startswith("sdk"):
        return "sdk"
    if agent.startswith("comm"):
        return "communication"
    if agent.startswith("mpm"):
        return "mpm"
    if agent.startswith("tools"):
        return "tools"
    if agent.startswith("qc") or agent in {"qc-python", "qc-orchestrator", "qc-runtime-bench", "qc-full-lang-bench"}:
        return "qa"
    if agent in {"docs", "language-docs-engineer"}:
        return None
    if agent == "infra-engineer":
        return "infra-engineer"
    return None


def norm_path(p: str) -> str:
    s = p.strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    return s


def agent_for_path(path: str) -> str | None:
    p = norm_path(path)
    # Marlin authoring split (not C++ product ICs)
    if p.endswith(".marlinheader"):
        if "libraries/sources/ConfigKit" in p:
            return "mpm-configkit-engineer"
        return "marlin-lead"
    if p.endswith(".marlin"):
        if p.startswith("qa/") or "/integrations/" in p:
            return "marlin-integration-engineer"
    if "qa/integrations/files/" in p or p.rstrip("/") == "qa/integrations/files":
        return "marlin-integration-engineer"
    hits = [(pref, ag) for pref, ag in PREFIXES if p == pref or p.startswith(pref)]
    if not hits:
        return None
    hits.sort(key=lambda x: len(x[0]), reverse=True)
    return hits[0][1]


def agent_for_section(section: str) -> str | None:
    s = section.strip().lower()
    s = re.sub(r"^═+\s*|\s*═+$", "", s).strip()
    for needle, ag in SECTIONS:
        if needle in s:
            return ag
    return None


def agent_for_lesson(lesson: str) -> str | None:
    """Lesson folder under qa/integrations/files → Marlin fixture authoring."""
    name = lesson.strip()
    if LIBRARY_LESSONS.search(name) or name in {
        "18_foundation",
        "19_secure",
        "21_unittest",
        "22_networking",
        "23_database",
    }:
        return "marlin-integration-engineer"
    if re.match(r"^(0[1-9]|1[0-7])_", name) or name.startswith("20_"):
        return "marlin-integration-engineer"
    return agent_for_path(name)


def emit(agent: str, role: str, harness: str = "grok") -> None:
    if role == "qc":
        agent = QC.get(agent, agent)
    elif role == "lead":
        agent = LEAD.get(agent, agent)
    fm = AGENTS.get(agent, {})
    tier = fm.get("tier") or fm.get("effort") or "low"
    model, effort = resolve_vendor(tier, harness)
    # Prefer explicit TSV leftovers only if harness map empty (should not happen).
    if not model:
        model = fm.get("model", "")
    perm = fm.get("permission_mode", "default")
    cap = fm.get("capability_mode") or ("read-only" if agent in ROUTING else "all")
    skill_name = SKILL.get(agent)
    skill = (f"{company_relposix()}/system/skills/defaults/{skill_name}/SKILL.md" if skill_name else "—")
    team = graph_team(agent)
    graph = f"{team}.md" if team else "—"
    print(f"agent: {agent}")
    print(f"tier: {tier}")
    print(f"harness: {harness}")
    if model:
        print(f"model: {model}")
    print(f"effort: {effort}")
    print(f"capability_mode: {cap}")
    print(f"permission_mode: {perm}")
    print(f"skill: {skill}")
    print(f"graph: {graph}")
    if agent in QC:
        print(f"qc: {QC[agent]}")
    if agent in LEAD:
        print(f"lead: {LEAD[agent]}")
    print("do_not: open ORG.md, load skill catalog, grep the repo")


def emit_list(harness: str = "grok") -> int:
    """Full agent list from agents.tsv. Do not ls .agents/marlin-language-company/system/staffs/."""
    print("name\ttier\tmodel\teffort\tcap\tblurb")
    for n, r in sorted(AGENTS.items()):
        tier = r.get("tier") or r.get("effort") or "low"
        model, effort = resolve_vendor(tier, harness)
        print(
            f"{n}\t{tier}\t{model}\t{effort}\t"
            f"{r.get('capability_mode','')}\t{r.get('blurb','')}"
        )
    print(f"count: {len(AGENTS)}  source: data/agents.tsv  harness: {harness}")
    return 0


def emit_roster(who: str) -> int:
    """Short blurbs of the rank below `who`. Do not open their agent files."""
    who = (who or "ceo").strip()
    if who in ("ceo", "all"):
        names = CEO_BELOW if who == "ceo" else list(BLURB)
    else:
        names = LEAD_BELOW.get(who)
        if not names:
            print(f"no roster for {who} — not a dispatch rank", file=sys.stderr)
            return 1
    print(f"roster: {who}")
    print("rule: spawn only rows you need; do not read their .md")
    for name in names:
        print(f"{name:24} {BLURB.get(name, '')}")
    return 0


def self_test() -> int:
    cases = [
        ("src/runtime/x.cpp", "cpp-llvm-engineer"),
        ("libraries/sources/ConfigKit/x", "mpm-configkit-engineer"),
        ("libraries/sources/Networking/Session.cpp", "libraries-engineer"),
        ("communication/language/cpp/x", "comm-cpp-engineer"),
        ("qa/integrations/files/22_networking/x.marlin", "marlin-integration-engineer"),
        ("qa/integrations/files/05_types/x.marlin", "marlin-integration-engineer"),
        ("qa/integrations/mpm/communications/cpp/Foo.marlinheader", "marlin-lead"),
        ("qa/benchmarks/comparison/run.sh", "qc-full-lang-bench"),
        (".agents/marlin-language-company/cache/plans/foo.md", "po-modify"),
    ]
    bad = 0
    for path, want in cases:
        got = agent_for_path(path)
        if got != want:
            print(f"FAIL path {path}: got {got} want {want}", file=sys.stderr)
            bad += 1
    if agent_for_section("══ Communication C++ ══") != "comm-cpp-engineer":
        print("FAIL section", file=sys.stderr)
        bad += 1
    if agent_for_lesson("22_networking") != "marlin-integration-engineer":
        print("FAIL lesson", file=sys.stderr)
        bad += 1
    print("self-test", "ok" if bad == 0 else f"{bad} failed")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Route a path/section to spawn fields")
    ap.add_argument("--path", help="repo-relative file or directory")
    ap.add_argument("--section", help="qa/run_all.sh ══ section ══ name")
    ap.add_argument("--lesson", help="▸ lesson name (e.g. 22_networking)")
    ap.add_argument("--agent", help="dump YAML fields for a known agent")
    ap.add_argument("--role", choices=("ic", "qc", "lead"), default="ic")
    ap.add_argument("--roster", nargs="?", const="ceo",
                    help="one-liners for the rank below (ceo|*-lead|cto|all)")
    ap.add_argument("--list", action="store_true", help="print agents.tsv (do not read .md)")
    ap.add_argument(
        "--harness",
        default=None,
        help="runtime driver id (grok|codex|…). Default: $MARLIN_HARNESS or grok",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    harness = (args.harness or __import__("os").environ.get("MARLIN_HARNESS") or "grok").strip()
    if args.self_test:
        return self_test()
    if args.list:
        return emit_list(harness)
    if args.roster is not None:
        return emit_roster(args.roster)

    agent = None
    if args.agent:
        agent = args.agent
    elif args.section:
        agent = agent_for_section(args.section)
    elif args.lesson:
        agent = agent_for_lesson(args.lesson)
    elif args.path:
        agent = agent_for_path(args.path)
    else:
        ap.print_help()
        return 2
    if not agent:
        print("unmapped — unique IC unknown; spawn team-lead or ceo", file=sys.stderr)
        return 1
    emit(agent, args.role, harness)
    return 0


if __name__ == "__main__":
    sys.exit(main())
